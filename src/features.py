"""Receiver-side features computed online, one transaction at a time.

The same AccountState builds the training tables and, later, scores live
transactions, so training and serving see identical features. Every feature
uses only transactions seen before the current one.
"""

import math
import time
from collections import deque

import numpy as np
import pandas as pd

HOUR = 3600
DAY = 24 * HOUR
SWEEP_EVERY = 6 * HOUR
PASS_THROUGH_CAP = 10.0

FEATURE_NAMES = [
    "log_amount",
    "amount_vs_dst_mean",
    "hour_of_day",
    "is_self_transfer",
    "payment_format",
    "receiving_currency",
    "cross_currency",
    "dst_in_count_1h",
    "dst_in_count_24h",
    "dst_unique_senders_24h",
    "dst_out_count_1h",
    "dst_out_count_24h",
    "dst_unique_receivers_24h",
    "dst_pass_through_1h",
    "dst_pass_through_24h",
    "dst_minutes_since_first_seen",
    "dst_lifetime_in_count",
    "sender_known_to_dst_24h",
    "src_out_count_24h",
    "src_unique_receivers_24h",
    "dst_flagged",
    "src_flagged",
    "dst_flagged_senders_24h",
    "dst_flagged_receivers_24h",
]


class _Window:
    """Events from the last `span` seconds, with a running amount total and optional counterparty counts."""

    __slots__ = ("span", "events", "head", "total", "parties")

    def __init__(self, span, track_parties=False):
        self.span = span
        self.events = []
        self.head = 0
        self.total = 0.0
        self.parties = {} if track_parties else None

    def expire(self, now):
        cutoff = now - self.span
        events = self.events
        head = self.head
        parties = self.parties
        while head < len(events) and events[head][0] <= cutoff:
            _, party, amount = events[head]
            self.total -= amount
            if parties is not None:
                left = parties[party] - 1
                if left:
                    parties[party] = left
                else:
                    del parties[party]
            head += 1

        if head == len(events):
            events.clear()
            head = 0
            self.total = 0.0  # avoid float drift once empty
        elif head > 64 and head * 2 > len(events):
            del events[:head]
            head = 0
        self.head = head

    def add(self, now, party, amount):
        self.events.append((now, party, amount))
        self.total += amount
        if self.parties is not None:
            self.parties[party] = self.parties.get(party, 0) + 1

    @property
    def count(self):
        return len(self.events) - self.head


class _Account:
    __slots__ = ("in_1h", "in_24h", "out_1h", "out_24h", "first_seen", "in_total", "in_n")

    def __init__(self, now):
        self.in_1h = _Window(HOUR)
        self.in_24h = _Window(DAY, track_parties=True)
        self.out_1h = _Window(HOUR)
        self.out_24h = _Window(DAY, track_parties=True)
        self.first_seen = now
        self.in_total = 0.0
        self.in_n = 0

    def expire(self, now):
        self.in_1h.expire(now)
        self.in_24h.expire(now)
        self.out_1h.expire(now)
        self.out_24h.expire(now)


def _ratio(out_total, in_total):
    if in_total > 0:
        return min(out_total / in_total, PASS_THROUGH_CAP)
    return PASS_THROUGH_CAP if out_total > 0 else 0.0


class AccountState:
    """Rolling per-account state.

    Labels play the role of confirmed fraud reports: a laundering transaction
    flags both its accounts only `label_delay` seconds later, and only if it
    happened at or before `label_cutoff` (end of the training period). Live
    scoring passes `label=None`.
    """

    def __init__(self, label_cutoff=None, label_delay=DAY):
        self.accounts = {}
        self.flagged = set()
        self.pending = deque()
        self.label_cutoff = label_cutoff
        self.label_delay = label_delay
        self.codes = {"payment_format": {}, "currency": {}}
        self.next_sweep = None

    def _code(self, field, value):
        table = self.codes[field]
        code = table.get(value)
        if code is None:
            code = table[value] = len(table)
        return code

    def _housekeeping(self, now):
        pending = self.pending
        while pending and pending[0][0] <= now:
            _, src, dst = pending.popleft()
            self.flagged.add(src)
            self.flagged.add(dst)

        if self.next_sweep is None:
            self.next_sweep = now + SWEEP_EVERY
        elif now >= self.next_sweep:
            for account in self.accounts.values():
                account.expire(now)
            self.next_sweep = now + SWEEP_EVERY

    def update_and_features(self, now, src, dst, amount, amount_paid,
                            payment_format, receiving_currency, payment_currency, label=None):
        """Return features for this transaction (from earlier history only), then record it."""
        self._housekeeping(now)
        accounts = self.accounts

        d = accounts.get(dst)
        dst_seen = d is not None
        if d is None:
            d = accounts[dst] = _Account(now)
        s = accounts.get(src)
        if s is None:
            s = accounts[src] = _Account(now)

        d.expire(now)
        if s is not d:
            s.expire(now)

        flagged = self.flagged
        in_24h_parties = d.in_24h.parties
        out_24h_parties = d.out_24h.parties
        mean_in = d.in_total / d.in_n if d.in_n else 0.0

        features = [
            math.log1p(amount),
            amount / mean_in if mean_in > 0 else 1.0,
            (now // HOUR) % 24,
            1.0 if src == dst else 0.0,
            self._code("payment_format", payment_format),
            self._code("currency", receiving_currency),
            1.0 if receiving_currency != payment_currency else 0.0,
            d.in_1h.count,
            d.in_24h.count,
            len(in_24h_parties),
            d.out_1h.count,
            d.out_24h.count,
            len(out_24h_parties),
            _ratio(d.out_1h.total, d.in_1h.total),
            _ratio(d.out_24h.total, d.in_24h.total),
            (now - d.first_seen) / 60 if dst_seen else -1.0,
            d.in_n,
            1.0 if src in in_24h_parties else 0.0,
            s.out_24h.count,
            len(s.out_24h.parties),
            1.0 if dst in flagged else 0.0,
            1.0 if src in flagged else 0.0,
            sum(1 for p in in_24h_parties if p in flagged) if flagged else 0,
            sum(1 for p in out_24h_parties if p in flagged) if flagged else 0,
        ]

        s.out_1h.add(now, dst, amount_paid)
        s.out_24h.add(now, dst, amount_paid)
        d.in_1h.add(now, src, amount)
        d.in_24h.add(now, src, amount)
        d.in_total += amount
        d.in_n += 1

        if label and (self.label_cutoff is None or now <= self.label_cutoff):
            self.pending.append((now + self.label_delay, src, dst))

        return features


def to_seconds(ts):
    """Timestamps (Series or scalar) → integer seconds since 1970-01-01."""
    epoch = pd.Timestamp("1970-01-01")
    if isinstance(ts, pd.Series):
        return ((ts - epoch) // pd.Timedelta(seconds=1)).astype("int64").to_numpy()
    return int((pd.Timestamp(ts) - epoch) // pd.Timedelta(seconds=1))


def build_feature_table(df, label_cutoff=None, progress_every=500_000):
    """Run AccountState over `df` in time order. Returns (features DataFrame with `label`, state)."""
    if not df["ts"].is_monotonic_increasing:
        raise ValueError("df must be sorted by ts")

    state = AccountState(label_cutoff=None if label_cutoff is None else to_seconds(label_cutoff))
    out = np.empty((len(df), len(FEATURE_NAMES)), dtype=np.float32)

    columns = (
        to_seconds(df["ts"]),
        df["src"].to_numpy(dtype=object),
        df["dst"].to_numpy(dtype=object),
        df["amount"].to_numpy(dtype=float),
        df["amount_paid"].to_numpy(dtype=float),
        df["payment_format"].astype(str).to_numpy(dtype=object),
        df["receiving_currency"].astype(str).to_numpy(dtype=object),
        df["payment_currency"].astype(str).to_numpy(dtype=object),
        df["label"].to_numpy(),
    )

    start = time.time()
    for i, row in enumerate(zip(*columns)):
        out[i] = state.update_and_features(*row)
        if progress_every and (i + 1) % progress_every == 0:
            elapsed = time.time() - start
            print(f"{i + 1:,} rows  {elapsed:.0f}s  ({1e6 * elapsed / (i + 1):.1f} µs/row)")

    features = pd.DataFrame(out, columns=FEATURE_NAMES, index=df.index)
    features["label"] = df["label"].to_numpy()
    return features, state
