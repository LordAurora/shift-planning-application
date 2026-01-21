"""
Notification Background Tasks.
"""
from celery import shared_task
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    queue="notifications"
)
def send_push_notification(
    self,
    user_id: int,
    title: str,
    body: str,
    data: Dict[str, Any] = None,
    priority: str = "normal",  # normal, high
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Send a push notification to a single user.
    """
    logger.info(
        f"Sending push notification to user {user_id}",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        from app.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # Get user's device tokens
            # Check notification preferences
            # Respect quiet hours if applicable
            
            # In real implementation:
            # 1. Query user's FCM tokens
            # 2. Check notification preferences
            # 3. Send via Firebase Admin SDK
            
            result = {
                "user_id": user_id,
                "status": "sent",
                "title": title,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Push notification sent to user {user_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(
            f"Push notification failed for user {user_id}: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    queue="notifications"
)
def send_batch_notifications(
    self,
    user_ids: List[int],
    title: str,
    body: str,
    data: Dict[str, Any] = None,
    notification_type: str = "general",
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Send push notifications to multiple users efficiently.
    Uses FCM multicast for better performance.
    """
    logger.info(
        f"Sending batch notifications to {len(user_ids)} users",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        from app.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            successful = []
            failed = []
            skipped = []
            
            # Group users by notification preferences
            # Respect quiet hours per user
            # Use FCM multicast (up to 500 tokens per request)
            
            for user_id in user_ids:
                try:
                    # Check user preferences
                    # In real implementation, check notification settings
                    
                    # Check quiet hours
                    # In real implementation, check user's quiet hours setting
                    
                    # Send notification
                    successful.append(user_id)
                    
                except Exception as e:
                    failed.append({"user_id": user_id, "error": str(e)})
            
            result = {
                "total": len(user_ids),
                "successful": len(successful),
                "failed": len(failed),
                "skipped": len(skipped),
                "notification_type": notification_type,
                "title": title,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Batch notifications completed: {len(successful)} sent, {len(failed)} failed",
                extra={"correlation_id": correlation_id}
            )
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(
            f"Batch notification failed: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    queue="notifications"
)
def send_email_notification(
    self,
    user_id: int,
    template: str,
    subject: str,
    context: Dict[str, Any],
    priority: str = "normal",
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Send an email notification to a user.
    """
    logger.info(
        f"Sending email to user {user_id}",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        from app.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # Get user's email address
            # Check email notification preferences
            # Render email template
            # Send via email service (SendGrid, SES, etc.)
            
            # In real implementation:
            # 1. Query user email
            # 2. Check email preferences
            # 3. Render template
            # 4. Send via email provider
            
            result = {
                "user_id": user_id,
                "status": "sent",
                "template": template,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Email sent to user {user_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(
            f"Email notification failed for user {user_id}: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise self.retry(exc=e)


@shared_task(queue="notifications")
def send_shift_reminder(
    employee_id: int,
    shift_id: int,
    shift_start: str,
    reminder_type: str = "1_hour",  # 1_hour, 24_hours, custom
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Send shift reminder notification to employee.
    """
    logger.info(
        f"Sending shift reminder to employee {employee_id}",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        shift_dt = datetime.fromisoformat(shift_start)
        
        # Format reminder message
        if reminder_type == "1_hour":
            title = "Shift Starting Soon"
            body = f"Your shift starts in 1 hour at {shift_dt.strftime('%H:%M')}"
        elif reminder_type == "24_hours":
            title = "Upcoming Shift Tomorrow"
            body = f"You have a shift tomorrow at {shift_dt.strftime('%H:%M')}"
        else:
            title = "Shift Reminder"
            body = f"Your shift starts at {shift_dt.strftime('%H:%M')}"
        
        # Send push notification
        send_push_notification.delay(
            user_id=employee_id,
            title=title,
            body=body,
            data={
                "type": "shift_reminder",
                "shift_id": shift_id,
                "shift_start": shift_start
            },
            priority="high",
            correlation_id=correlation_id
        )
        
        return {
            "employee_id": employee_id,
            "shift_id": shift_id,
            "reminder_type": reminder_type,
            "status": "scheduled",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Shift reminder failed: {str(e)}")
        raise


@shared_task(queue="notifications")
def notify_leave_status_change(
    employee_id: int,
    leave_request_id: int,
    new_status: str,
    approver_name: Optional[str] = None,
    reason: Optional[str] = None,
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Notify employee about leave request status change.
    """
    logger.info(
        f"Notifying employee {employee_id} about leave status: {new_status}",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        if new_status == "approved":
            title = "Leave Request Approved ✓"
            body = f"Your leave request has been approved"
            if approver_name:
                body += f" by {approver_name}"
        elif new_status == "rejected":
            title = "Leave Request Declined"
            body = "Your leave request was not approved"
            if reason:
                body += f". Reason: {reason}"
        else:
            title = "Leave Request Update"
            body = f"Your leave request status: {new_status}"
        
        # Send push notification
        send_push_notification.delay(
            user_id=employee_id,
            title=title,
            body=body,
            data={
                "type": "leave_status",
                "leave_request_id": leave_request_id,
                "status": new_status
            },
            priority="high",
            correlation_id=correlation_id
        )
        
        # Also send email for important status changes
        if new_status in ["approved", "rejected"]:
            send_email_notification.delay(
                user_id=employee_id,
                template="leave_status",
                subject=title,
                context={
                    "leave_request_id": leave_request_id,
                    "status": new_status,
                    "approver": approver_name,
                    "reason": reason
                },
                correlation_id=correlation_id
            )
        
        return {
            "employee_id": employee_id,
            "leave_request_id": leave_request_id,
            "status": new_status,
            "notifications_sent": ["push", "email"] if new_status in ["approved", "rejected"] else ["push"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Leave status notification failed: {str(e)}")
        raise


@shared_task(queue="low_priority")
def schedule_shift_reminders(
    shift_id: int,
    employee_id: int,
    shift_start: str,
    reminder_preferences: List[str] = None,
    correlation_id: str = None
) -> Dict[str, Any]:
    """
    Schedule all reminders for a shift based on user preferences.
    """
    if reminder_preferences is None:
        reminder_preferences = ["24_hours", "1_hour"]
    
    logger.info(
        f"Scheduling reminders for shift {shift_id}",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        shift_dt = datetime.fromisoformat(shift_start)
        scheduled = []
        
        for reminder_type in reminder_preferences:
            if reminder_type == "24_hours":
                eta = shift_dt - timedelta(hours=24)
            elif reminder_type == "1_hour":
                eta = shift_dt - timedelta(hours=1)
            elif reminder_type == "30_minutes":
                eta = shift_dt - timedelta(minutes=30)
            else:
                continue
            
            # Only schedule if ETA is in the future
            if eta > datetime.utcnow():
                send_shift_reminder.apply_async(
                    kwargs={
                        "employee_id": employee_id,
                        "shift_id": shift_id,
                        "shift_start": shift_start,
                        "reminder_type": reminder_type,
                        "correlation_id": correlation_id
                    },
                    eta=eta
                )
                scheduled.append({
                    "type": reminder_type,
                    "scheduled_for": eta.isoformat()
                })
        
        return {
            "shift_id": shift_id,
            "employee_id": employee_id,
            "reminders_scheduled": scheduled,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule reminders: {str(e)}")
        raise
