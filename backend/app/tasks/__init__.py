"""
Background Tasks Package - Async task processing with Celery.
"""
from .celery_app import celery_app
from .shift_tasks import (
    process_shift_optimization,
    notify_shift_changes,
    rebalance_after_leave,
    generate_weekly_schedule,
)
from .notification_tasks import (
    send_push_notification,
    send_batch_notifications,
    send_email_notification,
)
from .maintenance_tasks import (
    cleanup_expired_tokens,
    archive_old_audit_logs,
    generate_analytics_report,
)

__all__ = [
    "celery_app",
    # Shift tasks
    "process_shift_optimization",
    "notify_shift_changes",
    "rebalance_after_leave",
    "generate_weekly_schedule",
    # Notification tasks
    "send_push_notification",
    "send_batch_notifications",
    "send_email_notification",
    # Maintenance tasks
    "cleanup_expired_tokens",
    "archive_old_audit_logs",
    "generate_analytics_report",
]
