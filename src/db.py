"""SQLite store for scored transactions and review cases."""

import json
import sqlite3
import threading
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT, src TEXT, dst TEXT, amount REAL, payment_format TEXT, currency TEXT,
    score_xgb REAL, score_seq REAL, score REAL, decision TEXT,
    reasons_json TEXT, latency_ms REAL, source TEXT, label INTEGER
);
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id INTEGER REFERENCES transactions(id),
    status TEXT,
    warning_en TEXT, warning_bm TEXT, analyst_note TEXT, text_source TEXT,
    sender_reasons_json TEXT,
    sender_choice TEXT, analyst_decision TEXT, decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    """Thin thread-safe wrapper; the API, replay thread and Granite worker share one connection."""

    def __init__(self, path, reset=True):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.lock:
            # Demo data: favour speed over durability so replay isn't limited by disk syncs.
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=OFF")
            if reset:
                self.conn.executescript("DROP TABLE IF EXISTS cases; DROP TABLE IF EXISTS transactions;")
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    def _rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def add_transaction(self, txn, result, source):
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO transactions (ts, src, dst, amount, payment_format, currency, score_xgb, score_seq,"
                " score, decision, reasons_json, latency_ms, source, label) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (str(txn["ts"]), txn["src"], txn["dst"], txn["amount"], txn["payment_format"],
                 txn["receiving_currency"], result["score_xgb"], result["score_seq"], result["score"],
                 result["decision"], json.dumps(result["reasons"]), result["latency_ms"], source,
                 txn.get("label")),
            )
            txn_id = cur.lastrowid
            case_id = None
            if result["decision"] in ("pause", "hold"):
                cur = self.conn.execute(
                    "INSERT INTO cases (txn_id, status, warning_en, warning_bm, analyst_note, text_source,"
                    " sender_reasons_json) VALUES (?,?,?,?,?,?,?)",
                    (txn_id, "paused" if result["decision"] == "pause" else "held",
                     result["warning_en"], result["warning_bm"], result["analyst_note"], "template",
                     json.dumps(result["sender_reasons"])),
                )
                case_id = cur.lastrowid
            self.conn.commit()
        return txn_id, case_id

    def update_texts(self, case_id, texts, source):
        with self.lock:
            self.conn.execute(
                "UPDATE cases SET warning_en=?, warning_bm=?, analyst_note=?, text_source=? WHERE id=?",
                (texts["warning_en"], texts["warning_bm"], texts["analyst_note"], source, case_id),
            )
            self.conn.commit()

    def set_sender_choice(self, case_id, choice):
        with self.lock:
            self.conn.execute("UPDATE cases SET sender_choice=? WHERE id=?", (choice, case_id))
            self.conn.commit()

    def set_analyst_decision(self, case_id, decision):
        status = "approved" if decision == "approve" else "rejected"
        with self.lock:
            cur = self.conn.execute(
                "UPDATE cases SET status=?, analyst_decision=?, decided_at=? WHERE id=? AND status='held'",
                (status, decision, _now(), case_id),
            )
            self.conn.commit()
            return cur.rowcount == 1

    def feed(self, since=0, limit=50):
        rows = self._rows(
            "SELECT t.*, c.id AS case_id FROM transactions t LEFT JOIN cases c ON c.txn_id = t.id"
            " WHERE t.id > ? ORDER BY t.id DESC LIMIT ?", (since, limit))
        for r in rows:
            r["reasons"] = json.loads(r.pop("reasons_json") or "[]")
        return rows

    def queue(self, limit=50):
        rows = self._rows(
            "SELECT c.id AS case_id, c.status, c.text_source, t.id AS txn_id, t.ts, t.amount, t.currency,"
            " t.score, t.reasons_json FROM cases c JOIN transactions t ON t.id = c.txn_id"
            " WHERE c.status = 'held' ORDER BY c.id DESC LIMIT ?", (limit,))
        for r in rows:
            reasons = json.loads(r.pop("reasons_json") or "[]")
            r["first_reason"] = reasons[0]["sentence"] if reasons else None
        return rows

    def case(self, case_id):
        rows = self._rows(
            "SELECT c.*, t.ts, t.src, t.dst, t.amount, t.currency, t.payment_format, t.score_xgb, t.score_seq,"
            " t.score, t.decision, t.reasons_json, t.latency_ms, t.source, t.label"
            " FROM cases c JOIN transactions t ON t.id = c.txn_id WHERE c.id = ?", (case_id,))
        if not rows:
            return None
        r = rows[0]
        r["reasons"] = json.loads(r.pop("reasons_json") or "[]")
        r["sender_reasons"] = json.loads(r.pop("sender_reasons_json") or "[]")
        return r

    def counts(self):
        rows = self._rows(
            "SELECT decision, COUNT(*) AS n, SUM(label = 1) AS laundering FROM transactions"
            " WHERE source = 'replay' GROUP BY decision")
        total_laundering = self._rows("SELECT COUNT(*) AS n FROM transactions WHERE source='replay' AND label=1")[0]["n"]
        out = {"allow": 0, "pause": 0, "hold": 0, "laundering_seen": total_laundering, "laundering_flagged": 0}
        for r in rows:
            out[r["decision"]] = r["n"]
            if r["decision"] in ("pause", "hold"):
                out["laundering_flagged"] += r["laundering"] or 0
        return out

    def recent_latencies(self, n=1000):
        return [r["latency_ms"] for r in self._rows("SELECT latency_ms FROM transactions ORDER BY id DESC LIMIT ?", (n,))]
