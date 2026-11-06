"""Simple thread-safe in-memory rate limiter for authentication endpoints."""
import time
from collections import defaultdict
from typing import Dict, List
from shared.core.exceptions import RateLimitExceededException


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, key: str) -> None:
        """Checks if key (e.g. client IP or username) has exceeded the rate limit."""
        now = time.time()
        window_start = now - 60.0

        # Prune timestamps older than 60 seconds
        self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]

        if len(self.requests[key]) >= self.requests_per_minute:
            raise RateLimitExceededException(
                message=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed."
            )

        self.requests[key].append(now)


auth_rate_limiter = InMemoryRateLimiter(requests_per_minute=10)

