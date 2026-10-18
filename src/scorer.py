"""Real-time scorer: features -> XGBoost (+ optional sequence model) -> decision -> reasons.

Live features must match training exactly, so the scorer first replays all
history before the test period into AccountState, using the same code and
label cutoff as `python -m src.features`.

Verify:

    python -m src.scorer --verify 2000

Saving the warmed state (--cache / TRUSTPAUSE_STATE_CACHE=1) makes API restarts
fast but needs several GB of extra memory while saving, so it is off by default.
"""

import argparse
import gc
import os
import pickle
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from .data import DEFAULT_PATH, drop_sparse_days, load_transactions, time_split
from .features import FEATURE_NAMES, to_seconds, warm_state
from .reasons import top_reasons

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "state_warm.pkl"
USE_CACHE = os.environ.get("TRUSTPAUSE_STATE_CACHE") == "1"


def load_history(data_path=DEFAULT_PATH):
    """Return (history before test, test rows, train_end), split exactly as in training."""
    dense = drop_sparse_days(load_transactions(data_path))
    train, val, test = time_split(dense)  # same split as training (sparse days already gone)
    train_end = train["ts"].max()
    test_start = test["ts"].min()
    del train, val
    history = dense[dense["ts"] < test_start]
    del dense
    gc.collect()
    return history, test, train_end


def cache_key(history, train_end):
    return (len(history), str(history["ts"].iloc[-1]), str(train_end))


def warmed_state(history, train_end, cache=CACHE, use_cache=USE_CACHE):
    """AccountState after all history (from the cache only when enabled and matching)."""
    if use_cache and Path(cache).exists():
        with open(cache, "rb") as f:
            saved_key, state = pickle.load(f)
        if saved_key == cache_key(history, train_end):
            print(f"Loaded warm state from {cache}", flush=True)
            return state
    print(f"Warming up account state from {len(history):,} historical transactions...", flush=True)
    start = time.time()
    state = warm_state(history, label_cutoff=train_end)
    print(f"Warm-up done in {time.time() - start:.0f}s", flush=True)
    return state


def save_state(state, key, cache=CACHE):
    """Optional: save the warmed state. Call after freeing the history DataFrame."""
    gc.collect()
    with open(cache, "wb") as f:
        pickle.dump((key, state), f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Saved warm state to {cache}", flush=True)


class Scorer:
    def __init__(self, state, models=ROOT / "models", seq_scorer=None, seq_weight=0.0):
        import json

        self.state = state
        self.booster = xgb.Booster()
        self.booster.load_model(Path(models) / "xgb.json")
        self.thresholds = json.loads((Path(models) / "thresholds.json").read_text())
        # Card 04 hook: a callable (state, txn) -> score, used in the ensemble when given.
        # Thresholds were tuned for XGBoost alone; re-tune them if seq_weight > 0.
        self.seq_scorer = seq_scorer
        self.seq_weight = seq_weight
        self.lock = threading.Lock()

    def decide(self, score):
        if score >= self.thresholds["hold"]:
            return "hold"
        if score >= self.thresholds["pause"]:
            return "pause"
        return "allow"

    def preview(self, txn):
        """XGBoost score for txn without recording it in the account state."""
        with self.lock:
            feats = self.state.update_and_features(
                to_seconds(txn["ts"]), txn["src"], txn["dst"], txn["amount"], txn["amount_paid"],
                txn["payment_format"], txn["receiving_currency"], txn["payment_currency"], None, record=False)
            return float(self.booster.inplace_predict(np.asarray(feats, dtype=np.float32).reshape(1, -1))[0])

    def score(self, txn, record=True):
        """txn: dict with ts, src, dst, amount, amount_paid, payment_format, receiving_currency, payment_currency.

        record=False scores without adding the transfer to account history (used for
        sender-view demo transfers, so the demo behaves the same every time).
        """
        with self.lock:
            start = time.perf_counter()
            feats = self.state.update_and_features(
                to_seconds(txn["ts"]), txn["src"], txn["dst"], txn["amount"], txn["amount_paid"],
                txn["payment_format"], txn["receiving_currency"], txn["payment_currency"], None, record=record)
            x = np.asarray(feats, dtype=np.float32).reshape(1, -1)
            score_xgb = float(self.booster.inplace_predict(x)[0])
            score_seq = float(self.seq_scorer(self.state, txn)) if self.seq_scorer else None
            score = score_xgb if score_seq is None else (1 - self.seq_weight) * score_xgb + self.seq_weight * score_seq
            decision = self.decide(score)

            reasons, sender_reasons = [], []
            if decision != "allow":
                dm = xgb.DMatrix(x, feature_names=FEATURE_NAMES)
                contribs = self.booster.predict(dm, pred_contribs=True)[0]
                reasons = top_reasons(contribs, x[0], FEATURE_NAMES, audience="analyst")
                sender_reasons = top_reasons(contribs, x[0], FEATURE_NAMES, audience="sender")
            latency_ms = 1000 * (time.perf_counter() - start)

        return {
            "score": score, "score_xgb": score_xgb, "score_seq": score_seq, "decision": decision,
            "reasons": reasons, "sender_reasons": sender_reasons, "latency_ms": latency_ms,
            "features": dict(zip(FEATURE_NAMES, map(float, feats))),
        }


def test_rows(test):
    """Test rows as transaction dicts, in time order."""
    cols = ["ts", "src", "dst", "amount", "amount_paid", "payment_format",
            "receiving_currency", "payment_currency", "label"]
    out = test[cols].copy()
    for c in ("payment_format", "receiving_currency", "payment_currency"):
        out[c] = out[c].astype(str)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check live scores match training scores")
    parser.add_argument("--verify", type=int, default=2000, help="number of test transactions to compare")
    parser.add_argument("--data", default=DEFAULT_PATH)
    parser.add_argument("--cache", action="store_true",
                        help="load/save data/state_warm.pkl (needs several GB of free memory to save)")
    args = parser.parse_args(argv)
    use_cache = args.cache or USE_CACHE

    history, test, train_end = load_history(args.data)
    key = cache_key(history, train_end)
    state = warmed_state(history, train_end, use_cache=use_cache)
    del history
    gc.collect()
    if use_cache and not Path(CACHE).exists():
        save_state(state, key)  # before scoring: the cache must hold history only
    scorer = Scorer(state)
    rows = test_rows(test).iloc[: args.verify]

    saved = pd.read_pickle(ROOT / "data" / "xgb_scores.pkl")
    live, latencies = [], []
    for txn in rows.to_dict("records"):
        result = scorer.score(txn)
        live.append(result["score_xgb"])
        latencies.append(result["latency_ms"])
    expected = saved.loc[rows.index, "score_xgb"].to_numpy()
    diff = float(np.max(np.abs(np.asarray(live) - expected)))
    print(f"Scored {len(rows):,} test transactions live; max difference vs training scores: {diff:.2e}")
    print(f"Live latency incl. features and reasons: p50 {np.percentile(latencies, 50):.2f} ms, "
          f"p95 {np.percentile(latencies, 95):.2f} ms")
    print("MATCH" if diff < 1e-5 else "MISMATCH: live features differ from training")


if __name__ == "__main__":
    main()
