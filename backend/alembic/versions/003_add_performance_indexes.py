"""Add performance indexes for scheduling and audit queries

Revision ID: 003_performance_indexes
Revises: 002_add_leave_requests
Create Date: 2026-01-24
"""

from alembic import op


revision = '003_performance_indexes'
down_revision = '002_add_leave_requests'
branch_labels = None
depends_on = None


INDEXES = [
    # Calendar and list views filter shifts by time range
    ('ix_shifts_start_end', 'shifts', ['start_time', 'end_time']),
    # Per-employee lookups: conflicts, weekly hours, rest periods
    ('ix_shifts_employee_start', 'shifts', ['employee_id', 'start_time']),
    # Department schedules and recommendations
    ('ix_shifts_department_start', 'shifts', ['department_id', 'start_time']),
    ('ix_shifts_status', 'shifts', ['status']),
    ('ix_employees_department', 'employees', ['department_id']),
    ('ix_shift_rules_department_active', 'shift_rules', ['department_id', 'is_active']),
    ('ix_leave_requests_user_dates', 'leave_requests', ['user_id', 'start_date', 'end_date']),
    ('ix_leave_requests_status_created', 'leave_requests', ['status', 'created_at']),
    ('ix_notifications_user_read', 'notifications', ['user_id', 'is_read']),
    ('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id']),
    ('ix_audit_logs_created', 'audit_logs', ['created_at']),
]


def upgrade():
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table)
