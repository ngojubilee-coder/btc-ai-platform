"""Simple in-memory rate limiter middleware."""
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

_request_counts: dict[str, list[float]] = defaultdict(list)
WINDOW_SECONDS = 60
MAX_REQUESTS = 100
_CLEANUP_THRESHOLD = 200


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        timestamps = _request_counts[client_ip]
        _request_counts[client_ip] = [t for t in timestamps if now - t < WINDOW_SECONDS]
        if len(_request_counts[client_ip]) >= MAX_REQUESTS:
            return Response(
                content='{"error": "Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )
        _request_counts[client_ip].append(now)

        if len(_request_counts) > _CLEANUP_THRESHOLD:
            stale = [ip for ip, ts in _request_counts.items() if not ts or now - ts[-1] > WINDOW_SECONDS]
            for ip in stale:
                del _request_counts[ip]

        return await call_next(request)
