from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional

from .metrics import increment


@contextmanager
def span(
    name: str,
    correlation_id: Optional[str] = None,
) -> Generator[dict, None, None]:

    started = time.perf_counter()

    context = {
        "name": name,
        "correlation_id": correlation_id,
    }

    try:
        yield context

    except Exception:
        increment(
            f"trace.{name}.errors"
        )
        raise

    finally:
        elapsed = (
            time.perf_counter()
            - started
        )

        increment(
            f"trace.{name}.calls"
        )

        context["duration_seconds"] = elapsed


def trace(
    fn: Callable[..., Any],
):

    @functools.wraps(fn)
    def wrapper(
        *args,
        **kwargs,
    ):

        correlation_id = kwargs.get(
            "correlation_id"
        )

        with span(
            fn.__name__,
            correlation_id,
        ):
            return fn(
                *args,
                **kwargs,
            )

    return wrapper
