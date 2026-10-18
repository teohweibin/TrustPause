# Work Card 06: Real-Time Scorer, Replay and API

## Goal

A FastAPI backend that scores transactions live (replay and sender requests), applies the decision bands, runs Granite in the background for Pause/Hold, stores everything in SQLite, and exposes the endpoints in `architecture.md`.

## Owner

E (API)

## Inputs

`src/features.py`, `models/xgb.json`, `models/thresholds.json`, `src/explain.py`, optional `models/seq.pt`

## Files likely touched

`src/scorer.py`, `src/stream.py`, `src/db.py`, `src/api.py`

## Instructions for the coding agent

1. `scorer.py`: load models once; `score(txn)` → features → XGBoost (+ GRU if available) → ensemble → band → top reasons; measure `latency_ms`.
2. Warm up `AccountState` with the train+val period at startup so live features have history.
3. `stream.py`: background thread replays the test split in time order at a configurable speed (e.g. 50 txn/s).
4. `db.py`: create `transactions` and `cases` tables (see `architecture.md`).
5. For Pause/Hold: insert a case with template warnings immediately; a worker thread calls Granite and updates the case.
6. `/api/demo-accounts`: pick ~6 recipients from the test period: 3 low-risk, 3 high-risk, with neutral labels ("Recipient A — Online seller").
7. Implement all endpoints in `architecture.md`; serve `web/` as static files.
8. Run on the server: `uvicorn src.api:app --host 0.0.0.0 --port 8000`; view through SSH tunnel `-L 8000:localhost:8000`.

## What not to do

- Do not call Granite inside the request that makes the decision.
- Do not open port 8000 to the internet; use the tunnel.
- No login system.

## Done when

Replay runs; `/api/feed`, `/api/queue`, `/api/metrics` return real data; `/api/transfer` returns a decision in < 100 ms.

## Verification steps

- `curl` or `/docs` (Swagger) for each endpoint.
- `/api/metrics` shows latency p50/p95 and decision counts.
- A held case gets its Granite note within the measured Granite time.

## Test before continuing

- Start replay, wait 1 minute, check `/api/metrics`.
- POST a transfer to a high-risk demo account → Pause or Hold.
- POST a transfer to a low-risk demo account → Allow.

## Stop condition

If threading causes problems, run replay as a separate process writing to SQLite and let the API only read.

## Status

In progress: code written and tested end to end on synthetic data; run on LinuxONE pending
