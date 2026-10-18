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
   - `in_count_1h`, `in_count_24h`, `lifetime_in_count`
   - `unique_senders_24h` (fan-in)
   - `out_count_24h`, `unique_receivers_24h` (fan-out)
   - `pass_through` ratio: out ÷ in amount over the last 1 h and 24 h (capped at 10)
   - `minutes_since_first_seen`
   - `log_amount`, `amount_vs_dst_mean`, `payment_format`, `receiving_currency`, `cross_currency`, `hour_of_day`, `is_self_transfer`
   - Proximity to flagged accounts: `dst_flagged`, `src_flagged`, flagged senders/receivers of the receiver in 24 h. Labels flag both accounts 24 h after the transaction (simulated report delay) and only up to the end of the training period. Rolling counterparty sets replace a networkx graph (much faster per transaction)
2. Use deques / dicts keyed by account for rolling windows so updates are O(1)-ish; target well under 1 ms per transaction.
3. Sequences for card 04 are built in card 04 from the time-ordered data (not stored per account here, to save memory).
4. `build_feature_table(df)` runs the state over a DataFrame in time order and returns a feature DataFrame + labels.
5. Notebook: build features for all dense days, save to `data/features_all.pkl` with a `split` column, show fraud vs normal comparisons.

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

If the full run is too slow or runs out of memory, build features on a sample of whole days and note it in `build-status.md`.

## Status

Done: verified on LinuxONE (see build-status.md)
