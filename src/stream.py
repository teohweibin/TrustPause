"""Replay test-period transactions in time order at a chosen speed."""

import threading
import time


class Replayer:
    def __init__(self, rows, process):
        """rows: DataFrame from scorer.test_rows; process: callable(txn dict, source) -> result."""
        self.records = rows.to_dict("records")
        self.process = process
        self.pos = 0
        self.speed = 50.0
        self.thread = None
        self.stop_event = threading.Event()
        self.started_at = None
        self.processed_since_start = 0

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    @property
    def clock(self):
        """Simulated 'now': timestamp of the latest replayed transaction (or the first one before starting)."""
        return self.records[max(self.pos - 1, 0)]["ts"] if self.records else None

    def start(self, speed=50.0):
        self.speed = max(float(speed), 1.0)
        if self.running:
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def rate(self):
        if not self.started_at:
            return 0.0
        return self.processed_since_start / max(time.time() - self.started_at, 1e-6)

    def _run(self):
        self.started_at = time.time()
        self.processed_since_start = 0
        next_at = time.perf_counter()
        while not self.stop_event.is_set() and self.pos < len(self.records):
            self.process(self.records[self.pos], "replay")
            self.pos += 1
            self.processed_since_start += 1
            next_at += 1.0 / self.speed
            delay = next_at - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            elif delay < -1.0:
                next_at = time.perf_counter()  # fell behind; don't burst to catch up
