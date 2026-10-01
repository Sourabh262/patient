import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from app.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter protecting public endpoints against abuse."""

    def __init__(self, app, max_requests: int = 120, window_sec: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_sec = window_sec
        self.requests_log = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        # Exclude internal health checks from throttling
        if request.url.path in ("/health", "/api/v1/health", "/"):
            return await call_next(request)

        current_time = time.time()
        timestamps = self.requests_log[client_ip]

        # Clean old timestamps
        self.requests_log[client_ip] = [ts for ts in timestamps if current_time - ts < self.window_sec]

        if len(self.requests_log[client_ip]) >= self.max_requests:
            logger.warning("Rate limit exceeded for client %s on %s", client_ip, request.url.path)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Request rate limit exceeded. Please wait before retrying.",
            )

        self.requests_log[client_ip].append(current_time)
        return await call_next(request)
