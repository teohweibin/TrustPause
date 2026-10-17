# Build Blueprint

## Source Files

- `project-brief.md`: problem, users, scope
- `architecture.md`: stack, modules, data model, endpoints
- `design.md`: sender and analyst view rules
- `build-status.md`: current progress (always read first)
- `work-cards/`: one build step at a time

## Project Identity

**TrustPause**: real-time scam interception on IBM LinuxONE. Submission title: `[TeamName]_IBM Z Datathon 2026 Project — TrustPause`. Theme 1: Real-Time AI for Critical Decisions.

## Build Shape

Full-stack AI prototype: FastAPI backend + XGBoost + PyTorch (Telum NNPA) + Granite LLM + two HTML views, in Docker on LinuxONE.

## Version-One Promise

A judge watching the video sees: a stream of transactions scored live on LinuxONE; a risky transfer paused with a clear Granite-written warning on the sender's screen; an analyst reviewing an explained hold; and real numbers for accuracy and latency, including the Telum NNPA comparison.

## Scope Lock

### Now
Features, XGBoost, GRU on NNPA, ensemble, three decision bands, Granite warnings (EN/BM) + analyst notes, FastAPI, sender view, analyst view, Docker, metrics, video.

### Later
Retraining from analyst labels, cross-bank data, real bank integration, Kafka, scaling.

### Never
Copied code (MulePulse, any earlier project, IBM lab notebooks), external AI APIs, real personal data or bank branding, secrets in the repo.

## Architecture Summary

Replay or sender request → `features.py` (rolling account state) → `scorer.py` (XGBoost + GRU → ensemble → band) → `explain.py` (Granite, background, only for Pause/Hold) → SQLite → FastAPI → `sender.html` / `analyst.html`. Full detail in `architecture.md`.

## Data / State / Storage Rules

- Dataset: IBM AML `HI-Small_Trans.csv`, stored in `data/` (gitignored). Sample if memory is tight.
- **Time-based split only** (train on earliest ~60% of days, validate on next ~20%, test on last ~20%).
- Graph "known mule" anchors come from **training-period labels only**.
- Same `AccountState` code for training and serving.
- SQLite file `trustpause.db` gitignored.
- Granite never receives account IDs, names or raw transactions; only reason codes and aggregate numbers.

## Design Direction Summary

Calm, trustworthy, clearly-mock banking transfer screen + clean three-panel operations console. Teal accent, green/amber/red decision chips always with text labels and icons. Readable in a 1920×1080 screen recording. No real bank branding, no invented numbers. Full rules in `design.md`.

## Implementation Rules

- All code written during the event, from scratch. Read the IBM labs for *how* (e.g. loading Granite) but write our own code.
- Python 3 in the L1CC Jupyter image; prefer libraries already installed; any new `pip install` goes in `requirements.txt` and is tested on s390x first.
- Notebooks for exploration and training; reusable logic lives in `src/` and is imported by notebooks and the API.
- Everything lives in `~/shared/trustpause/` on the server (survives container restarts) and is pushed to GitHub often.
- Report honest numbers. If NNPA is not faster, say so.

## File and Folder Expectations

See `architecture.md` → File Expectations.

## Team Split

| Role | Owns | Work cards |
|---|---|---|
| **A. Data & features** | Dataset, time split, `features.py` | 01, 02 |
| **B. XGBoost** | Training, thresholds, reasons | 03 |
| **C. Sequence model + Telum** | GRU, NNPA, latency benchmark | 04 |
| **D. Granite** | Prompts EN/BM, privacy-safe input, fallback | 05 |
| **E. API, frontend, Docker** | FastAPI, replay, both views, container | 06, 07, 08 |
| **F. Pitch & evidence** | Screenshots, README, flowchart, video, submission | 09 (starts at H0) |

With 4 people: merge B+C and E+F.

## Work Card Plan

| Card | Title | Depends on | Target hours |
|---|---|---|---|
| 00 | LinuxONE setup gate | none | done / H0 |
| 01 | Repo, data and environment | 00 | H0–H2 |
| 02 | Feature pipeline | 01 | H2–H5 |
| 03 | XGBoost model + reasons | 02 | H4–H7 |
| 04 | Sequence model on Telum NNPA | 02 | H5–H12 |
| 05 | Granite explainer | 01 (only needs reason codes format) | H2–H8 |
| 06 | Real-time scorer, replay and API | 03, 05 (04 optional) | H7–H12 |
| 07 | Sender + analyst views | 06 | H11–H16 |
| 08 | Docker on LinuxONE | 06 | H14–H17 |
| 09 | Evidence, README, video, submission | all | H0 start, H17–H24 finish |

**MVP checkpoint (H10):** cards 01, 02, 03, 05 done and a notebook shows replay → XGBoost → decision → Granite text end to end.

**Feature freeze: H17.** Only bug fixes after this.

**If behind, cut in this order:** frontend polish → analyst view (keep sender view) → Docker → sequence model. Never cut: live scoring on LinuxONE, Granite explanation, the video.

## Timeline (24 hours)

| Block | Goal |
|---|---|
| H0–H2 | Repo, `.gitignore`, dataset on server, roles agreed. Labs done ✅ |
| H2–H6 | Features working; first XGBoost; Granite answers a test prompt |
| H6–H10 | **MVP** end to end in a notebook |
| H10–H14 | GRU on NNPA + ensemble; FastAPI endpoints |
| H14–H17 | Sender + analyst views, Docker; latency benchmark |
| H17–H19 | Feature freeze; fix bugs; collect metrics and screenshots |
| H19–H22 | Record and edit video (≤ 3 min), README, flowchart |
| H22–H24 | Submit on Hack2Skill early |

## Review Mirror

Use `prompts/review-mirror.md` after cards 06, 07 and before submission.

## Proof Ladder

1. **Minimum:** notebook on LinuxONE showing replay → decisions → Granite text + metrics, in the video
2. **Good:** + FastAPI backend in Docker on LinuxONE + sender view
3. **Strong:** + analyst view + NNPA latency comparison + clean README + flowchart

## Risks and Limitations

| Risk | Mitigation |
|---|---|
| Scope too large for 24 h | MVP first; cut order above |
| Granite slow on CPU | Never on decision path; only Pause/Hold; template fallback; short outputs |
| `torch_nnpa` unverified / not faster for tiny model | Test early (card 04); report measured numbers; batch; fall back to CPU |
| BM quality from small Granite | Test early; fixed BM template if poor |
| Synthetic AML data ≠ real scam data | Say so clearly in pitch |
| Shared server memory/CPU | `free -h`, sample data, no parallel training |
| Real time is simulated | Present as prototype; explain scaling on IBM Z |
| False positives on legitimate fan-in accounts | Middle band warns only; holds need human approval; mention in pitch |
| Needs cross-bank data in real life | Future work |
| Fraud is a common idea | Lead with: payment-time, victim-facing, hybrid AI on Telum, privacy-safe LLM |

## 60-Second Explanation Template

"In most scams the victim sends the money themselves, so banks see a normal transfer, and less than 2% is ever recovered. TrustPause looks at the *receiving* account instead: is it suddenly collecting money from many strangers and passing it straight on? At the moment someone presses Send, two models score the recipient on IBM LinuxONE: XGBoost on behaviour features, and a sequence model on the Telum AI accelerator, in [X] milliseconds. Risky transfers are paused with a clear warning in English or Malay written by IBM Granite running on the same machine, so no customer data leaves the platform. The highest-risk ones go to a human analyst with an explained case note. On IBM's synthetic AML data we reach [PR-AUC] and catch [Y]% of mule transfers at [Z]% precision."

## Guardrails for the Coding Agent

- Read `build-status.md`, `build-blueprint.md`, `architecture.md`, `design.md` and the current work card before editing.
- Implement only the current work card; do not jump ahead.
- Stop after verification; update `build-status.md` after each card.
- Use only the stack in `architecture.md`; no external AI APIs; no new heavy dependencies without testing on s390x.
- Never put secrets, keys, `.pem` files or real personal data in code or the repo.
- Never copy code from earlier projects or the IBM lab notebooks.
- Do not invent metrics, claims, logos or testimonials; every number shown must be computed.
- Keep the decision path free of Granite calls.
