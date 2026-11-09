"""Multi-tenancy: organizations own all business data

Revision ID: 005_organizations
Revises: 004_employee_preferences
Create Date: 2026-11-12

Creates the organizations table, moves every existing row into a
"Demo Company" workspace and adds a required organization_id to all
tenant-owned tables. Department names become unique per organization.
"""

from alembic import op
import sqlalchemy as sa


revision = '005_organizations'
down_revision = '004_employee_preferences'
branch_labels = None
depends_on = None

TENANT_TABLES = [
    'users',
    'departments',
    'employees',
    'shifts',
    'shift_rules',
    'notifications',
    'leave_requests',
    'audit_logs',
]


def upgrade():
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_organizations_id', 'organizations', ['id'])

    bind = op.get_bind()
    bind.execute(sa.text("INSERT INTO organizations (name) VALUES ('Demo Company')"))
    demo_id = bind.execute(sa.text("SELECT MIN(id) FROM organizations")).scalar()

    for table in TENANT_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
        bind.execute(sa.text(f"UPDATE {table} SET organization_id = :org"), {"org": demo_id})
        with op.batch_alter_table(table) as batch:
            batch.alter_column('organization_id', existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key(f'fk_{table}_organization', 'organizations', ['organization_id'], ['id'])
            batch.create_index(f'ix_{table}_organization_id', ['organization_id'])

    # Department names are unique within a company, not globally
    if bind.dialect.name == 'postgresql':
        op.drop_constraint('departments_name_key', 'departments', type_='unique')
    with op.batch_alter_table('departments') as batch:
        batch.create_unique_constraint('uq_departments_org_name', ['organization_id', 'name'])


def downgrade():
    bind = op.get_bind()
    with op.batch_alter_table('departments') as batch:
        batch.drop_constraint('uq_departments_org_name', type_='unique')
    if bind.dialect.name == 'postgresql':
        op.create_unique_constraint('departments_name_key', 'departments', ['name'])

    for table in reversed(TENANT_TABLES):
        with op.batch_alter_table(table) as batch:
            batch.drop_index(f'ix_{table}_organization_id')
            batch.drop_constraint(f'fk_{table}_organization', type_='foreignkey')
            batch.drop_column('organization_id')

    op.drop_table('organizations')
