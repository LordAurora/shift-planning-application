"""
Server-Sent Events (SSE) Router - Real-time updates.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator, Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime
import logging

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])

# In-memory event queue (use Redis in production for multi-server)
event_queues: Dict[int, asyncio.Queue] = {}
# Polling buffer for fallback
polling_buffers: Dict[int, List[Dict[str, Any]]] = {}


async def event_generator(user_id: int) -> AsyncGenerator[str, None]:
    """
    Generate SSE events for a user.
    """
    # Create queue for this user
    if user_id not in event_queues:
        event_queues[user_id] = asyncio.Queue()
    
    queue = event_queues[user_id]
    
    # Send initial connection event
    yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
    try:
        while True:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        if user_id in event_queues:
            del event_queues[user_id]


@router.get("/stream")
async def event_stream(
    token: str = Query(..., description="Auth token"),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events stream for real-time updates.
    
    Connect to this endpoint to receive real-time events:
    - shift:created, shift:updated, shift:deleted
    - leave:requested, leave:approved, leave:rejected
    - notification:new
    - schedule:published
    """
    # Validate token manually (can't use Depends with SSE easily)
    from app.utils.security import decode_access_token
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    logger.info(f"SSE connection established for user {user_id}")
    
    return StreamingResponse(
        event_generator(int(user_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/poll")
async def poll_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Polling endpoint for clients that can't use SSE.
    Returns events since last poll.
    """
    user_id = current_user.id
    
    # Get buffered events
    events = polling_buffers.get(user_id, [])
    
    # Clear buffer
    polling_buffers[user_id] = []
    
    return events


async def broadcast_event(
    event_type: str,
    data: Dict[str, Any],
    user_ids: List[int] = None,
    exclude_user_id: int = None,
    correlation_id: str = None
):
    """
    Broadcast event to users.
    
    Args:
        event_type: Type of event (e.g., 'shift:updated')
        data: Event payload
        user_ids: Specific users to notify (None = all connected)
        exclude_user_id: User to exclude (e.g., the one who made the change)
        correlation_id: Request correlation ID
    """
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "correlationId": correlation_id
    }
    
    # Determine target users
    if user_ids:
        targets = [uid for uid in user_ids if uid != exclude_user_id]
    else:
        targets = [uid for uid in event_queues.keys() if uid != exclude_user_id]
    
    # Send to SSE queues
    for user_id in targets:
        if user_id in event_queues:
            try:
                event_queues[user_id].put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Event queue full for user {user_id}")
        
        # Also add to polling buffer
        if user_id not in polling_buffers:
            polling_buffers[user_id] = []
        polling_buffers[user_id].append(event)
        
        # Limit buffer size
        if len(polling_buffers[user_id]) > 100:
            polling_buffers[user_id] = polling_buffers[user_id][-100:]
    
    logger.info(f"Broadcast event {event_type} to {len(targets)} users")


async def notify_shift_change(
    shift_id: int,
    change_type: str,
    shift_data: Dict[str, Any],
    affected_user_ids: List[int],
    actor_id: int = None
):
    """Helper to broadcast shift changes."""
    await broadcast_event(
        event_type=f"shift:{change_type}",
        data={"shift_id": shift_id, **shift_data},
        user_ids=affected_user_ids,
        exclude_user_id=actor_id
    )


async def notify_leave_decision(
    leave_id: int,
    decision: str,
    leave_data: Dict[str, Any],
    requester_id: int,
    approver_id: int = None
):
    """Helper to broadcast leave decisions."""
    await broadcast_event(
        event_type=f"leave:{decision}",
        data={"leave_id": leave_id, **leave_data},
        user_ids=[requester_id],
        exclude_user_id=approver_id
    )


async def notify_schedule_published(
    department_id: int,
    schedule_data: Dict[str, Any],
    affected_user_ids: List[int]
):
    """Helper to broadcast schedule publication."""
    await broadcast_event(
        event_type="schedule:published",
        data={"department_id": department_id, **schedule_data},
        user_ids=affected_user_ids
    )


async def send_notification(
    user_id: int,
    notification_data: Dict[str, Any]
):
    """Helper to send notification to specific user."""
    await broadcast_event(
        event_type="notification:new",
        data=notification_data,
        user_ids=[user_id]
    )


# Connection stats endpoint
@router.get("/stats")
async def connection_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get SSE connection statistics (admin only).
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "active_connections": len(event_queues),
        "connected_users": list(event_queues.keys()),
        "polling_buffers": {uid: len(events) for uid, events in polling_buffers.items()},
        "timestamp": datetime.utcnow().isoformat()
    }
