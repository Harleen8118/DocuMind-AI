"""Redis-based rate limiting middleware."""

import logging
import time

import redis.asyncio as redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window counters.

    Limits requests per user (authenticated) or per IP (anonymous).
    """

    def __init__(self, app, redis_url: str | None = None, requests_per_minute: int = 60):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.requests_per_minute = requests_per_minute
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed for rate limiting: {e}")
                self._redis = None
                raise
        return self._redis

    def _get_client_identifier(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try to get user ID from auth header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # Use a hash of the token as identifier
            token = auth_header[7:]
            return f"user:{hash(token) % 10**10}"

        # Fall back to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and docs
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        try:
            redis_client = await self._get_redis()
        except Exception:
            # If Redis is unavailable, let request through
            return await call_next(request)

        client_id = self._get_client_identifier(request)
        key = f"rate_limit:{client_id}"
        window = 60  # 1 minute window

        try:
            # Use Redis pipeline for atomic operations
            current_time = time.time()
            window_start = current_time - window

            pipe = redis_client.pipeline()
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            # Count requests in window
            pipe.zcard(key)
            # Set expiry on key
            pipe.expire(key, window)
            results = await pipe.execute()

            request_count = results[2]

            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.requests_per_minute - request_count)
            )
            response.headers["X-RateLimit-Reset"] = str(int(current_time + window))

            if request_count > self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": window,
                    },
                    headers={
                        "Retry-After": str(window),
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            return response

        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
            return await call_next(request)
