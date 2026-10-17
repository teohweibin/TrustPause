"""Load the IBM AML transactions dataset and split it by time."""

from pathlib import Path

import pandas as pd

# Raw CSV header has "Account" twice; pandas renames the second one to "Account.1".
RAW_COLUMNS = {
    "Timestamp": "ts",
    "From Bank": "src_bank",
    "Account": "src_account",
    "To Bank": "dst_bank",
    "Account.1": "dst_account",
    "Amount Received": "amount_received",
    "Receiving Currency": "receiving_currency",
    "Amount Paid": "amount_paid",
    "Payment Currency": "payment_currency",
    "Payment Format": "payment_format",
    "Is Laundering": "label",
}

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "HI-Small_Trans.csv"


def load_transactions(path=DEFAULT_PATH, nrows=None):
    """Return transactions sorted by time with opaque `src` / `dst` account keys."""
    df = pd.read_csv(
        path,
        nrows=nrows,
        dtype={
            "From Bank": "string",
            "Account": "string",
            "To Bank": "string",
            "Account.1": "string",
            "Receiving Currency": "category",
            "Payment Currency": "category",
            "Payment Format": "category",
            "Is Laundering": "int8",
        },
    )

    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Unexpected dataset columns, missing: {sorted(missing)}. Found: {list(df.columns)}")

    df = df.rename(columns=RAW_COLUMNS)
    df["ts"] = pd.to_datetime(df["ts"], format="%Y/%m/%d %H:%M")
    df["src"] = df["src_bank"] + "_" + df["src_account"]
    df["dst"] = df["dst_bank"] + "_" + df["dst_account"]
    df = df.drop(columns=["src_bank", "src_account", "dst_bank", "dst_account"])

    return df.sort_values("ts", kind="stable").reset_index(drop=True)


def time_split(df, train_frac=0.6, val_frac=0.2):
    """Split by calendar day so every test transaction is later than every training one."""
    days = df["ts"].dt.normalize()
    unique_days = days.drop_duplicates().sort_values().to_list()
    n = len(unique_days)
    train_end = unique_days[max(1, int(n * train_frac)) - 1]
    val_end = unique_days[max(2, int(n * (train_frac + val_frac))) - 1]

    train = df[days <= train_end]
    val = df[(days > train_end) & (days <= val_end)]
    test = df[days > val_end]
    return train, val, test


def split_summary(train, val, test):
    """One row per split: size, date range and fraud rate."""
    rows = []
    for name, part in (("train", train), ("val", val), ("test", test)):
        rows.append({
            "split": name,
            "rows": len(part),
            "start": part["ts"].min(),
            "end": part["ts"].max(),
            "fraud_rows": int(part["label"].sum()),
            "fraud_rate_%": round(100 * part["label"].mean(), 4) if len(part) else 0.0,
        })
    return pd.DataFrame(rows)
