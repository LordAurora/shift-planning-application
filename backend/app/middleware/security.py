"""
Security Middleware - Headers, Token Validation, Request Signing.
"""
import time
import hmac
import hashlib
import secrets
from typing import Optional, Dict, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (adjust based on your needs)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http: https:;"
        )
        
        # HSTS (enable in production with HTTPS)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class TokenBlacklist:
    """
    In-memory token blacklist for revoked tokens.
    In production, use Redis for distributed blacklist.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._blacklist: Set[str] = set()
        self._expiry: Dict[str, datetime] = {}
    
    def add(self, token_jti: str, expires_at: datetime):
        """Add token to blacklist"""
        if self.redis:
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl > 0:
                self.redis.setex(f"blacklist:{token_jti}", ttl, "1")
        else:
            self._blacklist.add(token_jti)
            self._expiry[token_jti] = expires_at
    
    def is_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        if self.redis:
            return self.redis.exists(f"blacklist:{token_jti}")
        
        if token_jti not in self._blacklist:
            return False
        
        # Check expiry
        if self._expiry.get(token_jti, datetime.min) < datetime.utcnow():
            self._blacklist.discard(token_jti)
            self._expiry.pop(token_jti, None)
            return False
        
        return True
    
    def cleanup(self):
        """Remove expired entries"""
        if self.redis:
            return  # Redis handles expiry
        
        now = datetime.utcnow()
        expired = [jti for jti, exp in self._expiry.items() if exp < now]
        for jti in expired:
            self._blacklist.discard(jti)
            self._expiry.pop(jti, None)


# Global blacklist instance
token_blacklist = TokenBlacklist()


class TokenRotationManager:
    """
    Manages token rotation for enhanced security.
    Supports refresh token rotation and grace periods.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._used_refresh_tokens: Dict[str, datetime] = {}
        self.grace_period = timedelta(seconds=30)  # Allow old token for 30s after rotation
    
    def mark_token_used(self, token_jti: str, new_token_jti: str):
        """Mark refresh token as used and record new token"""
        now = datetime.utcnow()
        
        if self.redis:
            # Store mapping with short TTL for grace period
            self.redis.setex(
                f"token_rotation:{token_jti}",
                int(self.grace_period.total_seconds()),
                new_token_jti
            )
        else:
            self._used_refresh_tokens[token_jti] = now
    
    def check_rotation(self, token_jti: str) -> tuple[bool, Optional[str]]:
        """
        Check if token has been rotated.
        Returns (is_valid, new_token_jti if available)
        """
        if self.redis:
            new_jti = self.redis.get(f"token_rotation:{token_jti}")
            if new_jti:
                return False, new_jti.decode() if isinstance(new_jti, bytes) else new_jti
            return True, None
        
        if token_jti in self._used_refresh_tokens:
            used_at = self._used_refresh_tokens[token_jti]
            if datetime.utcnow() - used_at < self.grace_period:
                # Within grace period - allow but warn
                logger.warning(f"Token {token_jti[:8]}... used within grace period")
                return True, None
            return False, None
        
        return True, None


# Global rotation manager
token_rotation_manager = TokenRotationManager()


class RequestSigningMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request signing verification.
    Used for high-security endpoints and API-to-API communication.
    """
    
    SIGNED_ENDPOINTS = {"/api/v1/admin/", "/api/v1/system/"}
    
    def __init__(self, app, signing_key: str = None):
        super().__init__(app)
        self.signing_key = signing_key or secrets.token_hex(32)
        self.time_tolerance = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check if endpoint requires signing
        if not self._requires_signing(request.url.path):
            return await call_next(request)
        
        # Verify signature
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")
        
        if not signature or not timestamp:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing signature or timestamp"}
            )
        
        # Verify timestamp is recent
        try:
            req_time = int(timestamp)
            if abs(time.time() - req_time) > self.time_tolerance:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Request timestamp expired"}
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid timestamp format"}
            )
        
        # Verify signature
        body = await request.body()
        expected_signature = self._compute_signature(
            request.method,
            request.url.path,
            timestamp,
            body
        )
        
        if not hmac.compare_digest(signature, expected_signature):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid signature"}
            )
        
        return await call_next(request)
    
    def _requires_signing(self, path: str) -> bool:
        """Check if path requires request signing"""
        return any(path.startswith(ep) for ep in self.SIGNED_ENDPOINTS)
    
    def _compute_signature(
        self,
        method: str,
        path: str,
        timestamp: str,
        body: bytes
    ) -> str:
        """Compute HMAC-SHA256 signature"""
        message = f"{method}:{path}:{timestamp}:{body.decode()}"
        return hmac.new(
            self.signing_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def sign_request(
        method: str,
        path: str,
        body: str,
        signing_key: str
    ) -> Dict[str, str]:
        """
        Utility to sign a request (for clients).
        Returns headers to include in request.
        """
        timestamp = str(int(time.time()))
        message = f"{method}:{path}:{timestamp}:{body}"
        signature = hmac.new(
            signing_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(length)


def hash_password_with_pepper(password: str, salt: str, pepper: str) -> str:
    """
    Hash password with salt and pepper for enhanced security.
    Pepper is a secret key stored in environment, not database.
    """
    # First round with salt
    salted = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    )
    # Second round with pepper
    peppered = hmac.new(
        pepper.encode(),
        salted,
        hashlib.sha256
    ).hexdigest()
    
    return peppered
