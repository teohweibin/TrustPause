# Build Status

## Project

- Name: TrustPause (working name)
- Submission title: `[TeamName]_IBM Z Datathon 2026 Project — TrustPause`
- Theme: Theme 1, Real-Time AI for Critical Decisions
- Build shape: Full-stack AI prototype on IBM LinuxONE (FastAPI + XGBoost + PyTorch/NNPA + Granite + 2 HTML views, Docker)
- Current stage: Ready to build
- Current work card: `work-cards/00-setup-gate.md` (finish unticked items), then `work-cards/01-repo-data-environment.md`

## Completed work cards

- [ ] 00 LinuxONE setup gate (mostly done)
- [ ] 01 Repo, data and environment
- [ ] 02 Feature pipeline
- [ ] 03 XGBoost model + reasons
- [ ] 04 Sequence model on Telum NNPA
- [ ] 05 Granite explainer
- [ ] 06 Real-time scorer, replay and API
- [ ] 07 Sender and analyst views
- [ ] 08 Docker on LinuxONE
- [ ] 09 Evidence, README, video and submission

## In progress

- 00 Setup gate: remaining items

## Blockers

- None recorded yet

## Decisions made

- Theme: Theme 1 (Real-Time AI for Critical Decisions)
- Stack: Python, pandas, networkx, XGBoost, PyTorch + torch_nnpa, llama.cpp + Granite, FastAPI, SQLite, plain HTML/CSS/JS, Docker
- Dataset: IBM AML synthetic (`HI-Small_Trans.csv`), licence to verify
- Split: time-based train/val/test
- Explanations: XGBoost `pred_contribs` (no `shap` package)
- LLM: Granite on LinuxONE only; no external AI APIs; no IDs in prompts
- Storage: SQLite
- Frontend: sender view + analyst view, served by FastAPI
- Access: SSH tunnels (Jupyter 38888, app 8000); no public ports
- Deployment: Docker on LinuxONE; judges see it in the video

## Last verified state

- Server: ACTIVE, SSH works (user `linux1`)
- Docker: installed and working
- Jupyter: running in container `notebook`, reached via SSH tunnel
- IBM labs: both run (screenshots to save)
- Telum NNPA: present (`lscpu` → `nnpa`)
- Libraries: xgboost 3.4.1, torch 2.11.0+cpu, torch_nnpa 1.5.0, tensorflow 2.18.1, llama_cpp_python 0.3.36, networkx 3.7, pandas 3.0.6, scikit-learn 1.9.0
- FastAPI / Uvicorn: not checked
- Server memory / CPU (`free -h`, `nproc`): not checked
- `torch_nnpa` usage: not tested
- Granite generation time: not measured
- Dataset on server: not yet
- GitHub repo: not created yet

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
