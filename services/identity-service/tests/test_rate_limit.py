import pytest
from app.core.rate_limit import InMemoryRateLimiter
from shared.core.exceptions import RateLimitExceededException


def test_rate_limiter_exceeded():
    limiter = InMemoryRateLimiter(requests_per_minute=3)
    key = "192.168.1.50"

    # 3 allowed requests
    limiter.check_rate_limit(key)
    limiter.check_rate_limit(key)
    limiter.check_rate_limit(key)

    # 4th request should raise RateLimitExceededException
    with pytest.raises(RateLimitExceededException):
        limiter.check_rate_limit(key)

