"""Add scheduling preferences to employees

Revision ID: 004_employee_preferences
Revises: 003_performance_indexes
Create Date: 2026-11-12

Stores each employee's preferred shift, weekly day off and work model
so the optimizer can take them into account.
"""

from alembic import op
import sqlalchemy as sa


revision = '004_employee_preferences'
down_revision = '003_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('employees', sa.Column('preferences', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('employees', 'preferences')
