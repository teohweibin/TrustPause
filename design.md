# Design Direction

## Design Inspiration

Own direction: **"calm safety layer"**: a modern mobile banking transfer screen (sender view) and a clean operations console (analyst view). Generic patterns only; no specific bank or product is copied.

Both views will be **recorded for a 3-minute video at 1920×1080**, so readability on a screen recording matters more than fine detail.

## What We Borrow

- **Layout:** banking-app transfer flow (recipient → amount → Send) for the sender; three-panel console (feed, queue, case detail) for the analyst
- **Spacing:** generous; 8 px grid; 24 px card padding
- **Colour mood:** calm, trustworthy, neutral with one accent
- **Typography feel:** clear and official, not playful
- **Card/button style:** rounded corners (12 px), soft shadow, solid primary button
- **Mobile feel:** the sender view is a phone-sized frame (max 420 px wide) centred on the page

## What We Do Not Copy

- No real bank names, logos, colours or app screenshots (e.g. no Maybank, CIMB, PayNet, DuitNow branding)
- No real people's names or account numbers; demo accounts use labels like "Recipient A — Online seller"
- No invented statistics in the UI; all numbers come from our own model and data
- No IBM logo misuse; "Running on IBM LinuxONE" as plain text is fine

## Visual Mood

Calm, trustworthy, clear, protective.

## Layout Rules

**Sender view (`/sender`):**
- Phone frame centred; header "TrustPause Demo Bank (mock)"
- Recipient dropdown, amount input, one primary "Send" button
- Result states:
  - Allow → green success card "Transfer sent"
  - Pause → modal pop-up: amber header "Wait — check this recipient", 2–3 sentence Granite warning, language toggle EN / BM, top 3 reasons as bullet points, **primary button "Cancel transfer"**, secondary text button "I understand the risk, continue"
  - Hold → blue info card "This transfer is being reviewed for your protection"
- Small footer: "Scored on IBM LinuxONE in 12 ms" (real measured latency)

**Analyst view (`/analyst`):**
- Top bar: title, Start/Stop replay button, live stats (txn/sec, latency p50/p95, Allow / Pause / Hold counts, "Telum NNPA: on/off")
- Left (40%): live feed table: time, amount, score, decision chip; newest on top; max 50 rows
- Middle (25%): hold queue: cards with score and first reason
- Right (35%): case detail: score breakdown (XGBoost, GRU, ensemble), top reasons, Granite analyst note, Approve / Reject buttons
- Empty states: "Press Start replay to begin" / "No transfers waiting for review"

## Colour / Contrast Rules

| Token | Use | Value |
|---|---|---|
| `--bg` | page background | `#F5F7FA` |
| `--surface` | cards | `#FFFFFF` |
| `--text` | body text | `#1A2230` |
| `--muted` | secondary text | `#5B6675` |
| `--accent` | primary buttons, links | `#0F6E78` (teal) |
| `--allow` | Allow chip | `#1E7B45` |
| `--pause` | Pause chip / warning header | `#B25E00` |
| `--hold` | Hold chip | `#B3261E` |

- Text contrast at least 4.5:1 on its background
- **Never use colour alone:** every chip also has a text label (ALLOW / PAUSE / HOLD) and an icon character (✓ / ! / ⏸)

## Typography Feel

- System font stack: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (no external fonts; works offline on the server)
- Body 16 px minimum; feed table 15 px; stats numbers 28 px bold; modal heading 22 px
- Numbers use `font-variant-numeric: tabular-nums` so the live feed doesn't jitter

## Component Style

- **Buttons:** primary solid `--accent`, white text, 44 px tall; secondary is a text button; destructive (Reject) outlined `--hold`
- **Cards:** white, 12 px radius, `0 1px 3px rgba(0,0,0,.08)` shadow
- **Inputs:** 44 px tall, 1 px `#C9D1DB` border, visible label above, focus ring 2 px `--accent`
- **Status chips:** pill shape, tinted background (10% of chip colour), bold uppercase label + icon
- **Score:** shown as a number 0.00–1.00 plus a thin horizontal bar

## Mobile Rules

- Sender view must work at 375 px width (it is phone-first by design)
- Analyst view is desktop-only (≥ 1280 px); below that, panels stack vertically: stats → queue → case → feed

## Accessibility Basics

- Readable contrast (see above)
- Visible focus states on all buttons and inputs
- Every input has a `<label>`
- Modal traps focus and closes with Esc; "Cancel transfer" is focused by default
- Tap targets ≥ 44 px
- Warning text available in English and Bahasa Malaysia

## Anti-Slop Rules

- No fake logos, fake testimonials or real brands
- No fake statistics: the UI only shows numbers computed by our system
- No lorem ipsum
- No decorative gradient blobs or stock illustrations
- One clear primary action per screen (Send; Cancel transfer; Approve/Reject in case detail)
- The word "mock" or "demo" visible on the sender view so nobody mistakes it for a real bank

## Design Verification Checklist

- [ ] Sender view reads as a calm, believable (but clearly mock) transfer screen
- [ ] The pause pop-up is the visual focus and "Cancel transfer" is the obvious choice
- [ ] Analyst view readable in a 1920×1080 screen recording without zooming
- [ ] Decision chips readable without colour (labels + icons)
- [ ] Sender view works at 375 px width
- [ ] No real bank branding, no invented numbers
