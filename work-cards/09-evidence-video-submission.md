# Work Card 09: Evidence, README, Video and Submission

## Goal

A complete Hack2Skill submission: ≤ 3-minute video, GitHub repo with README, screenshots, and the required links.

## Owner

F (Pitch & evidence): **starts at H0**, collecting screenshots as other cards finish.

## Files likely touched

`README.md`, `screenshots/`, `docs/flowchart.png` (optional)

## Instructions

### Screenshots to collect (name them clearly)
- `labs/`: both IBM labs completed
- `lscpu-nnpa.png`, `uname-s390x.png`, `docker-ps.png`
- XGBoost PR curve + metrics; NNPA latency chart
- Granite prompt (showing no IDs) + outputs
- Sender pause pop-up (EN and BM); analyst view with live feed and a case

### README sections
Title (`[TeamName]_IBM Z Datathon 2026 Project — TrustPause`) · problem · solution · architecture diagram · why IBM LinuxONE · results (real numbers) · how to run on L1CC · dataset + licence link · open-source libraries with links (pandas, networkx, scikit-learn, XGBoost, PyTorch, torch_nnpa, llama.cpp / llama-cpp-python, IBM Granite, FastAPI, Uvicorn) · team members and roles · limitations.

### Video (max 3:00)

| Time | Content |
|---|---|
| 0:00–0:25 | Problem: victim authorises the transfer; losses; < 2% recovered (cited) |
| 0:25–0:45 | Who we protect; the gap: action happens *after* the report |
| 0:45–1:15 | Solution + architecture flowchart; hybrid AI; human in the loop |
| 1:15–2:15 | Live demo on LinuxONE: terminal with server + `docker ps`; sender view pause pop-up (EN/BM); analyst view live stream, approves a hold |
| 2:15–2:40 | Why IBM Z: Telum NNPA latency numbers, data + LLM never leave the server, containerised |
| 2:40–3:00 | Results (PR-AUC, latency), team roles, impact |

Record at 1920×1080; rehearse with a timer; **must be ≤ 3:00**.

## What not to do

- Do not show the `.pem` file, tokens or the server IP in the video if avoidable.
- Do not state numbers that are not in our notebooks.
- Do not leave submission to the last hour.

## Done when

Submitted on https://hack2skill.com/event/datathon-2026 with video, repo link, title and library links.

## Verification steps (submission checklist)

- [ ] Title contains the team name
- [ ] Video ≤ 3:00, shows LinuxONE instance and the model running
- [ ] GitHub repo public (or accessible), no `.pem`, no secrets, no data files
- [ ] Open-source libraries and dataset listed with links
- [ ] Lab screenshots included
- [ ] Optional: flowchart, prototype
- [ ] Statistics in the video have sources
- [ ] All code written during the event

## Stop condition

At H22, submit whatever is ready, then improve and resubmit if the platform allows.

## Status

Not started
