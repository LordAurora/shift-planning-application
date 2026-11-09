from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from app.database import Base


class Organization(Base):
    """A company workspace. All business data belongs to exactly one organization."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"


DEMO_ORGANIZATION_NAME = "Demo Company"


def get_or_create_demo_organization(db) -> Organization:
    """The workspace that holds the development accounts and synthetic demo data."""
    organization = db.query(Organization).filter(Organization.name == DEMO_ORGANIZATION_NAME).order_by(Organization.id).first()
    if organization is None:
        organization = Organization(name=DEMO_ORGANIZATION_NAME)
        db.add(organization)
        db.flush()
    return organization
