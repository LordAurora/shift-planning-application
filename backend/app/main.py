from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from datetime import datetime

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.employee import Employee
from app.models.shift import Shift
from app.models.shift_rule import ShiftRule
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.leave_request import LeaveRequest  # noqa: F401
from app.models.security_scan import SecurityScan  # noqa: F401
from app.utils.security import get_password_hash

# Import middleware
from app.middleware.logging_middleware import (
    LoggingMiddleware,
    CorrelationIdMiddleware,
    configure_logging,
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# Import routers
from app.routers import auth, employees, departments, shifts, rules, ai, notifications
from app.routers import leave_requests
from app.routers import health
from app.routers import events
from app.routers import shifts_enhanced, leave_enhanced
from app.routers import security, security_scans
from app.routers import dashboard


def create_initial_data(db):
    """Create initial data for development"""
    # Check if admin user exists
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if admin:
        return  # Data already exists
    
    # Create admin user
    admin = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db.add(admin)
    
    # Create manager user
    manager = User(
        email="manager@example.com",
        name="Manager User",
        hashed_password=get_password_hash("manager123"),
        role=UserRole.MANAGER
    )
    db.add(manager)
    
    # Create employee user
    employee_user = User(
        email="employee@example.com",
        name="Employee User",
        hashed_password=get_password_hash("employee123"),
        role=UserRole.EMPLOYEE
    )
    db.add(employee_user)
    
    # Create departments
    engineering = Department(name="Engineering", description="Software development team")
    operations = Department(name="Operations", description="Operations and logistics")
    customer_service = Department(name="Customer Service", description="Customer support team")
    hr = Department(name="HR", description="Human Resources")
    
    db.add_all([engineering, operations, customer_service, hr])
    db.flush()  # Get department IDs
    
    # Create employees
    employees_data = [
        {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "role": "Developer",
            "department_id": engineering.id,
            "availability": [
                {"day": 1, "start_time": "09:00", "end_time": "17:00"},
                {"day": 2, "start_time": "09:00", "end_time": "17:00"},
                {"day": 3, "start_time": "09:00", "end_time": "17:00"},
                {"day": 4, "start_time": "09:00", "end_time": "17:00"},
                {"day": 5, "start_time": "09:00", "end_time": "17:00"},
            ],
            "weekly_working_limit": 40,
            "overtime_limit": 10
        },
        {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com",
            "role": "Manager",
            "department_id": operations.id,
            "availability": [
                {"day": 1, "start_time": "08:00", "end_time": "16:00"},
                {"day": 2, "start_time": "08:00", "end_time": "16:00"},
                {"day": 3, "start_time": "08:00", "end_time": "16:00"},
                {"day": 4, "start_time": "08:00", "end_time": "16:00"},
                {"day": 5, "start_time": "08:00", "end_time": "16:00"},
            ],
            "weekly_working_limit": 45,
            "overtime_limit": 15
        },
        {
            "name": "Michael Brown",
            "email": "michael.brown@example.com",
            "role": "Support",
            "department_id": customer_service.id,
            "availability": [
                {"day": 0, "start_time": "10:00", "end_time": "18:00"},
                {"day": 1, "start_time": "10:00", "end_time": "18:00"},
                {"day": 2, "start_time": "10:00", "end_time": "18:00"},
                {"day": 5, "start_time": "10:00", "end_time": "18:00"},
                {"day": 6, "start_time": "10:00", "end_time": "18:00"},
            ],
            "weekly_working_limit": 40,
            "overtime_limit": 8
        },
        {
            "name": "Emily Davis",
            "email": "emily.davis@example.com",
            "role": "Developer",
            "department_id": engineering.id,
            "availability": [
                {"day": 1, "start_time": "10:00", "end_time": "18:00"},
                {"day": 2, "start_time": "10:00", "end_time": "18:00"},
                {"day": 3, "start_time": "10:00", "end_time": "18:00"},
                {"day": 4, "start_time": "10:00", "end_time": "18:00"},
                {"day": 5, "start_time": "10:00", "end_time": "18:00"},
            ],
            "weekly_working_limit": 40,
            "overtime_limit": 10
        },
    ]
    
    for emp_data in employees_data:
        emp = Employee(**emp_data)
        db.add(emp)
    
    # Create shift rules
    from datetime import time
    rules_data = [
        {
            "name": "Morning Shift - Engineering",
            "department_id": engineering.id,
            "role": "Developer",
            "start_time": time(9, 0),
            "end_time": time(17, 0),
            "min_employees": 2,
            "max_employees": 5,
            "days_of_week": [1, 2, 3, 4, 5],
            "is_active": True
        },
        {
            "name": "Support Shift",
            "department_id": customer_service.id,
            "role": "Support",
            "start_time": time(8, 0),
            "end_time": time(20, 0),
            "min_employees": 3,
            "max_employees": 8,
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "is_active": True
        },
        {
            "name": "Operations Day Shift",
            "department_id": operations.id,
            "role": "Any",
            "start_time": time(6, 0),
            "end_time": time(14, 0),
            "min_employees": 4,
            "max_employees": 10,
            "days_of_week": [1, 2, 3, 4, 5],
            "is_active": True
        },
    ]
    
    for rule_data in rules_data:
        rule = ShiftRule(**rule_data)
        db.add(rule)
    
    # Create sample notifications for admin
    from app.models.notification import NotificationType
    notifications_data = [
        {
            "user_id": 1,  # Admin user
            "title": "Welcome to ShiftMaster AI",
            "message": "Your account has been set up successfully. Start by exploring the dashboard.",
            "type": NotificationType.INFO,
            "is_read": False
        },
        {
            "user_id": 1,
            "title": "New Shift Rule Created",
            "message": "Morning Shift - Engineering rule has been created and activated.",
            "type": NotificationType.SUCCESS,
            "is_read": True
        },
    ]
    
    for notif_data in notifications_data:
        notif = Notification(**notif_data)
        db.add(notif)
    
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    # Record start time
    os.environ["APP_START_TIME"] = datetime.utcnow().isoformat()
    
    # Configure logging
    configure_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        json_format=settings.ENVIRONMENT != "development"
    )
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial data for development
    if settings.ENVIRONMENT == "development":
        db = SessionLocal()
        try:
            create_initial_data(db)
        finally:
            db.close()
    
    yield
    
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title="ShiftMaster AI API",
    description="AI-powered shift planning and optimization system",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware (order matters - last added is first executed)
# 1. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate limiting (only in production to avoid dev friction)
if settings.ENVIRONMENT != "development":
    app.add_middleware(RateLimitMiddleware)

# 3. Request logging
app.add_middleware(LoggingMiddleware)

# 4. Correlation ID for request tracing
app.add_middleware(CorrelationIdMiddleware)

# 5. CORS (geliştirme için geniş, prod için env'den)
cors_origins = ["*"] if settings.CORS_ORIGINS == "*" else settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(health.router)  # Health endpoints at root
app.include_router(auth.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(shifts.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(leave_requests.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")  # SSE real-time events

# Enhanced routers with domain service integration
app.include_router(shifts_enhanced.router, prefix="/api/v1")  # Enhanced shifts with rule validation
app.include_router(leave_enhanced.router, prefix="/api/v1")  # Enhanced leave with auto-approval

# Security AI Analysis endpoints
app.include_router(security_scans.router, prefix="/api/v1")  # Persisted scans + dashboard stats
app.include_router(security.router, prefix="/api/v1")  # Security vulnerability scanning


@app.get("/")
async def root():
    return {
        "message": "Welcome to ShiftMaster AI API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "metrics": "/metrics"
    }
