from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.tenancy import TenantScoped


class Department(TenantScoped, Base):
    """Department model"""
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint('organization_id', 'name', name='uq_departments_org_name'),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    employees = relationship("Employee", back_populates="department", cascade="all, delete-orphan")
    shifts = relationship("Shift", back_populates="department", cascade="all, delete-orphan")
    shift_rules = relationship("ShiftRule", back_populates="department", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name})>"
