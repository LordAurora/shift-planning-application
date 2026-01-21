"""
Rate Limiting Middleware - Token bucket algorithm with Redis support.
"""
import time
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Allow burst above normal rate
    # Specific limits for sensitive endpoints
    auth_attempts_per_minute: int = 5
    ai_requests_per_hour: int = 50


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: float
    tokens: float = field(default=0.0)
    last_update: float = field(default_factory=time.time)
    refill_rate: float = 1.0  # Tokens per second
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def time_until_available(self, tokens: int = 1) -> float:
        """Calculate seconds until tokens are available"""
        if self.tokens >= tokens:
            return 0
        return (tokens - self.tokens) / self.refill_rate


class RateLimiter:
    """
    Rate limiter with multiple strategies.
    Can use in-memory or Redis for distributed systems.
    """
    
    def __init__(self, config: RateLimitConfig = None, redis_client=None):
        self.config = config or RateLimitConfig()
        self.redis = redis_client
        
        # In-memory buckets (key -> TokenBucket)
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        
        # Cleanup task
        self._cleanup_interval = 300  # 5 minutes
        
    def _get_bucket_key(self, identifier: str, endpoint_type: str = "default") -> str:
        """Generate bucket key"""
        return f"ratelimit:{endpoint_type}:{identifier}"
    
    async def is_allowed(
        self,
        identifier: str,
        endpoint_type: str = "default",
        cost: int = 1
    ) -> tuple[bool, Dict]:
        """
        Check if request is allowed.
        Returns (allowed, metadata with limit info)
        """
        key = self._get_bucket_key(identifier, endpoint_type)
        
        # Get rate limit for endpoint type
        if endpoint_type == "auth":
            capacity = self.config.auth_attempts_per_minute
            refill_rate = capacity / 60.0
        elif endpoint_type == "ai":
            capacity = self.config.ai_requests_per_hour
            refill_rate = capacity / 3600.0
        else:
            capacity = self.config.requests_per_minute + self.config.burst_size
            refill_rate = self.config.requests_per_minute / 60.0
        
        if self.redis:
            return await self._check_redis(key, capacity, refill_rate, cost)
        else:
            return await self._check_memory(key, capacity, refill_rate, cost)
    
    async def _check_memory(
        self,
        key: str,
        capacity: float,
        refill_rate: float,
        cost: int
    ) -> tuple[bool, Dict]:
        """Check rate limit using in-memory storage"""
        async with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    capacity=capacity,
                    tokens=capacity,
                    refill_rate=refill_rate
                )
            
            bucket = self._buckets[key]
            allowed = bucket.consume(cost)
            
            return allowed, {
                "remaining": int(bucket.tokens),
                "limit": int(capacity),
                "reset_in": bucket.time_until_available(cost) if not allowed else 0
            }
    
    async def _check_redis(
        self,
        key: str,
        capacity: float,
        refill_rate: float,
        cost: int
    ) -> tuple[bool, Dict]:
        """Check rate limit using Redis (for distributed systems)"""
        # Sliding window implementation with Redis
        now = time.time()
        window_start = now - 60  # 1-minute window
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add new entry
        pipe.zadd(key, {str(now): now})
        # Set expiry
        pipe.expire(key, 120)
        
        results = await pipe.execute()
        current_count = results[1]
        
        allowed = current_count < capacity
        
        return allowed, {
            "remaining": max(0, int(capacity - current_count - cost)),
            "limit": int(capacity),
            "reset_in": 60  # Window size
        }
    
    async def cleanup(self):
        """Remove stale buckets from memory"""
        if self.redis:
            return  # Redis handles expiry
        
        now = time.time()
        stale_threshold = 3600  # 1 hour
        
        async with self._lock:
            stale_keys = [
                key for key, bucket in self._buckets.items()
                if now - bucket.last_update > stale_threshold
            ]
            for key in stale_keys:
                del self._buckets[key]
        
        logger.debug(f"Cleaned up {len(stale_keys)} stale rate limit buckets")


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to all requests.
    """
    
    # Endpoints with special rate limiting
    AUTH_ENDPOINTS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh"}
    AI_ENDPOINTS = {"/api/v1/ai/optimize", "/api/v1/ai/suggest", "/api/v1/ai/analyze"}
    
    # Endpoints exempt from rate limiting
    EXEMPT_ENDPOINTS = {"/health", "/metrics", "/docs", "/openapi.json"}
    
    def __init__(self, app, limiter: RateLimiter = None):
        super().__init__(app)
        self.limiter = limiter or rate_limiter
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip exempt endpoints
        if request.url.path in self.EXEMPT_ENDPOINTS:
            return await call_next(request)
        
        # Get identifier (IP or user ID)
        identifier = self._get_identifier(request)
        
        # Determine endpoint type
        endpoint_type = self._get_endpoint_type(request.url.path)
        
        # Check rate limit
        allowed, metadata = await self.limiter.is_allowed(
            identifier,
            endpoint_type
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.url.path}",
                extra={"identifier": identifier, "endpoint_type": endpoint_type}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": metadata["reset_in"]
                },
                headers={
                    "Retry-After": str(int(metadata["reset_in"])),
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user ID from auth header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Use token hash as identifier for authenticated users
            # This provides per-user rate limiting
            import hashlib
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:16]
            return f"user:{token_hash}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        return f"ip:{request.client.host if request.client else 'unknown'}"
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting"""
        if path in self.AUTH_ENDPOINTS:
            return "auth"
        if any(path.startswith(ep.rstrip("/")) for ep in self.AI_ENDPOINTS):
            return "ai"
        return "default"
