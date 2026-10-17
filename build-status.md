# Build Status

## Project

- Name: TrustPause (working name)
- Submission title: `[TeamName]_IBM Z Datathon 2026 Project — TrustPause`
- Theme: Theme 1, Real-Time AI for Critical Decisions
- Build shape: Full-stack AI prototype on IBM LinuxONE (FastAPI + XGBoost + PyTorch/NNPA + Granite + 2 HTML views, Docker)
- Current stage: Building
- Current work card: `work-cards/02-feature-pipeline.md`; finish open items in `work-cards/00-setup-gate.md` alongside

## Completed work cards

- [ ] 00 LinuxONE setup gate (mostly done)
- [x] 01 Repo, data and environment
- [ ] 02 Feature pipeline
- [ ] 03 XGBoost model + reasons
- [ ] 04 Sequence model on Telum NNPA
- [ ] 05 Granite explainer
- [ ] 06 Real-time scorer, replay and API
- [ ] 07 Sender and analyst views
- [ ] 08 Docker on LinuxONE
- [ ] 09 Evidence, README, video and submission

## In progress

- 00 Setup gate: remaining items (Discord lab confirmation, `.pem` sharing, roles)

## Blockers

- None recorded yet

## Decisions made

- Theme: Theme 1 (Real-Time AI for Critical Decisions)
- Stack: Python, pandas, networkx, XGBoost, PyTorch + torch_nnpa, llama.cpp + Granite, FastAPI, SQLite, plain HTML/CSS/JS, Docker
- Dataset: IBM AML synthetic (`HI-Small_Trans.csv`), licence to verify
- Split: time-based by calendar day after dropping sparse days (< 1% of busiest day). HI-Small: drop Sep 11–18 (only ~1,100 rows, ~60% laundering); train Sep 1–6, val Sep 7–8, test Sep 9–10
- Explanations: XGBoost `pred_contribs` (no `shap` package)
- LLM: Granite on LinuxONE only; no external AI APIs; no IDs in prompts
- Storage: SQLite
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

## Measured results (fill in as you go)

- XGBoost test PR-AUC:
- Ensemble test PR-AUC:
- Hold band precision / recall:
- Pause band precision / recall:
- Scoring latency p50 / p95:
- GRU latency CPU vs NNPA (batch 1 / 64):
- Granite time per output:

## Next instruction for AI

Read `START_HERE.md`, `build-status.md`, `build-blueprint.md`, `architecture.md`, `design.md` and the current work card. Implement only the current work card. Run its verification steps, update this file, and stop for the team's check.
