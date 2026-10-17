# Prompt: Build Runner

Paste this into your AI coding assistant, replacing `NN`:

```text
Read START_HERE.md, build-status.md, build-blueprint.md, architecture.md, design.md, and work-cards/NN-*.md.

Implement only Work Card NN.

Rules:
- Code runs on IBM LinuxONE (s390x) in the L1CC Jupyter image. Use only libraries listed in architecture.md; flag any new dependency before adding it.
- Write new code from scratch. Do not copy from earlier projects or the IBM lab notebooks.
- No external AI APIs. Granite runs locally via llama_cpp_python.
- Never put secrets, keys, .pem files, account IDs in LLM prompts, or real personal data in code.
- Do not invent metrics; every number shown must be computed.
- Keep Granite off the real-time decision path.
- Follow design.md for any UI.
- Do not start the next work card or change scope.
- Run the card's verification steps.
- Update build-status.md: what changed, what passed, what failed, measured numbers, next card.
- Stop and wait for the team's check.
```

## After each card, report

**Work Card NN complete**

- **What changed:** files created or updated
- **How to run it:** the notebook or command on the server
- **Tests before moving on:** 2–5 specific checks from the card
- **Numbers measured:** anything to copy into `build-status.md` → Measured results
- **Next:** `continue`, or `fix` with the error
