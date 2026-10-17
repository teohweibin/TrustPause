# START HERE: TrustPause (IBM Z Datathon 2026)

Real-time scam interception on IBM LinuxONE. This folder is the team's planning pack and becomes the root of the GitHub repo.

## The files are the source of truth

Chat history is not. If you switch AI tools, teammates or laptops, read these files and continue from `build-status.md`.

| File | What it holds |
|---|---|
| `project-brief.md` | Problem, users, scope (Now / Later / Never) |
| `architecture.md` | Stack, modules, data model, API endpoints, latency rules |
| `design.md` | Sender view and analyst view design rules |
| `build-blueprint.md` | Everything combined: team split, work card plan, timeline, risks, pitch |
| `build-status.md` | Current progress, decisions, measured results. **Read first, update after every card** |
| `work-cards/00–09` | One build step each, with owner, instructions, tests and stop condition |
| `prompts/build-runner.md` | Prompt to give an AI coding assistant for one work card |
| `prompts/review-mirror.md` | Prompt for a quick review against the plan |

## Where the code runs

All code runs on the **LinuxONE server** (s390x), not on laptops:

- Repo cloned at `~/shared/trustpause/` (the `shared` folder survives container restarts)
- Edit and run in **Jupyter** (`http://localhost:38888` through the SSH tunnel) or in the Jupyter terminal
- The app runs on port 8000; open it through a second tunnel:
  ```powershell
  ssh -i "path\to\ibmzdatathon.pem" -L 38888:localhost:38888 -L 8000:localhost:8000 linux1@<SERVER_IP>
  ```
- Push to GitHub often from the Jupyter terminal (use a GitHub personal access token, not your password)

## Work order

```
00 Setup gate ─► 01 Repo + data ─► 02 Features ─┬─► 03 XGBoost ──┐
                       │                         └─► 04 GRU/NNPA ─┤ (optional for MVP)
                       └──────────────► 05 Granite ───────────────┤
                                                                  ▼
                                   06 Scorer + API ─► 07 Views ─► 08 Docker
09 Evidence + video: starts at H0, finishes last
```

Cards 03, 04 and 05 can run in parallel by different people.

## Using an AI coding assistant

Paste `prompts/build-runner.md` and name the work card. The assistant implements only that card, runs its checks, updates `build-status.md` and stops.

## Rules that can get us disqualified

- All code must be written during the event (Oct 17–18). Nothing copied from earlier projects or the IBM lab notebooks.
- Video max 3 minutes; title includes the team name; GitHub link required.
- List all open-source libraries and the dataset with links.

## Never commit

`*.pem`, `data/`, `*.db`, `*.gguf`, tokens or passwords. `.gitignore` already covers these.
