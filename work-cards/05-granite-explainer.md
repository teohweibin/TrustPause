# Work Card 05: Granite Explainer

## Goal

`explain.py` turns reason codes into a short sender warning (English + Bahasa Malaysia) and an analyst note using IBM Granite running locally, with no personal data in the prompt.

## Owner

D (Granite)

## Inputs

- Granite loading approach and model file location from `Loan_Approval_Demo.ipynb` (read it; write our own code)
- Reason code format from card 03 (can start with mocked reasons)

## Files likely touched

`src/explain.py`, `notebooks/05_granite.ipynb`

## Instructions for the coding agent

1. Load Granite with `llama_cpp_python` once at startup; model path from env var `GRANITE_MODEL_PATH`.
2. Input: `{decision, score, reasons: [{code, sentence}], amount_band}`, **no account IDs or names**.
3. Three short outputs (max ~60 words each, low temperature):
   - `warning_en`: calm, non-blaming, tells the sender what to check and that they can cancel
   - `warning_bm`: same in Bahasa Malaysia
   - `analyst_note`: 3 bullet points: pattern, evidence, suggested action
4. Template fallback for each output if Granite is slow (> configurable timeout) or fails.
5. Measure generation time per output; record in `build-status.md`.
6. Log one full prompt and confirm it has no IDs (screenshot for the privacy claim).

## What not to do

- No external LLM APIs.
- Do not let Granite decide the risk; it only explains the models' decision.
- Do not put Granite on the scoring path.

## Done when

Given mocked or real reasons, all three outputs are produced, readable, and within the time noted.

## Verification steps

- 5 different reason combinations → 5 sensible outputs.
- BM output reviewed by a Malay speaker on the team; if poor, use a fixed BM template.
- Prompt contains no account IDs.

## Test before continuing

- Run `05_granite.ipynb`; read the outputs aloud: would an elderly sender understand them?

## Stop condition

If generation takes > 15 s, shorten outputs / reduce context, or generate only the analyst note and use templates for warnings.

## Status

Not started
