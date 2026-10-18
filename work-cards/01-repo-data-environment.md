# Work Card 01: Repo, Data and Environment

## Goal

A GitHub repo cloned on the server at `~/shared/trustpause/`, with the folder layout, `.gitignore`, `requirements.txt`, and the dataset loaded and checked.

## Inputs

- `architecture.md` → File Expectations, Data / State Model
- Kaggle dataset `ealtman2019/ibm-transactions-for-anti-money-laundering-aml`, file `HI-Small_Trans.csv`

## Files likely touched

`.gitignore`, `requirements.txt`, `README.md` (stub), `src/__init__.py`, `src/data.py`, `notebooks/01_explore.ipynb`

## Instructions for the coding agent

1. Create the folder layout from `architecture.md`. Copy this planning pack into the repo root (or the repo *is* this folder).
2. `.gitignore` must include: `*.pem`, `data/`, `*.db`, `__pycache__/`, `.ipynb_checkpoints/`, `.env`, `*.gguf`.
3. `requirements.txt`: `fastapi`, `uvicorn` (others are already in the image; list them with versions in the README instead).
4. Get the dataset onto the server under `data/`. It is larger than Jupyter's 200 MB upload limit: download on a laptop and `scp -i <key>.pem HI-Small_Trans.csv linux1@<IP>:~/shared/trustpause/data/`.
5. `src/data.py`: `load_transactions(path, nrows=None)` → DataFrame with parsed timestamps, `src = From Bank + "_" + Account`, `dst = To Bank + "_" + Account.1`, `amount`, `payment_format`, `label`; sorted by time. `time_split(df)` → train / val / test by date (≈60/20/20).
6. `notebooks/01_explore.ipynb`: row count, date range, fraud rate per split, top fan-in receivers, memory usage.

## What not to do

- Do not commit the dataset, `.pem` or any `.db` file.
- Do not split randomly.
- Do not copy code from MulePulse or the labs.

## Done when

- Repo exists on GitHub and is cloned at `~/shared/trustpause/`.
- `load_transactions` + `time_split` run on the server; notebook shows the stats above.

## Verification steps

- `git status` shows no data or key files staged.
- Columns match the expected list (or `architecture.md` is updated with the real names).
- Fraud rate is reported for each split; memory use fits the server (`free -h`).

## Test before continuing

- Open `01_explore.ipynb` on the server and run all cells without errors.
- Confirm the test split is the latest dates.
- Push and see the repo on GitHub without `data/`.

## Stop condition

If the full file does not fit in memory, use `nrows` or sample whole days and record the choice in `build-status.md`.

## Status

Done: verified on IBM LinuxONE (see `build-status.md` → Work Card 01 Verification).
