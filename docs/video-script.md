# TrustPause: 3-Minute Video Script

**Title card:** Stats Power_IBM Z Datathon 2026 Project — TrustPause
**Hard limit: 3:00.** Narration below is ~420 words (about 2:50 at a calm pace). Rehearse with a timer.

The rules ask the video to cover: the problem, data supporting it, the solution, and **how it uses IBM Z** (tech stack, the LinuxONE instance and the model running). Every section below maps to one of those.

---

## Shot list and narration

| Time | On screen | Narration |
|---|---|---|
| **0:00–0:20** **Hook** | Sender view (phone frame) on the home screen. The **HR Recruiter** message slides in: *"pay the $500 registration fee today…"* | "This is Mei. She just got a message: she's landed a job, and only needs to pay a five-hundred-dollar registration fee. It feels real. She opens her banking app to pay. This is exactly how most scams in Malaysia work: the victim sends the money herself." |
| **0:20–0:45** **Problem + data** | Slide: the README statistics table (or a clean slide with 3 numbers + sources) | "From January to November 2025, Malaysians lost over 2.7 billion ringgit across 67,735 online crime cases, already about 70% more than all of 2024. The National Scam Response Centre froze nearly 139,000 accounts last year, yet only about 34 million ringgit was saved. Once the money leaves, it's almost never coming back." |
| **0:45–1:05** **Solution** | Architecture flowchart (teammate's version) | "TrustPause is Team Stats Power's answer. Instead of tracing money after the report, it checks the **receiving** account at the moment someone presses Send, on IBM LinuxONE. Every transfer gets one of three decisions: allow, pause and warn, or hold for a human analyst." |
| **1:05–1:45** **Live demo: sender** | Tap the message → amount $500 → purpose *Job deposit* → **Confirm** → *Security check on IBM LinuxONE* → warning sheet. Tap **BM**, point at the reasons and the **997** hotline. Tap **Cancel transfer** → "Transfer cancelled" with the *Checked on IBM LinuxONE in N ms* pill. Then a quick $200 to **Utility company** → *Transfer sent* | "When Mei confirms, TrustPause scores the transfer in about a millisecond. The receiving account is linked to an earlier reported case, and it's a new recipient for her. So instead of a silent block, Mei gets a calm warning in English or Bahasa Malaysia, with the reasons and the 997 scam hotline. She cancels. No money left her account. Normal payments, like her utility bill, go straight through." |
| **1:45–2:15** **Live demo: analyst** | Analyst console. Press **Start replay** (500 tx/s). Point at the yellow latency tile, the counters and *Laundering caught*. Open a held case: scores, reasons, analyst note (Granite tag if present). Click **Block** | "Behind the scenes, we replay real-time traffic from IBM's anti-money-laundering dataset: hundreds of transfers per second, each scored in well under a millisecond. The riskiest go to an analyst with the reasons the model used, and a case note drafted by IBM Granite running on the same machine. A human always makes the final call." |
| **2:15–2:40** **Why IBM Z** | Terminal on the server: `uname -m` → **s390x**, `lscpu \| grep -io nnpa` → **nnpa**, `docker ps` → **trustpause**. Then the NNPA latency chart | "Everything runs on IBM LinuxONE: the s390x server, the containerised app, and the model. We also ran a PyTorch model on the Telum on-chip AI accelerator: up to 13 times faster than the CPU. And because Granite runs on LinuxONE, no customer data is ever sent to an outside AI service." |
| **2:40–3:00** **Results + close** | Slide: test results (PR-AUC 0.254 ≈ 230× the base rate; holds 1 in 2,000 transfers, half are laundering; warns < 1 in 100 and catches over half). Then the TrustPause title card | "On days the model had never seen, TrustPause held about one in two thousand transfers, and half of those were laundering. It warned on fewer than one in a hundred while catching over half of all laundering. TrustPause: a pause at the right moment, so people keep their money. Thank you from Team Stats Power." |

---

## Numbers you may say (all measured or sourced)

| Claim | Value | Where it comes from |
|---|---|---|
| Losses Jan–Nov 2025 | over RM2.7 billion, 67,735 cases | PDRM / CCID via The Vibes (README) |
| Losses 2024 | RM1.6 billion | Bukit Aman CCID via Bernama (README) |
| NSRC 2025 | 138,915 accounts frozen; RM34.05 million saved | Home Minister via Asia News Network (README) |
| Live scoring speed | p50 0.30 ms (features + model + reasons) | `build-status.md` |
| Test PR-AUC | 0.254 (base rate 0.11%, ~230×) | `models/metrics.json` |
| Hold band (test) | 0.049% of transfers, 52% precision, 23% recall | `models/metrics.json` |
| Pause band (test) | 0.70% of transfers, catches 52% of laundering | `models/metrics.json` |
| NNPA vs CPU (GRU) | 2.1× (batch 1), 12.9× (batch 64) | `screenshots/sequence_latency.png` |

**Do not say:** "real bank data" (it's IBM's synthetic dataset), "blocks scams automatically" (the top band goes to a human), "Granite writes the customer warning" (it writes analyst notes; warnings are reviewed templates), or any statistic not in the table above.

---

## Before recording

1. **Restart the API** on the server so counters start at zero; wait for `curl -s localhost:8000/api/status` → `"stage":"ready"` and all six `demo_check` entries `"passed": true`.
2. **Record the sender story first**, then start replay in the analyst tab (replay moves the data clock forward).
3. Screen: **1920×1080**, browser zoom 100%, bookmarks bar hidden, notifications off. Close other tabs.
4. **Hide the server IP** and anything from the `.pem` path in terminal shots (crop or blur).
5. Terminal shot commands (run on the server, in one clean terminal):
   ```bash
   uname -m
   lscpu | grep -io nnpa
   docker ps
   ```
6. If a held case shows **"drafted by IBM Granite"**, use it; otherwise the template note is fine; don't wait for Granite on camera (it takes ~15 s).
7. Analyst replay speed **500 tx/s**; let it run ~30 s before opening a held case. The *Laundering caught* tile needs a few minutes of replay to mean anything (after 30 s it showed 1 of 4); if it's still small, don't point at it and quote the test results instead.
9. Reference stills from the live demo are in `screenshots/demo_*.png`.
8. Record voice separately if needed and keep total length **under 3:00**, title card included.
