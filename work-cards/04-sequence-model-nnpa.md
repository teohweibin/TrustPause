# Work Card 04: Sequence Model on Telum NNPA

## Goal

A small PyTorch GRU that scores the receiver's last 10 transactions, run on the Telum NNPA, with an honest CPU vs NNPA latency comparison.

## Owner

C (Sequence model + Telum)

## Inputs

Receiver sequences from card 02.

## Files likely touched

`src/train_seq.py`, `notebooks/04_sequence_nnpa.ipynb`, `models/seq.pt`

## Instructions for the coding agent

1. **First hour: prove `torch_nnpa` works.** Find how to move a model/tensors to NNPA (check docs, the lab notebooks, or ask `#ibm-z-sme-helpdesk`). Run a tiny GRU forward pass on NNPA and on CPU. Record what works in `build-status.md`. Do not guess the API.
2. Model: input = last 10 transactions × ~6 features (amount scaled, time gap, direction in/out, counterparty novelty, payment format); GRU(hidden 32) → Linear → sigmoid. Train on CPU.
3. Evaluate on test: PR-AUC alone and in an ensemble with XGBoost (e.g. `0.7·xgb + 0.3·seq`, weight tuned on val).
4. Benchmark inference: batch 1 and batch 64, CPU vs NNPA, 1,000 runs each, report p50/p95. Chart for the video.
5. Save `models/seq.pt` and the ensemble weight.

## What not to do

- Do not claim an NNPA speed-up that was not measured.
- Do not let this card block the MVP; the scorer works without it.

## Done when

Either: GRU runs on NNPA with a measured comparison, **or**: documented reason it could not, with CPU fallback working.

## Verification steps

- Same inputs give (near) identical outputs on CPU and NNPA.
- Ensemble vs XGBoost-only metrics compared on test.

## Test before continuing

- Run `04_sequence_nnpa.ipynb` end to end.
- Screenshot the latency chart and `lscpu | grep -io nnpa` output.

## Stop condition

If `torch_nnpa` is not working by H8, switch to CPU, keep the GRU only if it improves the ensemble, and move on.

## Status

Not started
