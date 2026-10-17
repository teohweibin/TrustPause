# Prompt: Review Mirror

Use after cards 06 and 07, and before submission.

```text
Read project-brief.md, architecture.md, design.md, build-blueprint.md, build-status.md, and the latest completed work card.

Review the current project against them. Check:
1. Does it match the version-one promise in build-blueprint.md?
2. Does the full flow work: replay → features → models → decision → Granite → views?
3. Is Granite off the decision path, and does its prompt contain no account IDs?
4. Are all numbers shown in the UI, README and video computed by us (no invented stats)?
5. Is the time-based split respected (no leakage)?
6. Does the UI follow design.md (chips with labels, modal focus, readable at 1920×1080, sender view at 375 px)?
7. Are there real bank brands, fake logos, or lorem ipsum?
8. Is anything secret in the repo (.pem, tokens, data, .db, .gguf)?
9. Does the submission checklist in work-cards/09 pass?

Return:
- PASS / NEEDS FIX
- top 1–3 issues
- the single smallest useful fix
Do not redesign the project.
```
