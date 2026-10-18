# Architecture

## Build Shape

Full-stack AI prototype: Python backend + two ML models + local LLM + two HTML views, in Docker on IBM LinuxONE.

## Stack Decision

All libraries below were confirmed installed in the L1CC Jupyter image (`pip list`), except FastAPI/Uvicorn which still need `pip install fastapi uvicorn`.

| Layer | Technology |
|---|---|
| Data / features | pandas 3.0, numpy, scikit-learn 1.9 |
| Model 1 | XGBoost 3.4.1; explanations via `booster.predict(dmatrix, pred_contribs=True)` (no `shap` package) |
| Model 2 | PyTorch 2.11 + `torch_nnpa` on Telum NNPA; TensorFlow 2.18 as fallback |
| LLM | IBM Granite via `llama_cpp_python` 0.3.36 (same loading approach as the Loan Approval lab) |
| API | FastAPI + Uvicorn |
| Storage | SQLite (Python built-in `sqlite3`) |
| Frontend | Plain HTML + CSS + vanilla JavaScript served by FastAPI (no build step, no Node) |
| Deployment | Docker on LinuxONE, built `FROM` the L1CC Jupyter image |
| Platform | L1CC, Ubuntu 24.04, s390x, Telum NNPA confirmed (`lscpu` → `nnpa`) |

## Structure Overview

```
 Transaction replay (time-ordered)          Sender view (mock transfer)
            │                                         │
            ▼                                         ▼
 ┌──────────────────────── LinuxONE server (s390x, Docker) ────────────────────────┐
 │  FastAPI                                                                        │
 │   ├─ Feature service: rolling per-account state (in-memory dicts + SQLite)      │
 │   ├─ Scorer: XGBoost (CPU) + PyTorch GRU (Telum NNPA) → ensemble → decision     │
 │   ├─ Reasons: top-k XGBoost pred_contribs → plain-language reason codes          │
 │   ├─ Explainer: Granite (llama.cpp) → sender warning EN/BM + analyst note        │
 │   └─ Case store: SQLite (transactions, cases, analyst decisions)                │
 └─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
 Analyst view (live feed, hold queue, approve/reject, latency stats)
```

## Component Map

| Module | Responsibility |
|---|---|
| `src/data.py` | Load dataset, clean columns, time-ordered split (train / validation / test by date) |
| `src/features.py` | `AccountState` class: rolling in/out counts and sums (1h, 24h), unique senders (fan-in), unique receivers (fan-out), pass-through ratio (out ÷ in, 1h and 24h), first-seen time; proximity to flagged accounts via rolling counterparty sets (labels act as reports: flag both accounts 24 h later, training period only). See `FEATURE_NAMES`. Same code used offline (training) and online (scoring), so there is no train/serve skew |
| `src/train_xgb.py` | Train XGBoost (`python -m src.train_xgb`), choose pause/hold thresholds by alert budget on validation, save `models/xgb.json`, `thresholds.json`, `metrics.json` |
| `src/reasons.py` | Top-3 reasons per transaction from XGBoost `pred_contribs`, as `{code, feature, value, contribution, sentence}`; sentences use counts and amounts only |
| `src/train_seq.py` | Train GRU over the receiver's last N=10 transactions, save `models/seq.pt` |
| `src/scorer.py` | Load models, score one transaction, ensemble, apply decision bands, return reasons |
| `src/explain.py` | Build privacy-safe prompt from reason codes + aggregates, call Granite, return `warning_en`, `warning_bm`, `analyst_note`; template fallback if Granite is slow/unavailable |
| `src/stream.py` | Replay test-period transactions in time order at a configurable speed |
| `src/db.py` | SQLite tables and helpers |
| `src/api.py` | FastAPI app, endpoints, serves `web/` |
| `web/sender.html` | Mock transfer screen + warning pop-up |
| `web/analyst.html` | Live feed, hold queue, case detail, approve/reject, stats |
| `notebooks/` | Exploration, training, evaluation, NNPA latency benchmark |

## Data / State Model

**Dataset:** IBM "Transactions for Anti Money Laundering (AML)" (Kaggle `ealtman2019/ibm-transactions-for-anti-money-laundering-aml`), file `HI-Small_Trans.csv`. Expected columns (verify on load): `Timestamp, From Bank, Account, To Bank, Account.1, Amount Received, Receiving Currency, Amount Paid, Payment Currency, Payment Format, Is Laundering`.

- **Account ID** = bank + account (e.g. `"011_8000ABC"`), used only as an opaque key.
- **Label** = `Is Laundering` on the transaction; the receiver of a laundering transaction is treated as a suspected mule for graph features (training period only, to avoid leakage).

**SQLite tables:**

| Table | Fields |
|---|---|
| `transactions` | `id, ts, src, dst, amount, payment_format, score_xgb, score_seq, score, decision, reasons_json, latency_ms, source ('replay' or 'sender')` |
| `cases` | `id, txn_id, status ('paused','held','approved','rejected'), warning_en, warning_bm, analyst_note, analyst_decision, decided_at` |

**Decision bands** are set by an alert budget on the validation set (scores are not calibrated probabilities because of `scale_pos_weight`). Defaults, stored in `models/thresholds.json`:

| Score | Decision | Default budget |
|---|---|---|
| below `pause` | Allow | |
| `pause` – `hold` | Pause & warn | top 0.5% of transfers |
| at or above `hold` | Hold for analyst | top 0.05% of transfers |

Change with `python -m src.train_xgb --pause-rate ... --hold-rate ...` after reading the alert-budget table in `notebooks/03_xgboost.ipynb`.

## Storage Logic

- Raw data: `data/` (gitignored), on the server under `~/shared/trustpause/data/`.
- Models: `models/` (small files committed if < 50 MB, otherwise gitignored and documented).
- Runtime: `trustpause.db` (SQLite, gitignored).
- Granite model file: path from the Loan Approval lab, set via env var `GRANITE_MODEL_PATH`.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
Implemented in `src/api.py` (card 06). Full request/response schemas at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/status` | `{stage, error, granite}`; every other endpoint returns 503 until `stage == "ready"` (warm-up) |
| `GET` | `/api/demo-accounts` | `[{id, label, currency}]`: 3 receivers that stay risky and 3 that stay safe for a demo-sender transfer at 100 / 1,000 / 10,000 (checked by preview at startup; US-dollar accounts; labels don't reveal which) |
| `POST` | `/api/transfer` | Sender view: `{dst, amount}` → `{txn_id, case_id, decision, score, score_xgb, score_seq, latency_ms, sender_reasons, warning_en, warning_bm}`. Sender is the fixed `DEMO_SENDER`; time is the replay clock |
| `POST` | `/api/transfer/{case_id}/choice` | Sender's answer to a pause: `{choice: "cancel" or "continue"}` |
| `POST` | `/api/replay/start` | Start replay `{speed}` (transactions per second, 1–5000) |
| `POST` | `/api/replay/stop` | Stop replay |
| `GET` | `/api/feed?since=<id>&limit=50` | Latest scored transactions, newest first (no account IDs); analyst view polls every 1 s |
| `GET` | `/api/queue` | Held cases waiting for review: `{case_id, status, note_source, ts, amount, currency, score, first_reason}` |
| `GET` | `/api/case/{id}` | Case detail: transaction, scores, `reasons` (analyst), `sender_reasons`, `warning_en/bm` (always template), `analyst_note`, `note_source` (`template` or `granite`) |
| `POST` | `/api/case/{id}/decision` | Analyst `{decision: "approve" or "reject"}`; 409 if not held |
| `GET` | `/api/metrics` | Decision counts, laundering seen/flagged in replay, latency p50/p95, txn/sec, replay position, clock, thresholds, `sequence_model`, `granite`, `granite_queue` |
| `GET` | `/`, `/sender`, `/analyst`, `/web/<file>` | Pages from `web/` (card 07) |

**Granite (card 05), decided for the demo:** the sender's warnings always come from the reviewed templates in `src/templates.py` (specific, predictable, checked by a Malay speaker). Granite only drafts the **analyst note for held cases**: `explain(payload)` gets `{decision, score, amount_band, currency, reasons}` (no account IDs), and its `analyst_note` replaces the template note only if `used_granite` is true and the note passes `good_note()` (three labelled bullets, not explain.py's fallback, not the prompt's example). Sender holds go first; replayed holds only while the queue is under 5. Start the API with `GRANITE_MODEL_PATH`; `/api/status` → `granite_last` shows the latest result. Pitch line: the AI never writes the customer-facing warning unreviewed; Granite drafts notes for a human analyst.

## User Flow

**Sender:** open `/sender` → choose recipient from demo list → enter amount → Send → if Allow: success; if Pause: pop-up with warning and "Cancel transfer" (primary) / "I understand, continue"; if Hold: "This transfer is being reviewed for your protection".

**Analyst:** open `/analyst` → press Start replay → feed scrolls with Allow/Pause/Hold chips → click a held case → read reasons + Granite note → Approve or Reject → case leaves queue, decision logged.

## Real-Time Path and Latency

- Decision path (features → XGBoost + GRU → bands) must be **fast (target < 50 ms)**. It does not wait for Granite.
- Granite runs **only for paused/held cases**, in a background thread; the UI shows a template warning instantly and swaps in Granite text when ready.
- Every scored transaction records `latency_ms`; `/api/metrics` reports p50/p95.

## File Expectations

```
trustpause/
├── data/                 # gitignored
├── models/
├── notebooks/
│   ├── 01_explore.ipynb
│   ├── 02_features.ipynb
│   ├── 03_xgboost.ipynb
│   └── 04_sequence_nnpa.ipynb
├── src/                  # modules listed above
├── web/
│   ├── sender.html
│   └── analyst.html
├── screenshots/
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

## Constraints

- s390x: only use libraries already in the image or pure-Python packages; test any new install early.
- One shared server: check `free -h` and `nproc`; sample data if memory is tight; avoid parallel training.
- Granite on CPU is slow (seconds); never on the decision path.
- No external network calls at runtime: the app must work fully on the server.

## Technical Non-Goals

- Login / authentication
- Real bank integration, real customer data
- Kafka or distributed streaming
- Public hosting (judges see it in the video)
- Retraining pipeline

## Verification Notes

- Offline: PR-AUC, precision/recall at each band on the **time-based test set**.
- Online: replay 10,000+ test transactions; report decision counts and latency p50/p95.
- NNPA: same GRU, CPU vs NNPA timing, batch sizes 1 and 64; report honestly.
- Privacy: log the exact prompt sent to Granite once and confirm it contains no account IDs.
