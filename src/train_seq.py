"""Train and benchmark the TrustPause receiver sequence model."""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
import torch
from torch.utils.data import DataLoader, TensorDataset

from .data import drop_sparse_days, load_transactions
from .features import FEATURE_NAMES


ROOT = Path(__file__).resolve().parent.parent
SEQ_FEATURE_NAMES = [
    "log_amount",
    "time_gap_minutes",
    "direction",
    "counterparty_novelty",
    "payment_format",
    "cross_currency",
]
SEQ_LEN = 10


class SequenceGRU(torch.nn.Module):
    """Small GRU used for receiver transaction histories."""

    def __init__(self, input_size=6, hidden_size=32):
        super().__init__()
        self.gru = torch.nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            batch_first=True,
        )
        self.output = torch.nn.Linear(hidden_size, 1)

    def forward(self, inputs):
        sequence, _ = self.gru(inputs)
        return self.output(sequence[:, -1, :]).squeeze(-1)


def _append_event(
    histories,
    account,
    timestamp,
    amount,
    direction,
    counterparty,
    payment_format,
    cross_currency,
):
    history = histories.setdefault(account, deque(maxlen=SEQ_LEN))
    previous_time = history[-1][0] if history else None
    previous_parties = {event[7] for event in history}

    gap_minutes = (
        0.0
        if previous_time is None
        else max(0.0, (timestamp - previous_time) / 60.0)
    )

    history.append(
        (
            timestamp,
            float(np.log1p(max(float(amount), 0.0))),
            min(gap_minutes, 24.0 * 60.0),
            float(direction),
            float(counterparty not in previous_parties),
            float(payment_format),
            float(cross_currency),
            counterparty,
        )
    )


def _sequence_from_history(history):
    sequence = np.zeros((SEQ_LEN, len(SEQ_FEATURE_NAMES)), dtype=np.float32)
    events = list(history)[-SEQ_LEN:]

    if events:
        sequence[-len(events):] = np.asarray(
            [event[1:7] for event in events],
            dtype=np.float32,
        )

    return sequence


def iter_sequence_batches(
    df,
    target_mask,
    format_codes,
    batch_size=1024,
):
    """Yield receiver-history sequences before each selected transaction."""
    histories = {}
    batch_sequences = []
    batch_labels = []
    batch_indices = []

    for position, row in enumerate(df.itertuples(index=True)):
        timestamp = int(pd.Timestamp(row.ts).timestamp())
        payment_format = format_codes[str(row.payment_format)]
        cross_currency = str(row.receiving_currency) != str(row.payment_currency)

        if target_mask[position]:
            history = histories.get(row.dst, deque(maxlen=SEQ_LEN))
            batch_sequences.append(_sequence_from_history(history))
            batch_labels.append(int(row.label))
            batch_indices.append(row.Index)

            if len(batch_sequences) >= batch_size:
                yield (
                    np.asarray(batch_sequences, dtype=np.float32),
                    np.asarray(batch_labels, dtype=np.int8),
                    np.asarray(batch_indices),
                )
                batch_sequences = []
                batch_labels = []
                batch_indices = []

        _append_event(
            histories,
            row.dst,
            timestamp,
            row.amount,
            direction=1.0,
            counterparty=row.src,
            payment_format=payment_format,
            cross_currency=cross_currency,
        )
        _append_event(
            histories,
            row.src,
            timestamp,
            row.amount_paid,
            direction=-1.0,
            counterparty=row.dst,
            payment_format=payment_format,
            cross_currency=cross_currency,
        )

    if batch_sequences:
        yield (
            np.asarray(batch_sequences, dtype=np.float32),
            np.asarray(batch_labels, dtype=np.int8),
            np.asarray(batch_indices),
        )


def collect_sequences(df, target_mask, format_codes, batch_size=1024):
    batches = list(
        iter_sequence_batches(
            df,
            target_mask,
            format_codes,
            batch_size=batch_size,
        )
    )

    if not batches:
        raise ValueError("No target transactions were selected.")

    return (
        np.concatenate([item[0] for item in batches]),
        np.concatenate([item[1] for item in batches]),
        np.concatenate([item[2] for item in batches]),
    )


def load_dense_dataset(data_path, features_path):
    raw = load_transactions(data_path)
    dense = drop_sparse_days(raw).copy()

    metadata = pd.read_pickle(features_path)
    train_end = pd.to_datetime(
        metadata.loc[metadata["split"] == "train", "ts"].max()
    )
    val_end = pd.to_datetime(
        metadata.loc[metadata["split"] == "val", "ts"].max()
    )

    dense["split"] = np.select(
        [
            dense["ts"] <= train_end,
            dense["ts"] <= val_end,
        ],
        [
            "train",
            "val",
        ],
        default="test",
    )

    return dense, train_end, val_end


def choose_training_rows(labels, split_values, max_rows, seed):
    train_positions = np.flatnonzero(split_values == "train")

    if max_rows is None or len(train_positions) <= max_rows:
        return train_positions

    if max_rows < 2:
        raise ValueError("max_rows must be at least 2.")

    positive = train_positions[labels[train_positions] == 1]
    negative = train_positions[labels[train_positions] == 0]

    rng = np.random.default_rng(seed)

    positive_budget = min(len(positive), max(1, max_rows // 2))
    negative_budget = max_rows - positive_budget

    selected_positive = rng.choice(
        positive,
        size=positive_budget,
        replace=False,
    )
    selected_negative = rng.choice(
        negative,
        size=min(negative_budget, len(negative)),
        replace=False,
    )

    selected = np.concatenate([selected_positive, selected_negative])
    rng.shuffle(selected)
    return np.sort(selected)


def normalize_sequences(sequences, mean=None, std=None):
    if mean is None:
        mean = sequences.mean(axis=(0, 1))
    if std is None:
        std = sequences.std(axis=(0, 1))

    std = np.where(std < 1e-6, 1.0, std)
    normalized = (sequences - mean.reshape(1, 1, -1)) / std.reshape(1, 1, -1)
    return normalized.astype(np.float32), mean.astype(np.float32), std.astype(np.float32)


def train_model(sequences, labels, epochs, batch_size, threads, seed):
    torch.manual_seed(seed)
    torch.set_num_threads(threads)

    model = SequenceGRU().float()
    dataset = TensorDataset(
        torch.from_numpy(sequences),
        torch.from_numpy(labels.astype(np.float32)),
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    positives = max(int(labels.sum()), 1)
    negatives = max(len(labels) - positives, 1)
    loss_function = torch.nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([negatives / positives])
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0

        for batch_inputs, batch_labels in loader:
            optimizer.zero_grad()
            logits = model(batch_inputs)
            loss = loss_function(logits, batch_labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(batch_labels)

        print(
            f"epoch {epoch}/{epochs}: "
            f"loss={total_loss / len(dataset):.5f}",
            flush=True,
        )

    return model.eval()


def score_sequences(model, df, target_mask, format_codes, mean, std, batch_size):
    scores = []
    labels = []
    indices = []

    with torch.inference_mode():
        for sequences, batch_labels, batch_indices in iter_sequence_batches(
            df,
            target_mask,
            format_codes,
            batch_size=batch_size,
        ):
            normalized = (sequences - mean.reshape(1, 1, -1)) / std.reshape(
                1,
                1,
                -1,
            )
            logits = model(torch.from_numpy(normalized.astype(np.float32)))
            scores.append(torch.sigmoid(logits).numpy())
            labels.append(batch_labels)
            indices.append(batch_indices)

    return (
        np.concatenate(scores),
        np.concatenate(labels),
        np.concatenate(indices),
    )


def benchmark(model, runs, threads):
    torch.set_num_threads(threads)
    results = {}

    cpu_model = SequenceGRU().eval().float()
    cpu_model.load_state_dict(model.state_dict())

    for batch_size in (1, 64):
        cpu_inputs = torch.randn(batch_size, SEQ_LEN, 6, dtype=torch.float32)

        with torch.inference_mode():
            for _ in range(20):
                cpu_model(cpu_inputs)

        timings = []
        with torch.inference_mode():
            for _ in range(runs):
                start = time.perf_counter()
                cpu_model(cpu_inputs)
                timings.append((time.perf_counter() - start) * 1000)

        results[f"cpu_batch_{batch_size}"] = {
            "p50_ms": round(float(np.percentile(timings, 50)), 3),
            "p95_ms": round(float(np.percentile(timings, 95)), 3),
        }

    try:
        import torch_nnpa

        if not torch_nnpa.NNPAModule.is_available():
            raise RuntimeError("torch_nnpa reports NNPA unavailable")

        nnpa_device = torch_nnpa.device()
        nnpa_model = SequenceGRU().eval().half()
        nnpa_model.load_state_dict(model.state_dict())
        nnpa_model = nnpa_model.to(nnpa_device)

        for batch_size in (1, 64):
            nnpa_inputs = torch.randn(
                batch_size,
                SEQ_LEN,
                6,
                dtype=torch.float16,
                device=nnpa_device,
            )

            with torch.inference_mode():
                for _ in range(20):
                    nnpa_model(nnpa_inputs).to("cpu")

            timings = []
            with torch.inference_mode():
                for _ in range(runs):
                    start = time.perf_counter()
                    nnpa_model(nnpa_inputs).to("cpu")
                    timings.append((time.perf_counter() - start) * 1000)

            results[f"nnpa_batch_{batch_size}"] = {
                "p50_ms": round(float(np.percentile(timings, 50)), 3),
                "p95_ms": round(float(np.percentile(timings, 95)), 3),
            }
    except Exception as error:
        results["nnpa_error"] = f"{type(error).__name__}: {error}"

    return results


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=ROOT / "data" / "HI-Small_Trans.csv")
    parser.add_argument(
        "--features",
        default=ROOT / "data" / "features_all.pkl",
    )
    parser.add_argument(
        "--xgb-scores",
        default=ROOT / "data" / "xgb_scores.pkl",
    )
    parser.add_argument("--model-out", default=ROOT / "models" / "seq.pt")
    parser.add_argument("--max-train-rows", type=int, default=100_000)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--benchmark-runs", type=int, default=1000)
    parser.add_argument("--threads", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    print("Loading dense transaction data...", flush=True)
    df, train_end, val_end = load_dense_dataset(args.data, args.features)
    print(
        f"rows={len(df):,}; train_end={train_end}; val_end={val_end}",
        flush=True,
    )

    format_codes = {
        value: code
        for code, value in enumerate(
            sorted(df["payment_format"].astype(str).unique())
        )
    }

    labels = df["label"].to_numpy(dtype=np.int8)
    split_values = df["split"].to_numpy()
    train_positions = choose_training_rows(
        labels,
        split_values,
        args.max_train_rows,
        args.seed,
    )

    train_mask = np.zeros(len(df), dtype=bool)
    train_mask[train_positions] = True

    print(
        f"Building {len(train_positions):,} training sequences...",
        flush=True,
    )
    train_sequences, train_labels, _ = collect_sequences(
        df,
        train_mask,
        format_codes,
        batch_size=args.batch_size,
    )
    train_sequences, mean, std = normalize_sequences(train_sequences)

    print(
        f"training positives={int(train_labels.sum()):,}; "
        f"negatives={int((train_labels == 0).sum()):,}",
        flush=True,
    )

    model = train_model(
        train_sequences,
        train_labels,
        epochs=args.epochs,
        batch_size=args.batch_size,
        threads=args.threads,
        seed=args.seed,
    )

    split_results = {}
    xgb_scores = pd.read_pickle(args.xgb_scores)["score_xgb"]
    selected_ensemble_weight = None

    for split in ("val", "test"):
        target_mask = split_values == split
        print(f"Scoring {split} sequences...", flush=True)

        seq_scores, split_labels, split_indices = score_sequences(
            model,
            df,
            target_mask,
            format_codes,
            mean,
            std,
            batch_size=args.batch_size,
        )
        xgb_for_split = xgb_scores.reindex(split_indices).to_numpy(dtype=float)

        if np.isnan(xgb_for_split).any():
            missing = int(np.isnan(xgb_for_split).sum())
            raise ValueError(
                f"Missing {missing} XGBoost scores for {split} indices."
            )

        if split == "val":
            best_weight = 0.0
            best_pr_auc = -1.0

            for weight in np.linspace(0.0, 1.0, 21):
                ensemble_scores = (
                    weight * xgb_for_split
                    + (1.0 - weight) * seq_scores
                )
                pr_auc = average_precision_score(
                    split_labels,
                    ensemble_scores,
                )

                if pr_auc > best_pr_auc:
                    best_pr_auc = float(pr_auc)
                    best_weight = float(weight)

            selected_ensemble_weight = best_weight
        else:
            if selected_ensemble_weight is None:
                raise RuntimeError(
                    "Validation ensemble weight was not selected."
                )

            best_weight = selected_ensemble_weight
            ensemble_scores = (
                best_weight * xgb_for_split
                + (1.0 - best_weight) * seq_scores
            )
            best_pr_auc = float(
                average_precision_score(split_labels, ensemble_scores)
            )

        split_results[split] = {
            "rows": int(len(split_labels)),
            "positives": int(split_labels.sum()),
            "seq_pr_auc": round(
                float(average_precision_score(split_labels, seq_scores)),
                6,
            ),
            "xgb_pr_auc": round(
                float(average_precision_score(split_labels, xgb_for_split)),
                6,
            ),
            "ensemble_pr_auc": round(best_pr_auc, 6),
            "ensemble_xgb_weight": round(best_weight, 3),
        }

        print(split_results[split], flush=True)

    benchmark_results = benchmark(
        model,
        runs=args.benchmark_runs,
        threads=args.threads,
    )
    print("benchmark:", json.dumps(benchmark_results, indent=2), flush=True)

    checkpoint = {
        "state_dict": model.state_dict(),
        "input_size": len(SEQ_FEATURE_NAMES),
        "hidden_size": 32,
        "sequence_length": SEQ_LEN,
        "feature_names": SEQ_FEATURE_NAMES,
        "normalization_mean": mean.tolist(),
        "normalization_std": std.tolist(),
        "ensemble_xgb_weight": best_weight,
        "train_rows": int(len(train_labels)),
        "train_end": str(train_end),
        "val_end": str(val_end),
        "results": split_results,
        "benchmark": benchmark_results,
    }

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.model_out)

    print(f"Saved sequence model to {args.model_out}", flush=True)


if __name__ == "__main__":
    main()