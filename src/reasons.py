"""Turn XGBoost feature contributions into plain-language reason codes.

Sentences use counts and amounts only, never account IDs, so they are safe to
show the sender and to pass to Granite.
"""

import math

import numpy as np


def _hours(minutes):
    if minutes < 0:
        return "has never received money before"
    if minutes < 60:
        return f"was first seen {minutes:.0f} minutes ago"
    if minutes < 48 * 60:
        return f"was first seen {minutes / 60:.0f} hours ago"
    return f"was first seen {minutes / 1440:.0f} days ago"


def _pass_through(v, window):
    if v >= 10:
        return f"the receiving account sent out far more than it received in the last {window}"
    return f"the receiving account sent on {v:.0%} of what it received in the last {window}"


def _n(value, word, plural=None):
    """'no transfers', '1 transfer', '3 transfers'."""
    n = int(round(value))
    if n == 0:
        return f"no {plural or word + 's'}"
    return f"{n} {word if n == 1 else plural or word + 's'}"


# feature -> (code, sentence builder taking the feature value)
REASONS = {
    "dst_flagged": ("RECEIVER_REPORTED",
                    lambda v: "the receiving account is linked to an earlier reported case"),
    "src_flagged": ("SENDER_REPORTED",
                    lambda v: "the sending account is linked to an earlier reported case"),
    "dst_flagged_senders_24h": ("RECEIVER_PAID_BY_REPORTED",
                                lambda v: f"the receiving account got money from {_n(v, 'reported account')} in the last 24 hours"),
    "dst_flagged_receivers_24h": ("RECEIVER_PAYS_REPORTED",
                                  lambda v: f"the receiving account sent money to {_n(v, 'reported account')} in the last 24 hours"),
    "dst_unique_senders_24h": ("FAN_IN_HIGH",
                               lambda v: f"the receiving account got money from {_n(v, 'different sender')} in the last 24 hours"),
    "dst_in_count_1h": ("RECEIVER_BURST",
                        lambda v: f"the receiving account received {_n(v, 'transfer')} in the last hour"),
    "dst_in_count_24h": ("RECEIVER_VOLUME",
                         lambda v: f"the receiving account received {_n(v, 'transfer')} in the last 24 hours"),
    "sender_known_to_dst_24h": ("NEW_RECIPIENT",
                                lambda v: "this is a new recipient for this sender"
                                if v < 0.5 else "the sender has paid this recipient recently"),
    "dst_minutes_since_first_seen": ("NEW_ACCOUNT",
                                     lambda v: f"the receiving account {_hours(v)}"),
    "dst_lifetime_in_count": ("FEW_PAST_RECEIPTS",
                              lambda v: f"the receiving account has received only {_n(v, 'transfer')} before"),
    "dst_out_count_1h": ("RECEIVER_OUTFLOW_1H",
                         lambda v: f"the receiving account sent {_n(v, 'transfer')} in the last hour"),
    "dst_out_count_24h": ("RECEIVER_OUTFLOW",
                          lambda v: f"the receiving account sent {_n(v, 'transfer')} in the last 24 hours"),
    "dst_unique_receivers_24h": ("RECEIVER_FAN_OUT",
                                 lambda v: f"the receiving account paid {_n(v, 'different account')} in the last 24 hours"
                                 if v >= 1 else "the receiving account has not paid anyone in the last 24 hours"),
    "dst_pass_through_1h": ("PASS_THROUGH",
                            lambda v: _pass_through(v, "hour")),
    "dst_pass_through_24h": ("PASS_THROUGH",
                             lambda v: _pass_through(v, "24 hours")),
    "src_unique_receivers_24h": ("SENDER_FAN_OUT",
                                 lambda v: f"the sending account paid {_n(v, 'different account')} in the last 24 hours"
                                 if v >= 1 else "the sending account has not paid anyone else in the last 24 hours"),
    "src_out_count_24h": ("SENDER_VOLUME",
                          lambda v: f"the sending account made {_n(v, 'payment')} in the last 24 hours"
                          if v >= 1 else "the sending account made no other payments in the last 24 hours"),
    "log_amount": ("AMOUNT",
                   lambda v: f"the amount ({math.expm1(v):,.0f}) fits a risky pattern"),
    "amount_vs_dst_mean": ("AMOUNT_UNUSUAL",
                           lambda v: f"the amount is {v:,.1f} times what this receiver usually gets"),
    "payment_format": ("PAYMENT_TYPE",
                       lambda v: "this payment type is common in reported cases"),
    "receiving_currency": ("CURRENCY",
                           lambda v: "this currency is common in reported cases"),
    "cross_currency": ("CROSS_CURRENCY",
                       lambda v: "the payment changes currency" if v > 0.5 else "the payment stays in one currency"),
    "is_self_transfer": ("NOT_SELF_TRANSFER",
                         lambda v: "this is a transfer between different accounts"),
    "hour_of_day": ("TIME_OF_DAY",
                    lambda v: f"the transfer was made around {v:02.0f}:00"),
}


# Properties of the payment itself: real model signal, but they tell a person
# little, so they are only used when there are not enough behavioural reasons.
GENERIC = {"payment_format", "receiving_currency", "log_amount", "hour_of_day",
           "is_self_transfer", "cross_currency"}
# Reasons about the paying account. The sender view hides these (the sender is
# the person being protected); the analyst view shows everything.
SENDER_SIDE = {"src_flagged", "src_unique_receivers_24h", "src_out_count_24h"}
# Activity counts. A zero ("received no transfers in the last hour") can raise the
# score, but reads oddly as a warning, so the sender view skips zero counts.
COUNTS = {"dst_in_count_1h", "dst_in_count_24h", "dst_unique_senders_24h", "dst_out_count_1h",
          "dst_out_count_24h", "dst_unique_receivers_24h", "dst_flagged_senders_24h",
          "dst_flagged_receivers_24h", "dst_pass_through_1h", "dst_pass_through_24h"}


def about(feature):
    if feature in SENDER_SIDE:
        return "sender"
    if feature in GENERIC or feature == "amount_vs_dst_mean":
        return "payment"
    return "receiver"


def reason(feature, value, contribution=None):
    code, sentence = REASONS.get(feature, ("OTHER", lambda v: feature.replace("_", " ")))
    item = {"code": code, "feature": feature, "about": about(feature),
            "value": float(value), "sentence": sentence(float(value))}
    if contribution is not None:
        item["contribution"] = round(float(contribution), 4)
    return item


def top_reasons(contribs, values, feature_names, k=3, audience="analyst"):
    """Top-k reasons pushing the score up for one transaction.

    contribs: one row of `pred_contribs` (last column is the bias).
    values: the matching feature values.
    audience: "analyst" (all reasons) or "sender" (no reasons about the paying account,
    no zero activity counts).
    Behavioural reasons come first, by contribution; generic payment properties
    only fill remaining slots.
    """
    contribs = np.asarray(contribs)[: len(feature_names)]
    candidates = [j for j in np.argsort(-contribs) if contribs[j] > 0]
    if audience == "sender":
        candidates = [j for j in candidates if feature_names[j] not in SENDER_SIDE
                      and not (feature_names[j] in COUNTS and values[j] == 0)]
    candidates.sort(key=lambda j: feature_names[j] in GENERIC)  # stable: keeps contribution order

    out, seen = [], set()
    for j in candidates:
        item = reason(feature_names[j], values[j], contribs[j])
        if item["code"] in seen:  # e.g. both pass-through windows
            continue
        seen.add(item["code"])
        out.append(item)
        if len(out) == k:
            break
    return out


def reasons_for(booster, X, feature_names, k=3, audience="analyst"):
    """Top-k reasons for every row of X (2-D array or DataFrame)."""
    import xgboost as xgb

    values = np.asarray(X, dtype=np.float32)
    contribs = booster.predict(xgb.DMatrix(values, feature_names=list(feature_names)), pred_contribs=True)
    return [top_reasons(c, v, feature_names, k, audience) for c, v in zip(contribs, values)]
