import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque

from ..exceptions import RateLimitExceededError


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    name: str
    max_requests: int
    window_seconds: int


LOGIN_RATE_LIMIT_POLICY = RateLimitPolicy(
    name="auth_login",
    max_requests=5,
    window_seconds=60,
)
CALLBACK_RATE_LIMIT_POLICY = RateLimitPolicy(
    name="auth_callback",
    max_requests=5,
    window_seconds=60,
)
REFRESH_RATE_LIMIT_POLICY = RateLimitPolicy(
    name="auth_refresh",
    max_requests=10,
    window_seconds=60,
)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[tuple[str, str], Deque[float]] = defaultdict(deque)

    def check(self, policy: RateLimitPolicy, key: str) -> None:
        now = time.monotonic()
        request_times = self._requests[(policy.name, key)]
        window_start = now - policy.window_seconds

        # Drop any timestamps that are older than the current rate-limit window
        # so the deque only represents recent requests for this policy/key pair.
        # Example: with a 60-second window at t=125, any request at t<=65 is
        # irrelevant to the current decision and can be discarded.
        while request_times and request_times[0] <= window_start:
            request_times.popleft()

        # If the remaining in-window requests already fill the quota, reject this
        # attempt and tell the caller roughly when the oldest request will age out.
        # Example: for a 5-requests-per-60-seconds policy, if the deque still
        # holds 5 timestamps after pruning, the 6th request is rejected.
        if len(request_times) >= policy.max_requests:
            retry_after = max(
                1,
                math.ceil(request_times[0] + policy.window_seconds - now),
            )
            raise RateLimitExceededError(retry_after=retry_after)

        # Record the current request only after we know it fits inside the policy.
        # Example: if 4 requests remain in the deque for a 5-request policy,
        # appending `now` consumes the final available slot.
        request_times.append(now)

    def reset(self) -> None:
        self._requests.clear()


_auth_rate_limiter = InMemoryRateLimiter()


def get_auth_rate_limiter() -> InMemoryRateLimiter:
    return _auth_rate_limiter


def reset_auth_rate_limiter() -> None:
    _auth_rate_limiter.reset()
