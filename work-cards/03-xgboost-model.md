# Work Card 03: XGBoost Model + Reasons

## Goal

A trained XGBoost receiver-risk model with chosen decision thresholds and plain-language top reasons for each prediction.

## Owner

B (XGBoost)

## Inputs

Feature tables from card 02.

## Files likely touched

`src/train_xgb.py`, `src/reasons.py`, `notebooks/03_xgboost.ipynb`, `models/xgb.json`, `models/thresholds.json`, `models/metrics.json`, `data/xgb_scores.pkl`

## Instructions for the coding agent

1. Train on train split; early-stop on val. Handle imbalance with `scale_pos_weight`.
2. Evaluate on test: PR-AUC, ROC-AUC, precision and recall per band. Choose the band edges on **val** by alert budget (default: pause top 0.5%, hold top 0.05%), then report on test.
3. Reasons: `booster.predict(DMatrix, pred_contribs=True)` → take top 3 positive contributions → map each feature to a reason code and sentence, e.g. `FAN_IN_HIGH` → "received money from {unique_senders_24h} different senders in 24 hours".
4. Save model as `models/xgb.json` and thresholds as `models/thresholds.json`.
5. Notebook: PR curve, confusion matrix per band, feature importance, 3 example explanations.

## What not to do

- Do not install `shap`.
- Do not tune thresholds on the test set.
- Do not report accuracy as the headline metric.

## Done when

Model and thresholds saved; test metrics and reason examples shown in the notebook.

## Verification steps

- Reload `xgb.json` in a fresh kernel and get the same predictions.
- Reason sentences contain numbers but no account IDs.
- Single-transaction prediction time measured.

## Test before continuing

- Run `03_xgboost.ipynb` end to end.
- Screenshot the PR curve and metrics table to `screenshots/`.

## Stop condition

If PR-AUC is very low, check features for bugs (card 02) before tuning the model.

## Status

Done: trained and verified on LinuxONE (see build-status.md)
