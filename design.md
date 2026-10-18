# Design Direction

## Design Inspiration

Team reference: a modern fintech mobile app concept (soft mint background, white rounded cards, black pill controls, one bright yellow highlight card, rounded geometric sans). We take its **style, colour and type only**; layout and features are our own. No specific bank or product is copied.

Both views will be **recorded for a 3-minute video**, so readability on a screen recording matters more than fine detail.

## What We Borrow

- **Style:** soft mint gradient background; white cards with large radius (20–28 px) and soft shadows
- **Controls:** near-black pills and buttons (account pill, primary buttons, replay button)
- **Highlight:** one yellow card per screen for the headline number (sender: amount; analyst: LinuxONE latency)
- **Typography:** DM Sans, big bold numbers
- **Lists:** rounded white rows with a round avatar (recipients, transfer history, feed rows)

## What We Do Not Copy

- No real bank names, logos, colours or app screenshots (e.g. no Maybank, CIMB, PayNet, DuitNow branding)
- No real people's names or account numbers; demo accounts use labels like "Recipient A — Online seller"
- No invented statistics in the UI; all numbers come from our own model and data
- No IBM logo misuse; "Running on IBM LinuxONE" as plain text is fine

## Visual Mood

Calm, modern, trustworthy, protective.

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
| `--bg-1` → `--bg-2` | page background gradient | `#DCEFE4` → `#EEF6EA` |
| `--surface` / `--surface-2` | cards / inner fills | `#FFFFFF` / `#F4F7F5` |
| `--text` / `--ink` | text / black pills and buttons | `#121417` |
| `--muted` | secondary text | `#7C838C` |
| `--highlight` | the one yellow card | `#F2EF7C` |
| `--accent` | focus rings | `#1E8C6E` |
| `--allow` | Allow chip | `#1F9D55` |
| `--pause` | Pause chip / warning icon | `#B86E00` |
| `--hold` | Hold chip, money out | `#B42318` |

- Text contrast at least 4.5:1 on its background
- **Never use colour alone:** every chip also has a text label (ALLOW / PAUSE / HOLD) and an icon character (✓ / ! / ⏸)

## Typography Feel

- **DM Sans** from Google Fonts, falling back to `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (pages still work if the font can't load)
- Body 16 px; amount 48 px bold; stat values 30 px (yellow tile 38 px); headings semibold with slight negative letter-spacing
- Numbers use `font-variant-numeric: tabular-nums` so the live feed doesn't jitter

## Component Style

- **Buttons:** primary near-black, white text, 48–56 px tall, 14–18 px radius (pill on the analyst bar); secondary is underlined text; Block is white with red text
- **Cards:** white, 20 px radius (28 px for panels and the yellow card), soft shadow `0 8px 24px rgba(28,58,46,.08)`
- **Recipient rows:** radio inputs styled as white rounded rows with avatar initial; selected row gets a black border and black check
- **Pills:** black for the demo account and "Running live on IBM LinuxONE"; white for the mock-bank badge and latency
- **Status chips:** pill shape, tinted background, bold uppercase label + icon
- **Score:** number plus thin black bar

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
