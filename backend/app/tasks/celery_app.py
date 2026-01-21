"""
Celery Application Configuration.
"""
from celery import Celery
from kombu import Queue
import os

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "shiftmaster",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.shift_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.maintenance_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Tasks acknowledged after completion
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Fair task distribution
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task routing - different queues for different priorities
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("high_priority", routing_key="high"),
        Queue("low_priority", routing_key="low"),
        Queue("notifications", routing_key="notifications"),
        Queue("ai_processing", routing_key="ai"),
    ),
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_routing_key="default",
    
    # Task routes
    task_routes={
        "app.tasks.shift_tasks.process_shift_optimization": {
            "queue": "ai_processing",
            "routing_key": "ai",
        },
        "app.tasks.notification_tasks.*": {
            "queue": "notifications",
            "routing_key": "notifications",
        },
        "app.tasks.maintenance_tasks.*": {
            "queue": "low_priority",
            "routing_key": "low",
        },
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-tokens-daily": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_tokens",
            "schedule": 86400.0,  # Once per day
        },
        "archive-audit-logs-weekly": {
            "task": "app.tasks.maintenance_tasks.archive_old_audit_logs",
            "schedule": 604800.0,  # Once per week
        },
        "generate-analytics-daily": {
            "task": "app.tasks.maintenance_tasks.generate_analytics_report",
            "schedule": 86400.0,  # Once per day
            "kwargs": {"report_type": "daily"},
        },
    },
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Worker settings
    worker_concurrency=4,
    worker_max_tasks_per_child=1000,
)


# Optional: Configure for different environments
def configure_celery(app_config: dict):
    """
    Configure Celery based on application settings.
    Call this during application startup if needed.
    """
    if app_config.get("TESTING"):
        celery_app.conf.update(
            task_always_eager=True,  # Execute tasks synchronously in tests
            task_eager_propagates=True,
        )
    
    if app_config.get("CELERY_BROKER_URL"):
        celery_app.conf.broker_url = app_config["CELERY_BROKER_URL"]
    
    if app_config.get("CELERY_RESULT_BACKEND"):
        celery_app.conf.result_backend = app_config["CELERY_RESULT_BACKEND"]


# Health check for Celery
def check_celery_health() -> dict:
    """Check Celery broker and worker health"""
    try:
        # Check broker connection
        celery_app.connection().ensure_connection(max_retries=1)
        broker_ok = True
    except Exception as e:
        broker_ok = False
    
    try:
        # Check worker availability
        inspect = celery_app.control.inspect()
        active_workers = inspect.active() or {}
        workers_ok = len(active_workers) > 0
    except Exception:
        workers_ok = False
    
    return {
        "broker_connected": broker_ok,
        "workers_available": workers_ok,
        "status": "healthy" if (broker_ok and workers_ok) else "degraded"
    }
