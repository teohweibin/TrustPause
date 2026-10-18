# Build Status

## Project

- Name: TrustPause (working name)
- Submission title: `[TeamName]_IBM Z Datathon 2026 Project — TrustPause`
- Theme: Theme 1, Real-Time AI for Critical Decisions
- Build shape: Full-stack AI prototype on IBM LinuxONE (FastAPI + XGBoost + PyTorch/NNPA + Granite + 2 HTML views, Docker)
- Current stage: Building
- Current work card: `work-cards/06-scorer-replay-api.md` (code written; verify on LinuxONE), then 07 views on the real API; in parallel 04 NNPA probe, 05, 06 stub, 07 mock, 09; finish open items in `work-cards/00-setup-gate.md` alongside

## Completed work cards

- [ ] 00 LinuxONE setup gate (mostly done)
- [x] 01 Repo, data and environment
- [x] 02 Feature pipeline
- [x] 03 XGBoost model + reasons
- [ ] 04 Sequence model on Telum NNPA
- [ ] 05 Granite explainer
- [ ] 06 Real-time scorer, replay and API
- [ ] 07 Sender and analyst views
- [ ] 08 Docker on LinuxONE
- [ ] 09 Evidence, README, video and submission

## In progress

- 00 Setup gate: remaining items (Discord lab confirmation, `.pem` sharing, roles)
- 06 Scorer + API: `src/scorer.py`, `src/api.py`, `src/db.py`, `src/stream.py`, `src/templates.py` written; tested on synthetic data (live scores match training exactly); run on LinuxONE pending

## Blockers

- None recorded yet

## Decisions made

- Theme: Theme 1 (Real-Time AI for Critical Decisions)
- Stack: Python, pandas, XGBoost, PyTorch + torch_nnpa, llama.cpp + Granite, FastAPI, SQLite, plain HTML/CSS/JS, Docker
- Dataset: IBM AML synthetic (`HI-Small_Trans.csv`), licence to verify
- Split: time-based by calendar day after dropping sparse days (< 1% of busiest day). HI-Small: drop Sep 11–18 (only ~1,100 rows, ~60% laundering); train Sep 1–6, val Sep 7–8, test Sep 9–10
- Features: online `AccountState` (24 features, see `FEATURE_NAMES`). Flagged-account proximity via rolling counterparty sets instead of networkx. Labels act as reports: flag both accounts 24 h later, training-period labels only
- Explanations: XGBoost `pred_contribs` (no `shap` package) → `src/reasons.py` reason codes
- Decision bands: alert budget on validation (default pause top 0.5%, hold top 0.05%), stored in `models/thresholds.json`
- LLM: Granite on LinuxONE only; no external AI APIs; no IDs in prompts
- Storage: SQLite (`data/trustpause.db`, reset on API start, WAL, no fsync: demo data)
- Live scoring: API warms `AccountState` with all history before the test period (same code and label cutoff as training), so live scores equal training scores; cached in `data/state_warm.pkl`
- Granite jobs: sender first, replayed holds only when queue < 5, replayed pauses never; templates shown instantly
- Frontend: sender view + analyst view, served by FastAPI
- Access: SSH tunnels (Jupyter 38888, app 8000); no public ports
- Deployment: Docker on LinuxONE; judges see it in the video
- Server Git: `~/shared/trustpause` always stays on `main`; personal branches use personal clones (e.g. `~/shared/trustpause-<name>`) with the dataset symlinked

## Last verified state

- Server: ACTIVE, SSH works (user `linux1`)
- Docker: installed and working
- Jupyter: running in container `notebook`, reached via SSH tunnel
- IBM labs: both run; screenshots in `screenshots/labs/`
- Telum NNPA: present (`lscpu` → `nnpa`)
- Libraries: xgboost 3.4.1, torch 2.11.0+cpu, torch_nnpa 1.5.0, tensorflow 2.18.1, llama_cpp_python 0.3.36, networkx 3.7, pandas 3.0.6, scikit-learn 1.9.0
- FastAPI / Uvicorn: installed in the Jupyter container
- Server CPU: 3 (`nproc`). `free` is not available inside the Jupyter container; run `free -h` in the SSH window
- `torch_nnpa` usage: not tested
- Granite generation time: not measured
- Dataset on server: `data/HI-Small_Trans.csv`, loading verified on LinuxONE.
- GitHub repo: https://github.com/teohweibin/TrustPause (cloned on server at `~/shared/trustpause`); branch `xiaowei` merged into `main`

## Work Card 01 Verification

- Dataset: `data/HI-Small_Trans.csv` (454 MB)
- Rows loaded: 5,078,345 in ~11–14 s; DataFrame memory ~0.8 GB
- Sparse tail dropped: Sep 11–18 (1,108 rows, ~60% laundering)
- Train: Sep 1–6, 3,248,921 rows, 2,530 laundering (0.0779%)
- Val: Sep 7–8, 965,524 rows, 1,036 laundering (0.1073%)
- Test: Sep 9–10, 862,792 rows, 956 laundering (0.1108%)
- Test dates are later than training dates.
- Exploration notebook executed on LinuxONE with no errors.
- Git ignore checks passed for `data/`, `*.pem`, and `*.db`.
- Mandatory-lab confirmation: Pending.

### Findings for Work Card 02

- Fan-in is a signal but not linear: laundering share ~0.03% for 1 sender, ~1.2% for 10–50 senders, drops again above 50 senders (likely businesses, a false-positive risk).
- Payment format matters: ACH 0.75% laundering; Reinvestment and Wire 0%.
- Amounts are in 15+ currencies (incl. Bitcoin); features must handle currency.
- Some rows are self-transfers (`src == dst`, e.g. Reinvestment).

## Work Card 02 Verification

- Build: `nohup python -m src.features > data/features_build.log 2>&1 &` → `data/features_all.pkl`
- 5,077,237 rows in 131 s on LinuxONE (**25.8 µs per transaction**, single core); 515,078 accounts; 3,471 flagged accounts (training labels only)
- Unit check passed; `No look-ahead: True` (first 100,000 rows identical when rebuilt alone)
- Split unchanged: train 3,248,921 / val 965,524 / test 862,792

### Findings for Work Card 03 / pitch

- Strongest signals (laundering ÷ normal mean, training period): `dst_flagged` 51×, `dst_flagged_receivers_24h` 13×, `src_flagged` 4.5×, `dst_flagged_senders_24h` 4.3×, sender fan-out (`src_unique_receivers_24h`, `src_out_count_24h`) 1.9×.
- Laundering goes to **new counterparties** (`sender_known_to_dst_24h` 0.32×) and to receivers that have **barely sent anything yet** (`dst_out_count_*` ~0.2×).
- Fan-in band 5–10 senders: 0.81% laundering vs 0.06% baseline (~13×); lower again above 10 senders (likely businesses).
- **Pass-through does not separate laundering in this dataset** (0.8–0.95×). Do not claim it in the pitch unless the model shows it matters.
- Test period only sees flags from before Sep 6, so expect test scores below validation; report both.
- `amount_vs_dst_mean` has extreme values: fine for XGBoost, log-scale it for the GRU (card 04).
- `payment_format` and `receiving_currency` are category codes (first-appearance order): treat as categorical in card 03. Card 06 must warm up `AccountState` on the same data in the same order (or save `state.codes`) so codes match at serving time.
- `cross_currency` and `is_self_transfer` are ~0 for laundering.

## Work Card 03 Notes

- Top features by gain: `payment_format` (ACH-heavy laundering, a dataset quirk), `is_self_transfer`, `src_flagged`, `sender_known_to_dst_24h`, `src_unique_receivers_24h`, `dst_flagged_senders_24h`.
- Test below validation as expected (flags frozen after training period); pause band drifts from 0.5% to 0.70% on test. Pitch: thresholds are re-tuned regularly.
- Highest-scored normal transfer is held (sender linked to a reported case): good demo moment for human review.
- Reasons: behavioural reasons first, generic payment properties only as filler; each reason has `about` (receiver / sender / payment). `audience="sender"` hides sender-side reasons for the sender view; the analyst view shows all.

## Measured results (fill in as you go)

- Feature computation per transaction (LinuxONE, single core): 25.8 µs

- XGBoost PR-AUC: val 0.361, **test 0.254** (base rate 0.11%, ~230× lift); ROC-AUC val 0.982, test 0.974
- Ensemble test PR-AUC:
- Hold band (top 0.05% on val): test 0.049% of transfers held, **precision 52%, recall 23%** (val 62% / 29%)
- Pause band (top 0.5% on val): test 0.70% of transfers paused, **precision 8%, recall 52%** (val 13% / 62%)
- XGBoost single prediction on LinuxONE: p50 0.10 ms, p95 0.30 ms (best iteration 283, trained in 74 s)
- End-to-end scoring latency p50 / p95 (card 06):
- GRU latency CPU vs NNPA (batch 1 / 64):
- Granite time per output:

## Next instruction for AI

Read `START_HERE.md`, `build-status.md`, `build-blueprint.md`, `architecture.md`, `design.md` and the current work card. Implement only the current work card. Run its verification steps, update this file, and stop for the team's check.
