"""Persist Security AI scans

Revision ID: 005_security_scans
Revises: 004_employee_preferences
Create Date: 2026-11-12
"""

from alembic import op
import sqlalchemy as sa


revision = '005_security_scans'
down_revision = '004_employee_preferences'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'security_scans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('language', sa.String(50), nullable=False),
        sa.Column('detection_mode', sa.String(30), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('critical', sa.Integer(), nullable=False),
        sa.Column('high', sa.Integer(), nullable=False),
        sa.Column('medium', sa.Integer(), nullable=False),
        sa.Column('low', sa.Integer(), nullable=False),
        sa.Column('info', sa.Integer(), nullable=False),
        sa.Column('findings', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_security_scans_id', 'security_scans', ['id'])
    op.create_index('ix_security_scans_created_at', 'security_scans', ['created_at'])


def downgrade():
    op.drop_table('security_scans')
