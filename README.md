# TrustPause

TrustPause is an IBM Z Datathon 2026 prototype for receiver-side scam-risk detection on IBM LinuxONE.

## Current status

Work Card 01 is setting up the repository, IBM AML dataset, normalized data loader, and exploration notebook.

## Dataset

Place the IBM AML dataset at:

```text
data/HI-Small_Trans.csv
```

The dataset is excluded from Git and must not be committed.

## Work Card 01 checks

The project currently verifies:

- IBM AML transactions load successfully.
- Timestamps are parsed and sorted.
- Source and destination account keys are normalized.
- Train, validation, and test splits are chronological.
- Exploration statistics are generated in `notebooks/01_explore.ipynb`.

## Planned runtime

TrustPause will run on IBM LinuxONE using Python, FastAPI, XGBoost, PyTorch, Granite, SQLite, and plain HTML views.
