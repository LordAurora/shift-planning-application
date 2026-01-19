"""
Health Check and Observability Endpoints.
"""
from fastapi import APIRouter, Depends, Response
from typing import Dict, Any, Optional
from datetime import datetime
import time
import logging
import os
import psutil

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


# ============== Health Check Models ==============

def get_system_info() -> Dict[str, Any]:
    """Get system resource information"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 1)
            }
        }
    except Exception:
        return {"error": "Unable to get system info"}


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        start_time = time.time()
        
        try:
            db.execute(text("SELECT 1"))
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2)
            }
        finally:
            db.close()
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, socket_connect_timeout=2)
        
        start_time = time.time()
        client.ping()
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2)
        }
    except ImportError:
        return {"status": "not_configured", "message": "Redis not installed"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_celery_health() -> Dict[str, Any]:
    """Check Celery workers"""
    try:
        from app.tasks.celery_app import check_celery_health as celery_health
        return celery_health()
    except ImportError:
        return {"status": "not_configured", "message": "Celery not installed"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============== Endpoints ==============

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    Use for load balancer health checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "shiftmaster-api",
        "version": os.getenv("APP_VERSION", "1.0.0")
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Verifies all dependencies are available.
    Use for Kubernetes readiness probes.
    """
    db_health = await check_database_health()
    
    # Service is ready only if database is healthy
    is_ready = db_health["status"] == "healthy"
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_health
        }
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    Verifies the service is responsive.
    Use for Kubernetes liveness probes.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with all dependencies.
    Includes performance metrics.
    """
    start_time = time.time()
    
    # Run all checks in parallel would be better, but keeping simple
    db_health = await check_database_health()
    redis_health = await check_redis_health()
    celery_health = await check_celery_health()
    system_info = get_system_info()
    
    total_time_ms = (time.time() - start_time) * 1000
    
    # Determine overall health
    all_healthy = (
        db_health.get("status") == "healthy" and
        (redis_health.get("status") in ["healthy", "not_configured"]) and
        (celery_health.get("status") in ["healthy", "not_configured", "degraded"])
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "shiftmaster-api",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {
            "database": db_health,
            "redis": redis_health,
            "celery": celery_health
        },
        "system": system_info,
        "check_duration_ms": round(total_time_ms, 2)
    }


# ============== Metrics Endpoint ==============

# Simple in-memory metrics (replace with Prometheus in production)
_metrics = {
    "requests_total": 0,
    "requests_by_status": {},
    "requests_by_endpoint": {},
    "errors_total": 0,
    "response_times": []
}


def record_request(status_code: int, endpoint: str, duration_ms: float):
    """Record a request metric"""
    _metrics["requests_total"] += 1
    
    status_key = str(status_code)
    _metrics["requests_by_status"][status_key] = \
        _metrics["requests_by_status"].get(status_key, 0) + 1
    
    _metrics["requests_by_endpoint"][endpoint] = \
        _metrics["requests_by_endpoint"].get(endpoint, 0) + 1
    
    if status_code >= 400:
        _metrics["errors_total"] += 1
    
    # Keep last 1000 response times
    _metrics["response_times"].append(duration_ms)
    if len(_metrics["response_times"]) > 1000:
        _metrics["response_times"] = _metrics["response_times"][-1000:]


@router.get("/metrics")
async def get_metrics(response: Response) -> str:
    """
    Prometheus-compatible metrics endpoint.
    """
    # Calculate percentiles
    response_times = sorted(_metrics["response_times"]) if _metrics["response_times"] else [0]
    p50 = response_times[len(response_times) // 2]
    p95 = response_times[int(len(response_times) * 0.95)]
    p99 = response_times[int(len(response_times) * 0.99)]
    
    # Format as Prometheus metrics
    lines = [
        "# HELP http_requests_total Total number of HTTP requests",
        "# TYPE http_requests_total counter",
        f"http_requests_total {_metrics['requests_total']}",
        "",
        "# HELP http_errors_total Total number of HTTP errors",
        "# TYPE http_errors_total counter",
        f"http_errors_total {_metrics['errors_total']}",
        "",
        "# HELP http_request_duration_ms HTTP request duration in milliseconds",
        "# TYPE http_request_duration_ms summary",
        f'http_request_duration_ms{{quantile="0.5"}} {p50}',
        f'http_request_duration_ms{{quantile="0.95"}} {p95}',
        f'http_request_duration_ms{{quantile="0.99"}} {p99}',
        "",
    ]
    
    # Add per-status metrics
    lines.append("# HELP http_requests_by_status_total HTTP requests by status code")
    lines.append("# TYPE http_requests_by_status_total counter")
    for status, count in _metrics["requests_by_status"].items():
        lines.append(f'http_requests_by_status_total{{status="{status}"}} {count}')
    
    lines.append("")
    
    # System metrics
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        lines.extend([
            "# HELP process_cpu_percent CPU usage percentage",
            "# TYPE process_cpu_percent gauge",
            f"process_cpu_percent {cpu}",
            "",
            "# HELP process_memory_bytes Memory usage in bytes",
            "# TYPE process_memory_bytes gauge",
            f"process_memory_bytes {psutil.Process().memory_info().rss}",
            "",
            "# HELP system_memory_percent System memory usage percentage",
            "# TYPE system_memory_percent gauge",
            f"system_memory_percent {memory.percent}",
        ])
    except Exception:
        pass
    
    response.headers["Content-Type"] = "text/plain; version=0.0.4"
    return "\n".join(lines)


@router.get("/metrics/json")
async def get_metrics_json() -> Dict[str, Any]:
    """
    JSON format metrics for non-Prometheus consumers.
    """
    response_times = _metrics["response_times"]
    
    if response_times:
        sorted_times = sorted(response_times)
        avg_time = sum(sorted_times) / len(sorted_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
    else:
        avg_time = p50 = p95 = p99 = 0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "requests": {
            "total": _metrics["requests_total"],
            "errors": _metrics["errors_total"],
            "error_rate": round(_metrics["errors_total"] / max(_metrics["requests_total"], 1) * 100, 2),
            "by_status": _metrics["requests_by_status"],
            "by_endpoint": dict(sorted(
                _metrics["requests_by_endpoint"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20])  # Top 20 endpoints
        },
        "response_times_ms": {
            "average": round(avg_time, 2),
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "samples": len(response_times)
        },
        "system": get_system_info()
    }


# ============== Info Endpoint ==============

@router.get("/info")
async def get_info() -> Dict[str, Any]:
    """
    Get service information.
    """
    return {
        "service": "shiftmaster-api",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": os.sys.version,
        "started_at": os.getenv("APP_START_TIME", datetime.utcnow().isoformat()),
        "features": {
            "ai_optimization": True,
            "push_notifications": True,
            "real_time_updates": True,
            "audit_logging": True,
            "rate_limiting": True
        }
    }
