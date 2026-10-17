"""Load and split the IBM AML transaction dataset."""

from pathlib import Path

import pandas as pd


RAW_COLUMNS = {
    "Timestamp": "ts",
    "From Bank": "src_bank",
    "Account": "src_account",
    "To Bank": "dst_bank",
    "Account.1": "dst_account",
    "Amount Received": "amount",
    "Receiving Currency": "receiving_currency",
    "Amount Paid": "amount_paid",
    "Payment Currency": "payment_currency",
    "Payment Format": "payment_format",
    "Is Laundering": "label",
}

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "HI-Small_Trans.csv"
)


def load_transactions(path=DEFAULT_PATH, nrows=None):
    """Load, normalize, and sort transactions by timestamp."""
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
        raise ValueError(
            f"Missing dataset columns: {sorted(missing)}. "
            f"Found: {list(df.columns)}"
        )

    df = df.rename(columns=RAW_COLUMNS)
    df["ts"] = pd.to_datetime(
        df["ts"],
        format="%Y/%m/%d %H:%M",
        errors="raise",
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    df["label"] = pd.to_numeric(df["label"], errors="raise").astype("int8")

    df["src"] = df["src_bank"] + "_" + df["src_account"]
    df["dst"] = df["dst_bank"] + "_" + df["dst_account"]

    df = df.drop(
        columns=["src_bank", "src_account", "dst_bank", "dst_account"]
    )

    return df.sort_values("ts", kind="stable").reset_index(drop=True)


def drop_sparse_days(df, min_share=0.01):
    """Drop calendar days with fewer rows than `min_share` of the busiest day.

    In HI-Small, normal activity stops after 2022-09-10; the remaining days
    hold only a few hundred rows, about 60% of them laundering. Keeping them
    would make validation and test unrealistic.
    """
    row_days = df["ts"].dt.normalize()
    counts = row_days.value_counts()
    dense_days = counts[counts >= min_share * counts.max()].index
    return df.loc[row_days.isin(dense_days)].copy()


def time_split(df, train_frac=0.6, val_frac=0.2, min_day_share=0.01):
    """Split transactions chronologically by calendar day, after dropping sparse days."""
    if df.empty:
        raise ValueError("Cannot split an empty DataFrame.")

    df = drop_sparse_days(df, min_day_share)

    days = (
        df["ts"]
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    if len(days) < 3:
        raise ValueError("At least three distinct dates are required.")

    train_days = max(1, int(len(days) * train_frac))
    val_days = max(1, int(len(days) * val_frac))

    if train_days + val_days >= len(days):
        train_days = len(days) - 2
        val_days = 1

    train_end = days.iloc[train_days - 1]
    val_end = days.iloc[train_days + val_days - 1]
    row_days = df["ts"].dt.normalize()

    train = df.loc[row_days <= train_end].copy()
    val = df.loc[
        (row_days > train_end) & (row_days <= val_end)
    ].copy()
    test = df.loc[row_days > val_end].copy()

    return train, val, test


def split_summary(train, val, test):
    """Return size, date range, and fraud rate for each split."""
    rows = []

    for name, part in (
        ("train", train),
        ("val", val),
        ("test", test),
    ):
        rows.append(
            {
                "split": name,
                "rows": len(part),
                "start": part["ts"].min(),
                "end": part["ts"].max(),
                "fraud_rows": int(part["label"].sum()),
                "fraud_rate_%": (
                    round(100 * part["label"].mean(), 4)
                    if len(part)
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(rows)
