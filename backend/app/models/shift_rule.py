from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ShiftRule(Base):
    """Shift rule model for defining shift requirements"""
    __tablename__ = "shift_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    role = Column(String(100), nullable=False)  # Job role this rule applies to
    
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    min_employees = Column(Integer, default=1)
    max_employees = Column(Integer, default=10)
    
    # Days of week this rule applies (0=Sunday, 6=Saturday)
    # Stored as JSON array: [0, 1, 2, 3, 4, 5, 6]
    days_of_week = Column(JSON, default=[1, 2, 3, 4, 5])  # Default: weekdays
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="shift_rules")

    def __repr__(self):
        return f"<ShiftRule(id={self.id}, name={self.name}, department_id={self.department_id})>"
