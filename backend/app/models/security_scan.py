from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class SecurityScan(Base):
    """A persisted Security AI scan and its findings."""
    __tablename__ = "security_scans"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, default="snippet")
    language = Column(String(50), nullable=False, default="python")
    detection_mode = Column(String(30), nullable=False)
    duration_ms = Column(Float, nullable=False, default=0)

    total = Column(Integer, nullable=False, default=0)
    critical = Column(Integer, nullable=False, default=0)
    high = Column(Integer, nullable=False, default=0)
    medium = Column(Integer, nullable=False, default=0)
    low = Column(Integer, nullable=False, default=0)
    info = Column(Integer, nullable=False, default=0)

    # List of serialized findings (see routers/security_scans.py)
    findings = Column(JSON, nullable=False, default=list)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
