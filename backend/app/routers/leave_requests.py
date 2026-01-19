from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.user import User
from app.schemas.leave_request import LeaveRequestCreate, LeaveRequestResponse
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])


def _to_response(entity: LeaveRequest) -> LeaveRequestResponse:
    return LeaveRequestResponse(
        id=entity.id,
        employee_id=entity.user_id,
        employee_name=entity.requester.name if entity.requester else None,
        type=entity.type,
        start_date=entity.start_date,
        end_date=entity.end_date,
        reason=entity.reason,
        status=entity.status,
        response_note=entity.response_note,
        responded_by=entity.responded_by,
        responder_name=entity.responder.name if entity.responder else None,
        responded_at=entity.responded_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get("", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    status_filter: Optional[LeaveStatus] = None,
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    query = db.query(LeaveRequest)

    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)

    if employee_id:
        query = query.filter(LeaveRequest.user_id == employee_id)

    if start_date:
        query = query.filter(LeaveRequest.start_date >= start_date)

    if end_date:
        query = query.filter(LeaveRequest.end_date <= end_date)

    requests = query.order_by(LeaveRequest.created_at.desc()).all()
    return [_to_response(r) for r in requests]


@router.get("/my", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requests = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id == current_user.id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )
    return [_to_response(r) for r in requests]


@router.post("", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    request_data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request_data.end_date < request_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date",
        )

    leave_request = LeaveRequest(
        user_id=current_user.id,
        type=request_data.type,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        reason=request_data.reason,
        status=LeaveStatus.PENDING,
    )

    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)

    return _to_response(leave_request)


@router.delete("/{request_id}")
async def delete_leave_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()

    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found",
        )

    if current_user.role.value not in {"admin", "manager"} and leave_request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this request",
        )

    if leave_request.status != LeaveStatus.PENDING and current_user.id == leave_request.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be cancelled",
        )

    db.delete(leave_request)
    db.commit()

    return {"message": "Leave request deleted"}
