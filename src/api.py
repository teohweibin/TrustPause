"""TrustPause API. Run on the LinuxONE server from the repo root:

    GRANITE_MODEL_PATH=/path/to/granite.gguf nohup uvicorn src.api:app --host 127.0.0.1 --port 8000 > data/api.log 2>&1 &

Open through the SSH tunnel (-L 8000:localhost:8000): http://localhost:8000/docs
Startup warms up account state (about 2 minutes, or seconds with data/state_warm.pkl
from `python -m src.scorer --verify`); endpoints return 503 until /api/status says ready.
"""

import itertools
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .db import Store
from .scorer import ROOT, USE_CACHE, CACHE, Scorer, cache_key, load_history, save_state, test_rows, warmed_state
from .stream import Replayer
from .templates import template_texts

try:  # card 05: explain(payload) -> {"warning_en", "warning_bm", "analyst_note", "used_granite", ...}
    from .explain import explain as granite_explain
except ImportError:
    granite_explain = None

WEB = ROOT / "web"
DEMO_SENDER = "DEMO_SENDER"
HIGH_LABELS = ["Recipient A — Online seller", "Recipient C — Investment agent", "Recipient E — Job agency"]
LOW_LABELS = ["Recipient B — Utility company", "Recipient D — Grocery store", "Recipient F — Family member"]

app_state = {"stage": "starting", "error": None, "granite_last": None}
# Granite is slow (seconds per case): sender transfers go first; replayed holds only
# when the queue is short; replayed pauses never (no sender is watching them).
granite_jobs = queue.PriorityQueue()
GRANITE_REPLAY_BACKLOG = 5
_job_order = itertools.count()


DEMO_AMOUNTS = (100, 1000, 10000)


def pick_demo_accounts(rows, scorer, clock):
    """Three receivers that stay risky and three that stay safe for a DEMO_SENDER transfer.

    Candidates come from the test period; each is checked by previewing a demo
    transfer at several amounts (nothing is recorded), because a brand-new
    sender scores differently from the real senders in the data.
    """
    scores = pd.read_pickle(ROOT / "data" / "xgb_scores.pkl")
    t = rows.join(scores["score_xgb"], how="inner")
    pause = scorer.thresholds["pause"]

    def profile(dst):
        incoming = t[t["dst"] == dst]
        return {"id": dst,
                "payment_format": incoming["payment_format"].mode().iloc[0],
                "currency": incoming["receiving_currency"].mode().iloc[0]}

    def preview_scores(account):
        return [scorer.preview({
            "ts": clock, "src": DEMO_SENDER, "dst": account["id"], "amount": a, "amount_paid": a,
            "payment_format": account["payment_format"], "receiving_currency": account["currency"],
            "payment_currency": account["currency"]}) for a in DEMO_AMOUNTS]

    risky = t[t["label"] == 1].sort_values("score_xgb", ascending=False)
    risky = risky.assign(flagged=risky["dst"].isin(scorer.state.flagged)).sort_values(
        ["flagged", "score_xgb"], ascending=False)
    per_dst = t.groupby("dst").agg(n=("label", "size"), bad=("label", "sum"), top=("score_xgb", "max"))
    safe = per_dst[(per_dst["bad"] == 0) & (per_dst["top"] < pause) & ~per_dst.index.isin(scorer.state.flagged)]

    def choose(candidates, passes, rank):
        """First 3 candidates that pass; if fewer, fill with the best-ranked of the rest."""
        chosen, rest = [], []
        for dst in candidates:
            account = profile(dst)
            previews = preview_scores(account)
            (chosen if passes(previews) else rest).append((rank(previews), account))
            if len(chosen) == 3:
                break
        if len(chosen) < 3:
            print(f"Only {len(chosen)} demo recipients passed; filling with closest candidates", flush=True)
            chosen += sorted(rest, key=lambda r: r[0])[: 3 - len(chosen)]
        return [account for _, account in chosen]

    high = choose(list(dict.fromkeys(risky["dst"]))[:60],
                  lambda p: min(p) >= pause, lambda p: -min(p))
    low = choose(safe.sort_values("n", ascending=False).index[:200],
                 lambda p: max(p) < pause, lambda p: max(p))

    accounts = [{**a, "label": label, "expected": "warn"} for label, a in zip(HIGH_LABELS, high)]
    accounts += [{**a, "label": label, "expected": "allow"} for label, a in zip(LOW_LABELS, low)]
    return sorted(accounts, key=lambda a: a["label"])


def amount_band(amount):
    return "small" if amount < 1_000 else "medium" if amount < 10_000 else "large"


def process(txn, source):
    """Score one transaction, store it, open a case if needed, queue Granite text."""
    scorer, store = app_state["scorer"], app_state["store"]
    result = scorer.score(txn)
    if result["decision"] != "allow":
        result.update(template_texts(result["decision"], result["score"], result["reasons"], result["sender_reasons"]))
    else:
        result.update(warning_en=None, warning_bm=None, analyst_note=None)
    txn_id, case_id = store.add_transaction(txn, result, source)
    result.update(txn_id=txn_id, case_id=case_id)
    wanted = source == "sender" or (result["decision"] == "hold" and granite_jobs.qsize() < GRANITE_REPLAY_BACKLOG)
    if case_id and granite_explain and wanted:
        priority = 0 if source == "sender" else 1
        # explain.py builds every text from `reasons`, and the warnings go to the
        # sender, so it gets the sender-safe list; the analyst list rides along.
        granite_jobs.put((priority, next(_job_order), case_id, {
            "decision": result["decision"], "score": result["score"],
            "amount_band": amount_band(txn["amount"]), "currency": txn["receiving_currency"],
            "reasons": result["sender_reasons"], "analyst_reasons": result["reasons"],
        }))
    return result


def granite_worker():
    while True:
        _, _, case_id, payload = granite_jobs.get()
        try:
            texts = granite_explain(payload)
            used = texts.get("used_granite", True)
            app_state["granite_last"] = {"case_id": case_id, "used_granite": used,
                                         "seconds": texts.get("generation_seconds")}
            if used:  # otherwise explain() returned its own generic fallback: keep our template
                app_state["store"].update_texts(case_id, texts, "granite")
            else:
                print(f"Granite not used for case {case_id} (model not loaded or timed out); "
                      "keeping template text", flush=True)
        except Exception as exc:  # keep the template text
            app_state["granite_last"] = {"case_id": case_id, "used_granite": False, "error": repr(exc)}
            print(f"Granite failed for case {case_id}: {exc}", flush=True)


def load():
    try:
        app_state["stage"] = "loading data"
        history, test, train_end = load_history()
        app_state["stage"] = f"warming up account state ({len(history):,} transactions)"
        key = cache_key(history, train_end)
        state = warmed_state(history, train_end)
        del history
        if USE_CACHE and not CACHE.exists():
            save_state(state, key)
        app_state["stage"] = "loading models"
        scorer = Scorer(state)
        rows = test_rows(test)
        del test
        app_state["stage"] = "choosing demo recipients"
        app_state["demo_accounts"] = pick_demo_accounts(rows, scorer, rows["ts"].iloc[0])
        app_state["store"] = Store(ROOT / "data" / "trustpause.db")
        app_state["scorer"] = scorer
        app_state["replayer"] = Replayer(rows, process)
        if granite_explain:
            threading.Thread(target=granite_worker, daemon=True).start()
        app_state["stage"] = "ready"
        print("TrustPause API ready", flush=True)
    except Exception as exc:
        app_state["stage"] = "failed"
        app_state["error"] = repr(exc)
        raise


@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=load, daemon=True).start()
    yield


app = FastAPI(title="TrustPause", lifespan=lifespan)


def ready():
    if app_state["stage"] != "ready":
        raise HTTPException(503, f"Not ready: {app_state['stage']}")
    return app_state


class TransferIn(BaseModel):
    dst: str
    amount: float = Field(gt=0)


class ReplayIn(BaseModel):
    speed: float = Field(50, ge=1, le=5000)


class ChoiceIn(BaseModel):
    choice: Literal["cancel", "continue"]


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject"]


@app.get("/api/status")
def status():
    return {"stage": app_state["stage"], "error": app_state["error"], "granite": granite_explain is not None,
            "granite_last": app_state["granite_last"]}


@app.get("/api/demo-accounts")
def demo_accounts():
    return [{"id": a["id"], "label": a["label"]} for a in ready()["demo_accounts"]]


@app.post("/api/transfer")
def transfer(body: TransferIn):
    s = ready()
    account = next((a for a in s["demo_accounts"] if a["id"] == body.dst), None)
    if account is None:
        raise HTTPException(404, "Unknown demo recipient")
    replayer = s["replayer"]
    txn = {
        "ts": replayer.clock, "src": DEMO_SENDER, "dst": body.dst,
        "amount": body.amount, "amount_paid": body.amount,
        "payment_format": account["payment_format"],
        "receiving_currency": account["currency"], "payment_currency": account["currency"],
    }
    result = process(txn, "sender")
    return {
        "txn_id": result["txn_id"], "case_id": result["case_id"], "decision": result["decision"],
        "score": round(result["score"], 4), "score_xgb": round(result["score_xgb"], 4),
        "score_seq": result["score_seq"], "latency_ms": round(result["latency_ms"], 2),
        "sender_reasons": result["sender_reasons"],
        "warning_en": result["warning_en"], "warning_bm": result["warning_bm"],
    }


@app.post("/api/transfer/{case_id}/choice")
def sender_choice(case_id: int, body: ChoiceIn):
    store = ready()["store"]
    if store.case(case_id) is None:
        raise HTTPException(404, "Unknown case")
    store.set_sender_choice(case_id, body.choice)
    return {"case_id": case_id, "choice": body.choice}


@app.post("/api/replay/start")
def replay_start(body: ReplayIn):
    replayer = ready()["replayer"]
    replayer.start(body.speed)
    return {"running": replayer.running, "speed": replayer.speed}


@app.post("/api/replay/stop")
def replay_stop():
    replayer = ready()["replayer"]
    replayer.stop()
    return {"running": False}


@app.get("/api/feed")
def feed(since: int = 0, limit: int = 50):
    rows = ready()["store"].feed(since, min(limit, 200))
    for r in rows:
        r.pop("src", None)  # account IDs stay server-side; the UI shows amounts, scores and decisions
        r.pop("dst", None)
    return rows


@app.get("/api/queue")
def review_queue():
    return ready()["store"].queue()


@app.get("/api/case/{case_id}")
def case(case_id: int):
    found = ready()["store"].case(case_id)
    if found is None:
        raise HTTPException(404, "Unknown case")
    return found


@app.post("/api/case/{case_id}/decision")
def case_decision(case_id: int, body: DecisionIn):
    if not ready()["store"].set_analyst_decision(case_id, body.decision):
        raise HTTPException(409, "Case is not waiting for review")
    return {"case_id": case_id, "decision": body.decision}


@app.get("/api/metrics")
def metrics():
    s = ready()
    replayer, store, scorer = s["replayer"], s["store"], s["scorer"]
    counts = store.counts()
    latencies = store.recent_latencies()
    return {
        **counts,
        "laundering_flagged_%": round(100 * counts["laundering_flagged"] / counts["laundering_seen"], 1)
        if counts["laundering_seen"] else None,
        "latency_ms_p50": round(float(np.percentile(latencies, 50)), 3) if latencies else None,
        "latency_ms_p95": round(float(np.percentile(latencies, 95)), 3) if latencies else None,
        "txn_per_sec": round(replayer.rate(), 1) if replayer.running else 0.0,
        "replay_running": replayer.running,
        "replay_position": replayer.pos,
        "replay_total": len(replayer.records),
        "clock": str(replayer.clock),
        "thresholds": {"pause": scorer.thresholds["pause"], "hold": scorer.thresholds["hold"]},
        "sequence_model": scorer.seq_scorer is not None,
        "granite": granite_explain is not None,
        "granite_queue": granite_jobs.qsize(),
        "granite_last": app_state["granite_last"],
    }


def _page(name):
    path = WEB / name
    if path.exists():
        return FileResponse(path)
    return HTMLResponse(f"<p>{name} is not built yet (work card 07). API docs: <a href='/docs'>/docs</a></p>")


@app.get("/")
def index():
    return HTMLResponse("<h1>TrustPause</h1><ul><li><a href='/sender'>Sender view</a></li>"
                        "<li><a href='/analyst'>Analyst view</a></li><li><a href='/docs'>API docs</a></li></ul>")


@app.get("/sender")
def sender_page():
    return _page("sender.html")


@app.get("/analyst")
def analyst_page():
    return _page("analyst.html")


@app.get("/web/{name}")
def web_asset(name: str):
    path = (WEB / name).resolve()
    if path.parent != WEB.resolve() or not path.exists():
        raise HTTPException(404)
    return FileResponse(path)
