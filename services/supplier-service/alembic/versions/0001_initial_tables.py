"""Initial migration for supplier-service

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-05 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'suppliers',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_suppliers_org', 'suppliers', ['organization_id'])

def downgrade() -> None:
    op.drop_table('suppliers')
