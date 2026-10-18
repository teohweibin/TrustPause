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


## Docker on IBM LinuxONE

Build the s390x Docker image on the LinuxONE host:

```bash
docker build -t trustpause .
```

The dataset, model artifacts, database, private keys, and Granite model must not be included in the image. Mount the required resources at runtime.

```bash
docker run -d \
  --name trustpause \
  --network host \
  -v ~/shared/trustpause/data:/app/data \
  -v ~/shared/trustpause/models:/app/models:ro \
  -v /path/to/granite:/granite:ro \
  -e GRANITE_MODEL_PATH=/granite/model.gguf \
  trustpause
```

Replace the Granite paths with the actual model directory and filename before running.

The default application port is `8000`. For parallel verification, an unused port such as `8001` can be used:

```bash
docker run -d \
  --name trustpause-test \
  --network host \
  -v ~/shared/trustpause/data:/app/data \
  -v ~/shared/trustpause/models:/app/models:ro \
  trustpause \
  python3 -m uvicorn src.api:app --host 127.0.0.1 --port 8001
```

### Deployment Verification

The Docker deployment was tested on IBM LinuxONE (`s390x`).

- Docker image build: Passed.
- Container startup: Passed.
- API readiness: Passed.
- `/sender` page: HTTP 200.
- `/analyst` page: HTTP 200.
- SSH tunnel access: Verified.
- Granite model mounting: Verified.

The Granite `.gguf` model was copied from the existing Jupyter container to `/home/linux1/granite/` and mounted inside the Docker container at `/granite`. `GRANITE_MODEL_PATH` was verified and the model file was readable inside the container.
