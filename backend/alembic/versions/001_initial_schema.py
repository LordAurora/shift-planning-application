"""Initial schema: users, departments, employees, shifts, rules, notifications, audit logs

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def _timestamps():
    return [
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'MANAGER', 'EMPLOYEE', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        *_timestamps(),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index('ix_departments_id', 'departments', ['id'])

    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('availability', sa.JSON(), nullable=True),
        sa.Column('weekly_working_limit', sa.Float(), default=40.0),
        sa.Column('overtime_limit', sa.Float(), default=10.0),
        *_timestamps(),
    )
    op.create_index('ix_employees_id', 'employees', ['id'])
    op.create_index('ix_employees_email', 'employees', ['email'], unique=True)

    op.create_table(
        'shifts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('SCHEDULED', 'COMPLETED', 'CANCELLED', name='shiftstatus'), nullable=False),
        *_timestamps(),
    )
    op.create_index('ix_shifts_id', 'shifts', ['id'])

    op.create_table(
        'shift_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('min_employees', sa.Integer(), default=1),
        sa.Column('max_employees', sa.Integer(), default=10),
        sa.Column('days_of_week', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        *_timestamps(),
    )
    op.create_index('ix_shift_rules_id', 'shift_rules', ['id'])

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('INFO', 'WARNING', 'ERROR', 'SUCCESS', name='notificationtype'), nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])


def downgrade():
    for table in ['audit_logs', 'notifications', 'shift_rules', 'shifts', 'employees', 'departments', 'users']:
        op.drop_table(table)
    for enum_name in ['notificationtype', 'shiftstatus', 'userrole']:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
