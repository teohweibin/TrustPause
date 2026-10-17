# Project Brief

## Project Identity

- **Name:** TrustPause (working name, rename freely)
- **Submission title:** `[TeamName]_IBM Z Datathon 2026 Project — TrustPause` (the rules require the team name in the title)
- **Event:** IBM Z Datathon 2026, Oct 17–18 (24-hour build)
- **Theme:** Theme 1, Real-Time AI for Critical Decisions (Detect. Decide. Respond.)
- **Platform:** IBM LinuxONE Community Cloud (s390x, Ubuntu 24.04, Telum NNPA)

## One-Sentence Concept

Real-time scam interception that scores the receiving account at the moment a transfer is made, and gives the sender a clear, human warning before the money leaves. It runs entirely on IBM LinuxONE, with Telum AI acceleration and an on-platform Granite LLM.

## Problem

- In most Malaysian scams the **victim authorises the transfer themselves**, so the sender-side transaction looks legitimate to bank rules.
- Once money reaches a mule account it moves on within minutes, and **recovery is below 2%**.
- The signal is on the **receiving side**: accounts that suddenly collect money from many unrelated people (fan-in) and pass it straight out again (pass-through).
- Current systems trace funds *after* a victim reports. TrustPause acts **in the seconds before the transfer completes**.

| Figure (verify and cite source before using) | Value |
|---|---|
| Fraud losses 2023 → 2025 | RM1.28B → RM1.57B → RM2.77B |
| Active mule accounts 2025 | 87,209 (+70% YoY) |
| Recovery rate 2025 | < 2% |

## Target User

- **Protected:** ordinary people sending money, especially the elderly, students and first-time digital banking users targeted by job, investment and impersonation scams.
- **Operator:** a bank or payment-network fraud analyst who reviews held transfers.

## User Goal

- **Sender:** before money leaves, see a calm, plain-language warning (English / Bahasa Malaysia) explaining *why* the recipient looks risky, and choose to stop.
- **Analyst:** see risky transfers as they happen, read an explained case note, and approve or reject a hold.

## Build Shape

Full-stack AI prototype: Python backend (FastAPI) with two ML models and a local LLM, plus two small HTML views, running in Docker on LinuxONE.

## Version-One Success

- A time-ordered stream of transactions is scored live on LinuxONE.
- Each transfer gets one of three decisions: Allow / Pause & warn / Hold.
- Granite produces a sender warning and an analyst note for paused/held transfers.
- The sender view shows the warning pop-up; the analyst view shows the live feed and hold queue.
- Measured results: PR-AUC, precision/recall at chosen thresholds, scoring latency (p50/p95), CPU vs NNPA comparison.
- A ≤ 3-minute video showing all of this running on LinuxONE.

## Now / Later / Never

### Now
- Receiver-side features: velocity, fan-in/fan-out, pass-through ratio, account age, graph proximity
- XGBoost risk model with built-in `pred_contribs` explanations
- PyTorch sequence model on Telum NNPA (if `torch_nnpa` works)
- Ensemble + three-band decision rules
- Granite warnings (EN + BM) and analyst notes from top reasons only (no PII)
- FastAPI backend, sender view, analyst view, Docker container on LinuxONE
- Human approve/reject on holds, logged

### Later
- Retraining from analyst decisions
- Cross-bank data via a central operator
- Real banking-app integration
- Streaming platform (e.g. Kafka) and horizontal scaling

### Never
- Code copied from MulePulse, any earlier project or the IBM lab notebooks
- External AI APIs (OpenRouter, OpenAI, etc.): the LLM stays on LinuxONE
- Real personal data, real bank logos or branding
- Automatic blocking without human review for the highest-risk band
- Secrets, `.pem` keys or passwords in the repo

## Assumptions

- The IBM AML synthetic dataset (Kaggle) is a fair proxy for mule behaviour; we say so in the pitch.
- "Real time" is a replay of historical transactions on one server.
- The Granite model file from the Loan Approval lab can be reused (model weights, not code).
- The team shares one LinuxONE server; resources are limited.

## Proof Target

- GitHub repo + ≤ 3-minute video on Hack2Skill
- Screenshots: both IBM labs completed, `lscpu` showing `nnpa`, `docker ps`, notebooks with metrics, both views running
- List of open-source libraries and dataset with links

## Team Notes

- The rules require all code to be written during the event (Oct 17–18). Libraries, the dataset and Granite weights are allowed and must be listed.
- If unsure whether the topic is too close to the team's earlier NexHack project, ask organisers on Discord.
