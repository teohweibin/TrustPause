"""Train the XGBoost receiver-risk model. Run from the repo root:

    nohup python -m src.train_xgb > data/train_xgb.log 2>&1 &

Reads data/features_all.pkl (card 02) and writes:
  models/xgb.json         booster, trimmed to the best iteration
  models/thresholds.json  pause / hold thresholds chosen on validation
  models/metrics.json     validation and test metrics
  data/xgb_scores.pkl     validation and test scores (for card 04 and the notebook)
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score

from .features import FEATURE_NAMES

ROOT = Path(__file__).resolve().parent.parent
ALERT_RATES = [0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02]


def band(scores, labels, threshold):
    alerts = scores >= threshold
    n_alerts = int(alerts.sum())
    caught = int(labels[alerts].sum())
    return {
        "threshold": float(threshold),
        "alert_rate_%": round(100 * n_alerts / len(scores), 4),
        "alerts": n_alerts,
        "laundering_caught": caught,
        "precision_%": round(100 * caught / n_alerts, 2) if n_alerts else 0.0,
        "recall_%": round(100 * caught / max(int(labels.sum()), 1), 2),
    }


def summary(scores, labels):
    return {
        "rows": int(len(labels)),
        "laundering": int(labels.sum()),
        "pr_auc": round(float(average_precision_score(labels, scores)), 4),
        "roc_auc": round(float(roc_auc_score(labels, scores)), 4),
        "base_rate_%": round(100 * float(labels.mean()), 4),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Train the XGBoost receiver-risk model")
    parser.add_argument("--features", default=ROOT / "data" / "features_all.pkl")
    parser.add_argument("--models", default=ROOT / "models")
    parser.add_argument("--scores-out", default=ROOT / "data" / "xgb_scores.pkl")
    parser.add_argument("--pause-rate", type=float, default=0.005, help="share of validation transfers to pause")
    parser.add_argument("--hold-rate", type=float, default=0.0005, help="share of validation transfers to hold")
    parser.add_argument("--n-estimators", type=int, default=2000)
    parser.add_argument("--threads", type=int, default=3)
    args = parser.parse_args(argv)
    models = Path(args.models)
    models.mkdir(exist_ok=True)

    features = pd.read_pickle(args.features)
    parts = {name: features[features["split"] == name] for name in ("train", "val", "test")}
    X = {k: v[FEATURE_NAMES].to_numpy(dtype=np.float32) for k, v in parts.items()}
    y = {k: v["label"].to_numpy(dtype=np.int8) for k, v in parts.items()}
    index = {k: v.index for k, v in parts.items()}
    del features, parts

    pos = int(y["train"].sum())
    spw = (len(y["train"]) - pos) / max(pos, 1)
    print(f"Train {len(y['train']):,} rows, {pos:,} laundering; scale_pos_weight={spw:.0f}", flush=True)

    model = xgb.XGBClassifier(
        n_estimators=args.n_estimators,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=spw,
        tree_method="hist",
        eval_metric="aucpr",
        early_stopping_rounds=100,
        n_jobs=args.threads,
        random_state=42,
    )
    start = time.time()
    model.fit(X["train"], y["train"], eval_set=[(X["val"], y["val"])], verbose=100)
    train_seconds = time.time() - start
    best = int(model.best_iteration)
    print(f"Trained in {train_seconds:.0f}s; best iteration {best}", flush=True)

    booster = model.get_booster()[: best + 1]
    booster.feature_names = list(FEATURE_NAMES)
    booster.save_model(models / "xgb.json")

    scores = {k: booster.inplace_predict(X[k]) for k in ("val", "test")}

    pause_t = float(np.quantile(scores["val"], 1 - args.pause_rate))
    hold_t = float(np.quantile(scores["val"], 1 - args.hold_rate))
    thresholds = {
        "pause": pause_t,
        "hold": hold_t,
        "pause_rate_on_val": args.pause_rate,
        "hold_rate_on_val": args.hold_rate,
        "feature_names": FEATURE_NAMES,
    }
    (models / "thresholds.json").write_text(json.dumps(thresholds, indent=2))

    # Single-transaction latency, as the API will call it
    sample = X["test"][:1000]
    timings = []
    for row in sample:
        t = time.perf_counter()
        booster.inplace_predict(row.reshape(1, -1))
        timings.append(1000 * (time.perf_counter() - t))

    importance = booster.get_score(importance_type="gain")
    metrics = {
        "best_iteration": best,
        "train_seconds": round(train_seconds, 1),
        "scale_pos_weight": round(spw, 1),
        "single_predict_ms_p50": round(float(np.percentile(timings, 50)), 3),
        "single_predict_ms_p95": round(float(np.percentile(timings, 95)), 3),
        "importance_gain": dict(sorted(importance.items(), key=lambda kv: -kv[1])),
    }
    for split in ("val", "test"):
        metrics[split] = summary(scores[split], y[split])
        metrics[split]["pause_band"] = band(scores[split], y[split], pause_t)
        metrics[split]["hold_band"] = band(scores[split], y[split], hold_t)
        metrics[split]["by_alert_rate"] = [
            band(scores[split], y[split], np.quantile(scores["val"], 1 - r)) for r in ALERT_RATES
        ]
    (models / "metrics.json").write_text(json.dumps(metrics, indent=2))

    pd.concat([
        pd.DataFrame({"split": split, "score_xgb": scores[split], "label": y[split]}, index=index[split])
        for split in ("val", "test")
    ]).to_pickle(args.scores_out)

    for split in ("val", "test"):
        m = metrics[split]
        print(f"\n{split}: PR-AUC {m['pr_auc']}  ROC-AUC {m['roc_auc']}  base rate {m['base_rate_%']}%")
        print(pd.DataFrame(m["by_alert_rate"]).to_string(index=False))
        print(f"pause band: {m['pause_band']}")
        print(f"hold band:  {m['hold_band']}")
    print(f"\nSingle prediction: p50 {metrics['single_predict_ms_p50']} ms, p95 {metrics['single_predict_ms_p95']} ms")
    print(f"Saved {models / 'xgb.json'}, thresholds.json, metrics.json and {args.scores_out}")


if __name__ == "__main__":
    main()
