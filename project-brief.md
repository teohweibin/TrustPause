# Project Brief

## Project Identity

- **Team:** Stats Power
- **Name:** TrustPause
- **Submission title:** `Stats Power_IBM Z Datathon 2026 Project — TrustPause`
- **Event:** IBM Z Datathon 2026, Oct 17–18 (24-hour build)
- **Theme:** Theme 1, Real-Time AI for Critical Decisions (Detect. Decide. Respond.)
- **Platform:** IBM LinuxONE Community Cloud (s390x, Ubuntu 24.04, Telum NNPA)

## One-Sentence Concept

Real-time scam interception that scores the receiving account at the moment a transfer is made, and gives the sender a clear, human warning before the money leaves. It runs entirely on IBM LinuxONE, with an on-platform IBM Granite LLM for analyst notes and a Telum NNPA benchmark.

## Problem

- In most scams the **victim authorises the transfer themselves**, so the sender-side transaction looks legitimate to bank rules.
- Once money reaches a mule account it moves on quickly, and **very little is ever recovered**.
- The signal is on the **receiving side**: accounts linked to earlier reported cases, accounts that are new to the sender, and accounts collecting money from many unrelated people (fan-in).
- Current systems trace funds *after* a victim reports. TrustPause acts **in the moment before the transfer completes**.

| Figure | Value | Source |
|---|---|---|
| Online crime losses, Jan–Nov 2025 | over RM2.7 billion, 67,735 cases | PDRM / Bukit Aman CCID, via The Vibes (8 Dec 2025) |
| Scam losses, 2024 | RM1.6 billion, 35,368 cases | Bukit Aman CCID, via Bernama (3 Mar 2025) |
| Largest category, Jan–Nov 2025 | Non-existent investment schemes, over RM1.37 billion | The Vibes (8 Dec 2025) |
| NSRC (997) in 2025 | 138,915 accounts frozen from 146,167 calls | Home Minister, via Asia News Network (4 Mar 2026) |
| Money saved / returned in 2025 | RM34.05 million saved; RM6.65 million returned (RM508,479 in 2024) | Home Minister, via Asia News Network (4 Mar 2026) |

Full links are in `README.md`. Figures from the team's earlier draft (RM2.77B, 87,209 mule accounts, < 2% recovery) could not be verified and are not used.

## Target User

- **Protected:** ordinary people sending money, especially the elderly, students and first-time digital banking users targeted by job, investment and impersonation scams.
- **Operator:** a bank or payment-network fraud analyst who reviews held transfers.

## User Goal

- **Sender:** before money leaves, see a calm, plain-language warning (English / Bahasa Malaysia) explaining *why* the recipient looks risky, with the 997 National Scam Response Centre hotline, and choose to stop.
- **Analyst:** see risky transfers as they happen, read an explained case note, and release or block a hold.

## Build Shape

Full-stack AI prototype: Python backend (FastAPI) with an XGBoost risk model, a PyTorch GRU benchmarked on the Telum NNPA, and a local IBM Granite LLM, plus two web views (a fictional mobile bank and an analyst console), running on LinuxONE and in Docker.

## Version-One Success (achieved)

- A time-ordered replay of the test days is scored live on LinuxONE: **p50 0.30 ms per transfer** for features + model + reasons.
- Each transfer gets one decision: Allow / Pause & warn / Hold.
- Sender warnings use reviewed EN/BM templates built from the model's reasons; Granite drafts analyst notes for held cases.
- The sender view shows the warning; the analyst view shows the live feed, hold queue and case detail.
- Measured results: test PR-AUC 0.254 (base rate 0.11%); hold band 52% precision / 23% recall; pause band catches 52% of laundering; NNPA 2.1× (batch 1) and 12.9× (batch 64) faster than CPU for the GRU.
- Remaining: a ≤ 3-minute video showing all of this running on LinuxONE.

## Now / Later / Never

### Now (built)
- Receiver-side features: velocity, fan-in/fan-out, pass-through ratio, account age, proximity to reported accounts
- XGBoost risk model with built-in `pred_contribs` explanations
- PyTorch GRU on Telum NNPA (benchmark; validation chose XGBoost alone for decisions)
- Three-band decision rules set by alert budget on validation
- EN/BM warning templates for senders; Granite analyst notes (no PII in prompts)
- FastAPI backend, sender view, analyst view, Docker container on LinuxONE
- Human release / block on holds, logged

### Later
- Retraining from analyst decisions
- Cross-bank data via a central operator
- Real banking-app integration
- Streaming platform (e.g. Kafka) and horizontal scaling
- An instruct-tuned Granite model for richer analyst notes

### Never
- Code copied from MulePulse, any earlier project or the IBM lab notebooks
- External AI APIs (OpenRouter, OpenAI, etc.): the LLM stays on LinuxONE
- Real personal data, real bank logos or branding
- Automatic blocking without human review for the highest-risk band
- Secrets, `.pem` keys or passwords in the repo

## Assumptions

- The IBM AML synthetic dataset (Kaggle, CDLA-Sharing-1.0) is a fair proxy for mule behaviour; we say so in the pitch.
- "Real time" is a replay of historical transactions on one server.
- The team shares one LinuxONE server (3 CPUs, 7.8 GB RAM); resources are limited.

## Proof Target

- GitHub repo + ≤ 3-minute video on Hack2Skill
- Screenshots: `lscpu` showing `nnpa`, `uname -m` → `s390x`, `docker ps`, model and NNPA charts, Granite privacy check, both views running
- List of open-source libraries and the dataset with links (in `README.md`)

## Team Notes

- The rules require all code to be written during the event (Oct 17–18). Libraries, the dataset and Granite weights are allowed and are listed in the README.
- The two IBM labs were run as learning demos, not as a submission requirement.
