"""Add leave requests

Revision ID: 002_add_leave_requests
Revises: 001_initial_schema
Create Date: 2026-01-21
"""

from alembic import op
import sqlalchemy as sa


revision = '002_add_leave_requests'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.Enum('ANNUAL', 'SICK', 'PERSONAL', 'MATERNITY', 'UNPAID', name='leavetype'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='leavestatus'), nullable=False),
        sa.Column('response_note', sa.Text(), nullable=True),
        sa.Column('responded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_leave_requests_id', 'leave_requests', ['id'])


def downgrade():
    op.drop_table('leave_requests')
    for enum_name in ['leavestatus', 'leavetype']:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
