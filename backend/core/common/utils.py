import inspect
from datetime import datetime, timezone
from functools import wraps
from time import perf_counter
from typing import Any, Callable, ParamSpec, TypeVar, cast

from loguru import logger


def get_current_timestamp_seconds() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_current_timestamp_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_current_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


P = ParamSpec("P")
R = TypeVar("R")


def time_it(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to time the execution of a function.
    """
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = perf_counter()
            try:
                return await cast(Callable[P, Any], func)(*args, **kwargs)  # type: ignore[no-any-return]
            finally:
                end_time = perf_counter()
                logger.info(f"{func.__name__} took {end_time - start_time:.6f} seconds")

        return cast(Callable[P, R], async_wrapper)

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            end_time = perf_counter()
            logger.info(f"{func.__name__} took {end_time - start_time:.6f} seconds")

    return sync_wrapper
