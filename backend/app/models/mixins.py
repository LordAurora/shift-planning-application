"""Database model mixins for common functionality."""

from datetime import datetime
from typing import Optional, TypeVar, Generic
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, event
from sqlalchemy.orm import declared_attr, Query
from sqlalchemy.ext.declarative import declared_attr


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime, 
            default=datetime.utcnow, 
            onupdate=datetime.utcnow,
            nullable=False
        )


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete capability to models.
    
    Adds columns:
    - is_deleted: Boolean flag for soft-delete status
    - deleted_at: Timestamp when record was soft-deleted
    - deleted_by: User ID who performed the soft-delete
    
    Usage:
        class MyModel(Base, SoftDeleteMixin):
            ...
            
        # Soft delete a record
        record.soft_delete(user_id=current_user.id)
        
        # Query only active records
        active_records = session.query(MyModel).filter(MyModel.is_deleted == False)
        
        # Restore a soft-deleted record
        record.restore()
    """
    
    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False, index=True)
    
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)
    
    @declared_attr
    def deleted_by(cls):
        return Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def soft_delete(self, user_id: Optional[int] = None) -> None:
        """
        Mark record as soft-deleted.
        
        Args:
            user_id: Optional ID of user performing the deletion
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if user_id:
            self.deleted_by = user_id
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    @classmethod
    def active(cls, query: Query) -> Query:
        """Filter query to only return active (non-deleted) records."""
        return query.filter(cls.is_deleted == False)
    
    @classmethod
    def deleted(cls, query: Query) -> Query:
        """Filter query to only return soft-deleted records."""
        return query.filter(cls.is_deleted == True)


class AuditMixin(TimestampMixin):
    """
    Mixin that adds audit trail columns.
    
    Extends TimestampMixin with:
    - created_by: User who created the record
    - updated_by: User who last updated the record
    """
    
    @declared_attr
    def created_by(cls):
        return Column(Integer, ForeignKey('users.id'), nullable=True)
    
    @declared_attr
    def updated_by(cls):
        return Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def set_created_by(self, user_id: int) -> None:
        """Set the created_by field."""
        self.created_by = user_id
    
    def set_updated_by(self, user_id: int) -> None:
        """Set the updated_by field."""
        self.updated_by = user_id


class VersionMixin:
    """
    Mixin for optimistic locking with version number.
    
    Adds:
    - version: Integer version number incremented on each update
    
    Useful for preventing lost updates in concurrent scenarios.
    """
    
    @declared_attr
    def version(cls):
        return Column(Integer, default=1, nullable=False)
    
    def increment_version(self) -> None:
        """Increment the version number."""
        self.version = (self.version or 0) + 1


def soft_delete_default_filter(execute_state):
    """
    SQLAlchemy event listener to automatically filter soft-deleted records.
    
    This can be attached to queries to automatically exclude soft-deleted
    records unless explicitly requested.
    
    Usage:
        from sqlalchemy import event
        event.listen(Session, "do_orm_execute", soft_delete_default_filter)
    """
    # Implementation would go here for automatic filtering
    # This is an advanced feature that requires careful consideration
    pass


class ActiveRecordMixin:
    """
    Mixin that provides convenient query methods on the model class.
    
    Allows for ActiveRecord-style queries:
        User.find_by_id(1)
        User.find_all()
        User.find_by(email="test@example.com")
    """
    
    @classmethod
    def find_by_id(cls, session, id: int):
        """Find record by primary key."""
        return session.query(cls).get(id)
    
    @classmethod
    def find_all(cls, session, include_deleted: bool = False):
        """Find all records."""
        query = session.query(cls)
        if hasattr(cls, 'is_deleted') and not include_deleted:
            query = query.filter(cls.is_deleted == False)
        return query.all()
    
    @classmethod
    def find_by(cls, session, include_deleted: bool = False, **kwargs):
        """Find records by column values."""
        query = session.query(cls).filter_by(**kwargs)
        if hasattr(cls, 'is_deleted') and not include_deleted:
            query = query.filter(cls.is_deleted == False)
        return query.all()
    
    @classmethod
    def find_one_by(cls, session, include_deleted: bool = False, **kwargs):
        """Find single record by column values."""
        query = session.query(cls).filter_by(**kwargs)
        if hasattr(cls, 'is_deleted') and not include_deleted:
            query = query.filter(cls.is_deleted == False)
        return query.first()
    
    @classmethod
    def count(cls, session, include_deleted: bool = False) -> int:
        """Count records."""
        query = session.query(cls)
        if hasattr(cls, 'is_deleted') and not include_deleted:
            query = query.filter(cls.is_deleted == False)
        return query.count()
