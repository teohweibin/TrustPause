# Build Status

## Project

- Team: **Stats Power**
- Name: TrustPause
- Submission title: `Stats Power_IBM Z Datathon 2026 Project — TrustPause`
- Theme: Theme 1, Real-Time AI for Critical Decisions
- Build shape: Full-stack AI prototype on IBM LinuxONE (FastAPI + XGBoost + PyTorch/NNPA benchmark + Granite + 2 web views, Docker)
- Repo: https://github.com/teohweibin/TrustPause (`main`); server copy at `~/shared/trustpause`
- Current stage: **Submission prep**: everything is built and running on LinuxONE; the video and submission remain
- Current work card: `work-cards/09-evidence-video-submission.md`

## Completed work cards

- [x] 00 LinuxONE setup gate
- [x] 01 Repo, data and environment
- [x] 02 Feature pipeline
- [x] 03 XGBoost model + reasons
- [x] 04 Sequence model on Telum NNPA
- [x] 05 Granite explainer
- [x] 06 Real-time scorer, replay and API
- [x] 07 Sender and analyst views
- [x] 08 Docker on LinuxONE
- [ ] 09 Evidence, README, video and submission (README done; video, screenshots and submission remain)

## Remaining

- **3-minute video**: script, shot list, recording (must show the LinuxONE instance and the model running)
- **Live screenshots**: sender warning, analyst console during replay, `uname -m` → `s390x`, `docker ps`, L1CC dashboard
- **Architecture flowchart**: a teammate has it on their branch; merge into `main`
- **Notebooks 02 and 03 outputs**: executed on the server but committed without outputs; commit the server copies with outputs
- **Hack2Skill submission**: title, GitHub link, video, open-source links (listed in the README)

## Blockers

- None

## Decisions made

- Theme: Theme 1 (Real-Time AI for Critical Decisions)
- Stack: Python, pandas, XGBoost, PyTorch + torch_nnpa, llama.cpp + IBM Granite, FastAPI, SQLite, plain HTML/CSS/JS, Docker
- Dataset: IBM AML synthetic (`HI-Small_Trans.csv`), licence CDLA-Sharing-1.0 (https://cdla.dev/sharing-1-0/)
- Split: time-based by calendar day after dropping sparse days (< 1% of busiest day). HI-Small: drop Sep 11–18 (only ~1,100 rows, ~60% laundering); train Sep 1–6, val Sep 7–8, test Sep 9–10
- Features: online `AccountState` (24 features, see `FEATURE_NAMES`). Flagged-account proximity via rolling counterparty sets instead of networkx. Labels act as reports: flag both accounts 24 h later, training-period labels only
- Model: XGBoost only for live decisions (validation chose ensemble weight 1.0; the GRU is kept as the NNPA benchmark)
- Explanations: XGBoost `pred_contribs` (no `shap` package) → `src/reasons.py` reason codes; behavioural reasons first; sender view hides sender-side reasons and zero counts
- Decision bands: alert budget on validation (pause top 0.5%, hold top 0.05%), stored in `models/thresholds.json`
- LLM: IBM Granite on LinuxONE only; no external AI APIs; no IDs in prompts
- Granite: analyst notes for held cases only (validated by `good_note()`); sender warnings always the reviewed EN/BM templates. Reason: the 350M base model copied the prompt example on LinuxONE
- Storage: SQLite (`data/trustpause.db`, reset on API start, WAL, no fsync: demo data)
- Live scoring: API warms `AccountState` with all history before the test period (same code and label cutoff as training), so live scores equal training scores. The warm-state cache (`data/state_warm.pkl`) is off by default (saving it ran out of memory); enable with `TRUSTPAUSE_STATE_CACHE=1`
- Sender-view transfers are scored without being recorded (`record=False`), so the demo behaves the same every time; replayed transactions are recorded
- Demo recipients: chosen at startup by previewing demo-sender transfers (US-dollar accounts). Risky recipients must warn at 2+ scam-like amounts; the strongest becomes "Job agency" and its first warning amount drives the scam-message story. `/api/status` → `demo_check` shows the result
- Sender view: fictional mobile bank (phone frame, scam message, keypad, purpose, security check, 997 NSRC hotline); analyst view: live stats, feed, hold queue, case detail with Release / Block
- Access: SSH keys only; Jupyter (38888) and the API (8000) reached through SSH tunnels; no public ports
- Secrets: the `.pem` key is never committed or shared publicly (`*.pem` in `.gitignore` and `.dockerignore`; no `.pem` in any commit); share it with teammates privately only
- Models in Git: `models/xgb.json`, `thresholds.json`, `metrics.json`, `seq.pt` are committed (a `git stash -u` once hid the uncommitted ones)
- Deployment: Docker on LinuxONE (s390x image from the L1CC Jupyter image; data, models and Granite mounted at runtime)
- Server Git: `~/shared/trustpause` always stays on `main`; personal branches use personal clones (e.g. `~/shared/trustpause-<name>`) with the dataset symlinked. Restart the API after pulls that change `src/`
- IBM labs: run as learning demos (not a submission requirement for this team)

## Last verified state

- Server: ACTIVE, SSH works (user `linux1`); 3 CPUs, 7.8 GB RAM, no swap
- Docker: installed; `trustpause` image builds and runs (s390x)
- Jupyter: running in container `notebook`, reached via SSH tunnel
- IBM labs: both run as learning demos; screenshots in `screenshots/labs/`
- Telum NNPA: present (`lscpu` → `nnpa`); `torch_nnpa` `is_available()` and `is_telum2_available()` return `True`; GRU runs on `nnpa:0`
- Libraries: xgboost 3.4.1, torch 2.11.0+cpu, torch_nnpa 1.5.0, tensorflow 2.18.1, llama_cpp_python 0.3.36, networkx 3.7, pandas 3.0.6, scikit-learn 1.9.0; FastAPI / Uvicorn installed
- Granite: `granite-4.0-h-350m-base-be.f16.gguf`; English 3.77–4.24 s, BM 5.54–6.17 s, analyst note 7.88–11.95 s
- Dataset on server: `data/HI-Small_Trans.csv`
- API on LinuxONE (latest `main`): `stage: ready`; all six demo recipients `passed: true` (A/C/E warn at every amount $500–$5,000, scores 0.96–0.998; B/D/F allowed at every amount); story = Job agency, $500; story warning confirmed in the browser
- GitHub `main` contains all code, trained models, notebooks, screenshots, README and Docker files

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

## Work Card 04 Verification

- Implementation: `src/train_seq.py`
- Model: PyTorch GRU, sequence length 10, hidden size 32
- Training sample: 100,000 sequences; 2,530 positive and 97,470 negative
- Model artifact: `models/seq.pt`
- Notebook: `notebooks/04_sequence_nnpa.ipynb`
- Notebook audit: 4 code cells, 0 unexecuted cells, 0 error cells
- Sequence PR-AUC: validation `0.010882`; test `0.005142`
- XGBoost PR-AUC: validation `0.360805`; test `0.254146`
- Validation-selected ensemble XGBoost weight: `1.0`
- CPU/NNPA output comparison: `outputs_close: True`; maximum absolute difference `0.000244140625`
- NNPA latency chart: `screenshots/sequence_latency.png`
- NNPA hardware evidence: `lscpu | grep -io nnpa` returned `nnpa`

## Work Card 05 Verification

- Implementation: `src/explain.py`
- Model runtime: local `llama_cpp_python` Granite using `GRANITE_MODEL_PATH`
- Model: `/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf`
- Five reason combinations generated English warning, Bahasa Malaysia warning, and analyst note.
- All analyst notes contain exactly three bullets: Pattern, Evidence, and Suggested action.
- Prompt privacy check: `prompt_has_identifiers: False`
- Malay speaker review: Approved
- Notebook: `notebooks/05_granite.ipynb`
- Notebook audit: 4 code cells, 0 unexecuted cells, 0 error cells
- Privacy screenshot: `screenshots/granite_prompt_privacy.png`
- Maximum observed generation time: 11.95 seconds
- Granite timeout stop condition: not triggered
- Informational runtime message about V-cache padding was observed; no generation failure occurred.

## Measured results

- Feature computation per transaction (LinuxONE, single core): 25.8 µs

- XGBoost PR-AUC: val 0.361, **test 0.254** (base rate 0.11%, ~230× lift); ROC-AUC val 0.982, test 0.974
- Ensemble: validation chose XGBoost weight 1.0 (GRU test PR-AUC 0.005 vs XGBoost 0.254), so live decisions use XGBoost alone
- Hold band (top 0.05% on val): test 0.049% of transfers held, **precision 52%, recall 23%** (val 62% / 29%)
- Pause band (top 0.5% on val): test 0.70% of transfers paused, **precision 8%, recall 52%** (val 13% / 62%)
- XGBoost single prediction on LinuxONE: p50 0.10 ms, p95 0.30 ms (best iteration 283, trained in 74 s)
- End-to-end scoring latency on LinuxONE (features + XGBoost + reasons, replay at 100 tx/s): **p50 0.30 ms, p95 0.72 ms**
- Live scores equal training scores (`python -m src.scorer --verify 2000` → MATCH on LinuxONE)
- GRU latency CPU vs NNPA over 1,000 runs: CPU batch 1 p50/p95 `0.171/0.192 ms`; CPU batch 64 `1.693/1.870 ms`; NNPA batch 1 `0.082/0.093 ms`; NNPA batch 64 `0.131/0.140 ms`
- Granite time per output: English 3.77–4.24 s; Bahasa Malaysia 5.54–6.17 s; analyst note 7.88–11.95 s; maximum 11.95 s.

## Work Card 08 Verification

- Status: Complete — verified on IBM LinuxONE.
- Docker image `trustpause:latest` built successfully.
- Image architecture: `s390x`.
- `.dockerignore` excludes datasets, models, Granite files, keys, databases, Git metadata, and notebook caches.
- Container `trustpause` ran successfully on isolated host port `8001`.
- API warm-up processed 4,214,445 historical transactions in 104 seconds.
- `/api/status` returned `stage: ready`.
- `/sender` returned HTTP 200.
- `/analyst` returned HTTP 200.
- Both views opened successfully through an SSH tunnel.
- Evidence screenshot: `screenshots/docker_s390x_evidence.png`.
- Granite model was copied from the Jupyter container to `/home/linux1/granite/`.
- `GRANITE_MODEL_PATH=/granite/granite-4.0-h-350m-base-be.f16.gguf` was set.
- The Granite model was readable inside the `trustpause` container.

## Work Card 06 Verification

- `python -m src.scorer --verify 2000` → `MATCH` on LinuxONE (live scores equal training scores)
- Warm-up: 4,214,445 historical transactions in ~100 s
- End-to-end latency during replay (features + XGBoost + reasons): p50 0.30 ms, p95 0.72 ms
- Endpoints checked through `/docs`: status, demo accounts, transfer, choice, replay start/stop, feed, queue, case, decision, metrics
- Fixes made while verifying: opt-in warm-state cache (out of memory), demo recipients previewed for the demo sender, sender transfers not recorded, story amount checked to warn

## Work Card 07 Verification

- Both pages load on LinuxONE through the SSH tunnel; restyled to the team's fintech reference (DM Sans, mint, black pills, yellow highlight)
- Sender view: scam message → transfer → security check → warning sheet with EN/BM and 997 hotline → cancel; safe recipients are sent
- Analyst view: replay, live stats, feed, hold queue, case detail, Release / Block
- Browser-tested locally at phone and desktop widths

## README

- Done: title, sourced Malaysian scam statistics (PDRM/CCID 2024 and Jan–Nov 2025, NSRC 2025), results, NNPA benchmark, limitations, architecture, privacy, demo, how to run (incl. Docker), dataset + CDLA-Sharing-1.0 licence, open-source list

## Next instruction for AI

Read `START_HERE.md`, `build-status.md`, `build-blueprint.md`, `architecture.md`, `design.md` and the current work card. Implement only the current work card. Run its verification steps, update this file, and stop for the team's check.
