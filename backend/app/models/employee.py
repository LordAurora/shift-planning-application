from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.tenancy import TenantScoped


class Employee(TenantScoped, Base):
    """Employee model"""
    __tablename__ = "employees"
    __table_args__ = (
        Index('ix_employees_department', 'department_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(100), nullable=False)  # Job role (Developer, Manager, etc.)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    
    # Availability stored as JSON array of slots
    # Format: [{"day": 0-6, "start_time": "HH:MM", "end_time": "HH:MM"}, ...]
    availability = Column(JSON, default=list)
    
    # Working hours limits
    weekly_working_limit = Column(Float, default=40.0)  # Hours per week
    overtime_limit = Column(Float, default=10.0)  # Maximum overtime hours per week

    # Scheduling preferences used by the optimizer
    # Format: {"preferred_shift": "morning|day|afternoon|night",
    #          "weekly_off_day": 0-6 (Sunday-Saturday),
    #          "work_model": "office|remote|hybrid"}
    preferences = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="employees")
    shifts = relationship("Shift", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.name}, role={self.role})>"
