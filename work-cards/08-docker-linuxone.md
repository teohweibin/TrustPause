# Work Card 08: Docker on LinuxONE

## Goal

The backend and frontend run as a Docker container on the LinuxONE server, as evidence of containerised deployment.

## Inputs

Working app from cards 06–07.

## Files likely touched

`Dockerfile`, `.dockerignore`, `README.md`

## Instructions for the coding agent

1. Build on the Jupyter image so all s390x libraries are present:
   ```dockerfile
   FROM registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x:latest
   WORKDIR /app
   COPY . /app
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   Check the image's default user and Python path; adjust if `pip`/`uvicorn` aren't on PATH.
2. `.dockerignore`: `data/`, `*.pem`, `.git`, `*.db`, `.ipynb_checkpoints`.
3. Mount data, models and the Granite file instead of copying them:
   ```bash
   docker build -t trustpause .
   docker run -d --name trustpause --network host \
     -v ~/shared/trustpause/data:/app/data \
     -v ~/shared/trustpause/models:/app/models \
     -v <granite-dir>:/granite -e GRANITE_MODEL_PATH=/granite/<file>.gguf \
     trustpause
   ```
4. Add the run instructions to the README.

## What not to do

- Do not bake the dataset, keys or the Granite file into the image.
- Do not stop or remove the team's `notebook` container.

## Done when

`docker ps` shows `trustpause` running and both views work through the tunnel.

## Verification steps

- `docker ps` and `docker logs trustpause` clean.
- Screenshot `docker ps` + `uname -m` (shows `s390x`) for the video.

## Test before continuing

- Open `http://localhost:8000/sender` and `/analyst` through the tunnel; repeat the card 07 tests.

## Stop condition

If the build fails after 45 minutes, demo the app running with uvicorn directly and show the Dockerfile in the video as "container-ready".

## Status

Complete — verified on IBM LinuxONE.

Evidence:

- `Dockerfile` builds successfully as image `trustpause:latest`.
- Image architecture is `s390x`.
- `.dockerignore` excludes `data/`, `models/`, `*.gguf`, `*.pem`, `*.db`, `.git/`, and notebook caches.
- Container `trustpause` starts successfully on isolated host port `8001`.
- API warm-up completed for 4,214,445 historical transactions.
- `/api/status` returned `stage: ready`.
- `/sender` returned HTTP 200.
- `/analyst` returned HTTP 200.
- Both views opened successfully through an SSH tunnel.
- Granite model was copied from the existing Jupyter container to `/home/linux1/granite/`.
- `GRANITE_MODEL_PATH=/granite/granite-4.0-h-350m-base-be.f16.gguf` was set.
- The Granite model was readable inside the `trustpause` container.
- Deployment evidence: `screenshots/docker_s390x_evidence.png`.
