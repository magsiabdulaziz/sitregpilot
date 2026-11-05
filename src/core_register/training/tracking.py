"""Run manifests (methodology section 12): provenance, environment, timing and peak memory."""

from __future__ import annotations

import importlib.metadata
import os
import platform
import subprocess
import threading
import time
from datetime import UTC, datetime
from typing import Any

import psutil


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()

    # dirty = modified tracked files, or untracked files under the code/config paths that a run can import or read
    tracked = run("status", "--porcelain", "--untracked-files=no")
    untracked = run("status", "--porcelain", "--untracked-files=all", "--", "src", "configs", "scripts", "schemas")
    return {"commit": run("rev-parse", "HEAD"), "branch": run("branch", "--show-current"),
            "dirty": bool(tracked or untracked)}


def environment() -> dict[str, Any]:
    pkgs = ("numpy", "scipy", "scikit-learn", "pandas", "pyarrow", "spacy", "joblib")
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_logical": psutil.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "packages": {p: importlib.metadata.version(p) for p in pkgs},
        "thread_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
    }


class RunTimer:
    """Wall time plus peak RSS of this process and its children (sampled every 0.5 s)."""

    def __init__(self) -> None:
        self.peak = 0
        self._stop = threading.Event()
        self._proc = psutil.Process()
        self._t = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self._stop.is_set():
            try:
                rss = self._proc.memory_info().rss + sum(c.memory_info().rss for c in self._proc.children(True))
                self.peak = max(self.peak, rss)
            except psutil.Error:
                pass
            time.sleep(0.5)

    def __enter__(self) -> RunTimer:
        self.started = datetime.now(UTC).isoformat(timespec="seconds")
        self._t0 = time.perf_counter()
        self._t.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._t.join()
        self.seconds = round(time.perf_counter() - self._t0, 1)
        self.ended = datetime.now(UTC).isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return {"started_utc": self.started, "ended_utc": self.ended, "seconds": self.seconds,
                "peak_rss_mb": round(self.peak / 2**20)}
