# Work Card 07: Sender and Analyst Views

## Goal

Two plain HTML/CSS/JS pages that follow `design.md`: the sender's mock transfer screen with the pause pop-up, and the analyst console.

## Owner

E (Frontend)

## Inputs

Endpoints from card 06; `design.md`

## Files likely touched

`web/sender.html`, `web/analyst.html`, `web/style.css`, `web/app.js` (optional)

## Instructions for the coding agent

1. Shared `style.css` with the colour tokens, type sizes and components from `design.md`.
2. **Sender:** recipient dropdown from `/api/demo-accounts`, amount input, Send → `/api/transfer` → Allow card / Pause modal (EN/BM toggle, top 3 reasons, "Cancel transfer" primary + focused, "I understand the risk, continue" secondary) / Hold card. Footer shows real `latency_ms`. Mark the page "mock".
3. If the Granite warning isn't ready yet, show the template text and poll `/api/case/{id}` to swap it in.
4. **Analyst:** top bar stats from `/api/metrics` (poll 1 s); Start/Stop replay; feed from `/api/feed?since=` (newest first, max 50 rows); hold queue from `/api/queue`; case detail from `/api/case/{id}` with Approve / Reject → `/api/case/{id}/decision`.
5. Empty states as in `design.md`.

## What not to do

- No frameworks, no build step, no external CDNs (the page must work offline on the server).
- No real bank names or logos; no invented numbers.

## Done when

Both pages work against the live backend and pass the design check.

## Verification steps

- Design check: colours, chips with labels + icons, modal focus, 44 px targets, empty states, and phone width follow `design.md`.
- Sender view at 375 px width.
- Analyst view readable in a 1920×1080 screen recording.

## Test before continuing

- Sender: send to a low-risk and a high-risk recipient; see Allow and Pause; toggle EN/BM; press Esc to close the modal.
- Analyst: start replay; feed scrolls; open a held case; Approve it; it leaves the queue.

## Stop condition

If time is short, ship the sender view first and make the analyst view a simple table.

## Status

Not started
