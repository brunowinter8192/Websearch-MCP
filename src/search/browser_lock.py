# INFRASTRUCTURE
import fcntl
import json
import os
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

_TS_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
POLL_INTERVAL_S = 0.25


# A held cross-process lock; released via release()
class LockHandle:
    def __init__(self, fd, sidecar_path: Path):
        self._fd = fd
        self._sidecar_path = sidecar_path

    def release(self) -> None:
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        self._fd.close()
        self._sidecar_path.unlink(missing_ok=True)


# FUNCTIONS

# Blocking acquire: polls a non-blocking flock; a sidecar older than hard_budget_s is presumed
# stuck (not just slow) and force-broken — on_stale runs first (e.g. to reap orphaned children of
# the presumed-stuck holder), then a fresh inode is opened at the same path (flock is inode-bound,
# so this bypasses the old holder's still-technically-held lock on the now-unlinked file) and
# acquire is retried. Returns once this process holds the lock.
def acquire(lock_path: Path, hard_budget_s: float, on_stale: Callable[[], None] | None = None) -> LockHandle:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path = lock_path.with_suffix(".json")
    while True:
        fd = open(lock_path, "a")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _write_sidecar(sidecar_path)
            return LockHandle(fd, sidecar_path)
        except BlockingIOError:
            fd.close()
        age = _sidecar_age_s(sidecar_path)
        if age is not None and age > hard_budget_s:
            if on_stale is not None:
                on_stale()
            _break_lock(lock_path, sidecar_path)
            continue
        time.sleep(POLL_INTERVAL_S)


# Write {"pid", "started_at"} sidecar for the just-acquired lock
def _write_sidecar(sidecar_path: Path) -> None:
    sidecar_path.write_text(json.dumps({
        "pid": os.getpid(),
        "started_at": datetime.now(timezone.utc).strftime(_TS_FMT),
    }))


# Age in seconds of the current holder's sidecar; None if missing/unreadable (treated as not-stale)
def _sidecar_age_s(sidecar_path: Path) -> float | None:
    try:
        data = json.loads(sidecar_path.read_text())
        started = datetime.strptime(data["started_at"], _TS_FMT).replace(tzinfo=timezone.utc)
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None
    return (datetime.now(timezone.utc) - started).total_seconds()


# Force-break a stale lock — see acquire()'s docstring for why unlink+recreate works
def _break_lock(lock_path: Path, sidecar_path: Path) -> None:
    lock_path.unlink(missing_ok=True)
    sidecar_path.unlink(missing_ok=True)
