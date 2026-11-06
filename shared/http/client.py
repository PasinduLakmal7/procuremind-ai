"""Resilient HTTP client configuration and factory."""
from typing import Optional
import httpx


def create_service_http_client(
    base_url: Optional[str] = None,
    timeout_seconds: float = 10.0,
    correlation_id: Optional[str] = None
) -> httpx.AsyncClient:
    """Creates an async HTTP client configured with timeouts and correlation headers."""
    headers = {"Content-Type": "application/json"}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    return httpx.AsyncClient(
        base_url=base_url or "",
        timeout=httpx.Timeout(timeout_seconds, connect=5.0),
        headers=headers,
        follow_redirects=True,
    )

