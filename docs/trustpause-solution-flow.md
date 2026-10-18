# TrustPause Solution Flowchart

TrustPause detects receiver-side scam risk and supports a human-in-the-loop pause decision on IBM LinuxONE.

```mermaid
flowchart LR
    dataset["IBM AML synthetic dataset<br/>HI-Small_Trans.csv"]
    loader["Data loader<br/>src/data.py<br/>parse, normalize, chronological split"]
    state["Receiver-side AccountState<br/>src/features.py<br/>rolling history and network features"]

    xgb["XGBoost risk model<br/>src/train_xgb.py"]
    reasons["Behavioural reason codes<br/>src/reasons.py"]
    gru["GRU sequence model<br/>src/train_seq.py<br/>CPU / Telum NNPA"]

    decision["TrustPause decision bands<br/>allow / hold / pause"]
    store["SQLite case store and replay state<br/>src/db.py + src/stream.py"]
    api["FastAPI scorer and API<br/>src/api.py"]

    granite["IBM Granite explainer<br/>src/explain.py<br/>analyst notes only<br/>no account IDs in prompts"]
    sender["Sender view<br/>web/sender.html"]
    analyst["Analyst view<br/>web/analyst.html"]

    deploy["IBM LinuxONE s390x<br/>Docker deployment<br/>SSH tunnel access"]

    dataset --> loader --> state
    state --> xgb
    state --> gru
    xgb --> reasons --> decision
    xgb --> decision
    gru --> decision

    decision --> store --> api
    decision --> sender
    decision --> analyst
    decision -. "held cases only" .-> granite
    granite -. "analyst note" .-> analyst

    deploy -. "hosts" .-> api
    deploy -. "mounts data, models, and Granite" .-> api
