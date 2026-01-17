"""Add indexes, constraints, and soft-delete support

Revision ID: 003_indexes_constraints
Revises: 002_add_leave_requests
Create Date: 2025-01-01

This migration adds:
1. Performance indexes for shift queries
2. Constraint for overlapping shifts (excluding soft-deleted)
3. Soft-delete columns to relevant tables
4. Indexes for audit trail queries
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_indexes_constraints'
down_revision = '002_add_leave_requests'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================
    # SOFT DELETE COLUMNS
    # =========================================
    
    # Add soft-delete columns to shifts
    op.add_column('shifts', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('shifts', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('shifts', sa.Column('deleted_by', sa.Integer(), nullable=True))
    
    # Add soft-delete columns to employees
    op.add_column('employees', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('employees', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('employees', sa.Column('deleted_by', sa.Integer(), nullable=True))
    
    # Add soft-delete columns to leave_requests
    op.add_column('leave_requests', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('leave_requests', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('leave_requests', sa.Column('deleted_by', sa.Integer(), nullable=True))
    
    # Add soft-delete columns to departments
    op.add_column('departments', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('departments', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # =========================================
    # PERFORMANCE INDEXES FOR SHIFTS
    # =========================================
    
    # Index for shift date range queries (most common)
    op.create_index(
        'ix_shifts_date_range',
        'shifts',
        ['shift_date', 'start_time', 'end_time'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Index for employee shift lookups
    op.create_index(
        'ix_shifts_employee_date',
        'shifts',
        ['employee_id', 'shift_date'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Index for department shift queries
    op.create_index(
        'ix_shifts_department_date',
        'shifts',
        ['department_id', 'shift_date'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Index for status-based queries
    op.create_index(
        'ix_shifts_status',
        'shifts',
        ['status', 'shift_date'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Composite index for calendar view queries
    op.create_index(
        'ix_shifts_calendar_view',
        'shifts',
        ['department_id', 'shift_date', 'status', 'employee_id'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # =========================================
    # PERFORMANCE INDEXES FOR EMPLOYEES
    # =========================================
    
    # Index for active employees by department
    op.create_index(
        'ix_employees_department_active',
        'employees',
        ['department_id', 'is_active'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Index for user email lookups (unique active)
    op.create_index(
        'ix_employees_email_active',
        'employees',
        ['email'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false AND is_active = true')
    )
    
    # =========================================
    # PERFORMANCE INDEXES FOR LEAVE REQUESTS
    # =========================================
    
    # Index for employee leave lookup by date range
    op.create_index(
        'ix_leave_requests_employee_dates',
        'leave_requests',
        ['employee_id', 'start_date', 'end_date'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Index for pending leave requests (for managers)
    op.create_index(
        'ix_leave_requests_pending',
        'leave_requests',
        ['status', 'created_at'],
        postgresql_where=sa.text("is_deleted = false AND status = 'pending'")
    )
    
    # Index for approved leave overlap checking
    op.create_index(
        'ix_leave_requests_approved_overlap',
        'leave_requests',
        ['employee_id', 'start_date', 'end_date', 'status'],
        postgresql_where=sa.text("is_deleted = false AND status = 'approved'")
    )
    
    # =========================================
    # PERFORMANCE INDEXES FOR AUDIT LOGS
    # =========================================
    
    # Index for audit trail by entity
    op.create_index(
        'ix_audit_logs_entity',
        'audit_logs',
        ['entity_type', 'entity_id', 'created_at']
    )
    
    # Index for user audit trail
    op.create_index(
        'ix_audit_logs_user',
        'audit_logs',
        ['user_id', 'created_at']
    )
    
    # Index for time-based audit queries
    op.create_index(
        'ix_audit_logs_timestamp',
        'audit_logs',
        ['created_at', 'action']
    )
    
    # =========================================
    # PERFORMANCE INDEXES FOR NOTIFICATIONS
    # =========================================
    
    # Index for unread notifications
    op.create_index(
        'ix_notifications_unread',
        'notifications',
        ['user_id', 'created_at'],
        postgresql_where=sa.text('is_read = false')
    )
    
    # =========================================
    # CONSTRAINT FOR OVERLAPPING SHIFTS
    # =========================================
    
    # Create function to check shift overlap (PostgreSQL-specific)
    op.execute("""
        CREATE OR REPLACE FUNCTION check_shift_overlap()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Skip check if shift is being soft-deleted
            IF NEW.is_deleted = true THEN
                RETURN NEW;
            END IF;
            
            -- Check for overlapping shifts for the same employee on the same date
            IF EXISTS (
                SELECT 1 FROM shifts s
                WHERE s.id != NEW.id
                AND s.employee_id = NEW.employee_id
                AND s.shift_date = NEW.shift_date
                AND s.is_deleted = false
                AND s.status NOT IN ('cancelled', 'rejected')
                AND (
                    -- Check time overlap
                    (NEW.start_time < s.end_time AND NEW.end_time > s.start_time)
                )
            ) THEN
                RAISE EXCEPTION 'Overlapping shift detected for employee % on date %', 
                    NEW.employee_id, NEW.shift_date;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for shift overlap validation
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_check_shift_overlap ON shifts;
        CREATE TRIGGER trigger_check_shift_overlap
        BEFORE INSERT OR UPDATE ON shifts
        FOR EACH ROW
        EXECUTE FUNCTION check_shift_overlap();
    """)
    
    # =========================================
    # CONSTRAINT FOR LEAVE REQUEST OVERLAP
    # =========================================
    
    # Create function to check leave overlap
    op.execute("""
        CREATE OR REPLACE FUNCTION check_leave_overlap()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Skip check if leave is being soft-deleted or rejected/cancelled
            IF NEW.is_deleted = true OR NEW.status IN ('rejected', 'cancelled') THEN
                RETURN NEW;
            END IF;
            
            -- Check for overlapping approved/pending leave for the same employee
            IF EXISTS (
                SELECT 1 FROM leave_requests lr
                WHERE lr.id != NEW.id
                AND lr.employee_id = NEW.employee_id
                AND lr.is_deleted = false
                AND lr.status IN ('approved', 'pending')
                AND (
                    -- Check date overlap
                    (NEW.start_date <= lr.end_date AND NEW.end_date >= lr.start_date)
                )
            ) THEN
                RAISE EXCEPTION 'Overlapping leave request detected for employee % between % and %', 
                    NEW.employee_id, NEW.start_date, NEW.end_date;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for leave overlap validation  
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_check_leave_overlap ON leave_requests;
        CREATE TRIGGER trigger_check_leave_overlap
        BEFORE INSERT OR UPDATE ON leave_requests
        FOR EACH ROW
        EXECUTE FUNCTION check_leave_overlap();
    """)
    
    # =========================================
    # CHECK CONSTRAINTS
    # =========================================
    
    # Shift time validation: end_time must be after start_time
    op.create_check_constraint(
        'ck_shifts_time_order',
        'shifts',
        'end_time > start_time'
    )
    
    # Leave request date validation: end_date must be >= start_date
    op.create_check_constraint(
        'ck_leave_requests_date_order',
        'leave_requests',
        'end_date >= start_date'
    )


def downgrade():
    # =========================================
    # DROP CHECK CONSTRAINTS
    # =========================================
    op.drop_constraint('ck_shifts_time_order', 'shifts', type_='check')
    op.drop_constraint('ck_leave_requests_date_order', 'leave_requests', type_='check')
    
    # =========================================
    # DROP TRIGGERS AND FUNCTIONS
    # =========================================
    op.execute('DROP TRIGGER IF EXISTS trigger_check_shift_overlap ON shifts')
    op.execute('DROP FUNCTION IF EXISTS check_shift_overlap()')
    op.execute('DROP TRIGGER IF EXISTS trigger_check_leave_overlap ON leave_requests')
    op.execute('DROP FUNCTION IF EXISTS check_leave_overlap()')
    
    # =========================================
    # DROP INDEXES
    # =========================================
    
    # Notification indexes
    op.drop_index('ix_notifications_unread', table_name='notifications')
    
    # Audit log indexes
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    
    # Leave request indexes
    op.drop_index('ix_leave_requests_approved_overlap', table_name='leave_requests')
    op.drop_index('ix_leave_requests_pending', table_name='leave_requests')
    op.drop_index('ix_leave_requests_employee_dates', table_name='leave_requests')
    
    # Employee indexes
    op.drop_index('ix_employees_email_active', table_name='employees')
    op.drop_index('ix_employees_department_active', table_name='employees')
    
    # Shift indexes
    op.drop_index('ix_shifts_calendar_view', table_name='shifts')
    op.drop_index('ix_shifts_status', table_name='shifts')
    op.drop_index('ix_shifts_department_date', table_name='shifts')
    op.drop_index('ix_shifts_employee_date', table_name='shifts')
    op.drop_index('ix_shifts_date_range', table_name='shifts')
    
    # =========================================
    # DROP SOFT DELETE COLUMNS
    # =========================================
    
    # Departments
    op.drop_column('departments', 'deleted_at')
    op.drop_column('departments', 'is_deleted')
    
    # Leave requests
    op.drop_column('leave_requests', 'deleted_by')
    op.drop_column('leave_requests', 'deleted_at')
    op.drop_column('leave_requests', 'is_deleted')
    
    # Employees
    op.drop_column('employees', 'deleted_by')
    op.drop_column('employees', 'deleted_at')
    op.drop_column('employees', 'is_deleted')
    
    # Shifts
    op.drop_column('shifts', 'deleted_by')
    op.drop_column('shifts', 'deleted_at')
    op.drop_column('shifts', 'is_deleted')
