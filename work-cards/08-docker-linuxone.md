# Work Card 08: Docker on LinuxONE

## Goal

The backend and frontend run as a Docker container on the LinuxONE server, as evidence of containerised deployment.

## Owner

E (Docker)

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

Not started
