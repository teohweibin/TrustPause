# Work Card 00: LinuxONE Setup Gate

## Goal

Confirm the shared LinuxONE server, Jupyter and team access are ready before building.

## Owner

Team lead

## Checklist

### Server
- [x] L1CC server created (Ubuntu 24.04-Datathon image), status ACTIVE
- [x] SSH login works: `ssh -i ibmzdatathon.pem linux1@<IP>`
- [x] Docker installed (`docker ps` works without sudo)
- [x] Jupyter container `notebook` running
- [x] Jupyter reachable through SSH tunnel at `http://localhost:38888`
- [ ] Port 38888 **not** open to the internet (`sudo iptables -L INPUT -n | grep 38888` prints nothing), or token changed from the default
- [ ] Event code `SSF2026` in the L1CC project description

### Platform checks
- [x] Telum NNPA present: `lscpu | grep -io nnpa` → `nnpa`
- [x] Libraries present: xgboost 3.4.1, torch 2.11 + torch_nnpa 1.5.0, tensorflow 2.18.1, llama_cpp_python 0.3.36, networkx 3.7, pandas 3.0.6, scikit-learn 1.9.0
- [ ] `pip install fastapi uvicorn` succeeds in the Jupyter terminal
- [ ] Server resources noted: `free -h`, `nproc`
- [ ] `git --version` works in the Jupyter terminal (needed to push from the server)

### Required labs
- [x] Both IBM labs run (`Fraud_LSTM_Keras_TF.ipynb`, `Loan_Approval_Demo.ipynb`)
- [ ] Screenshots of both labs saved to `screenshots/labs/`
- [ ] Confirmed on Discord which two labs count as mandatory

### Team
- [ ] Every member can SSH in and open Jupyter through their own tunnel
- [ ] `.pem` shared only through a private channel (or members added their own public keys)
- [ ] Roles assigned (see `build-blueprint.md` → Team Split)

## Commands

```bash
free -h
nproc
lscpu | grep -io nnpa
sudo iptables -L INPUT -n | grep 38888
pip install fastapi uvicorn
git --version
```

## Done when

All boxes above are ticked or have a recorded workaround in `build-status.md`.

## Stop condition

If the server is unreachable: stop the VM in the L1CC dashboard until SHUTOFF, start it again, then restart Jupyter with `docker start notebook`. If still broken after 15 minutes, post in Discord `#ibm-z-sme-helpdesk`.

## Status

Mostly done: see unticked items.
