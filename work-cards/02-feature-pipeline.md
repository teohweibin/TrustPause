# Work Card 02: Feature Pipeline

## Goal

One `AccountState` class that produces receiver-side features for each transaction in time order, used for both training and live scoring.

## Owner

A (Data & features)

## Inputs

- `src/data.py` from card 01
- `architecture.md` → Component Map (`features.py`)

## Files likely touched

`src/features.py`, `notebooks/02_features.ipynb`, `data/features_*.parquet` (gitignored)

## Instructions for the coding agent

1. `AccountState.update_and_features(txn)` returns features for the **receiver** (`dst`) computed from history **before** this transaction, then updates state:
   - `in_count_1h`, `in_count_24h`, `in_sum_24h`
   - `unique_senders_24h` (fan-in)
   - `out_count_24h`, `unique_receivers_24h` (fan-out)
   - `pass_through_ratio`: out ÷ in within the last 30 min
   - `minutes_since_first_seen`
   - `amount`, `amount_vs_receiver_median`, `payment_format` (encoded), `hour_of_day`
   - `hops_to_known_mule` (0/1/2/3+) using a networkx graph of training-period edges and training-period mule labels only
2. Use deques / dicts keyed by account for rolling windows so updates are O(1)-ish; target well under 1 ms per transaction.
3. Also keep the receiver's last 10 transactions (for card 04's sequence model).
4. `build_feature_table(df)` runs the state over a DataFrame in time order and returns a feature DataFrame + labels.
5. Notebook: build tables for train/val/test, save to parquet, show feature distributions for fraud vs normal.

## What not to do

- No future data in any feature (no look-ahead).
- No mule labels from val/test periods in graph features.

## Done when

Feature tables for all three splits exist and features differ visibly between fraud and normal receivers.

## Verification steps

- Unit check: feed 3 hand-made transactions and confirm counts are correct.
- Time per transaction measured and printed.
- Leakage check: features for transaction *t* do not change if later rows are removed.

## Test before continuing

- Run `02_features.ipynb` end to end.
- Look at the fraud vs normal comparison chart: fan-in and pass-through should be higher for fraud.

## Stop condition

If graph features are too slow, drop to `hops_to_known_mule` ≤ 1 (direct neighbour) and note it in `build-status.md`.

## Status

Not started
