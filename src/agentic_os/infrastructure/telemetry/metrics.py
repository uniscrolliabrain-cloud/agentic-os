from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Dict


_lock = RLock()
_metrics: Dict[str, float] = defaultdict(float)


def metric(
    name: str,
    value: float = 1,
) -> None:

    if not name:
        return

    with _lock:
        _metrics[name] += float(value)


def increment(
    name: str,
    value: float = 1,
) -> None:
    metric(name, value)


def get_metrics() -> Dict[str, float]:

    with _lock:
        return dict(_metrics)


def reset_metrics() -> None:

    with _lock:
        _metrics.clear()
