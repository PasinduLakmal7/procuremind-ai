"""Add supplier profile fields

Revision ID: 0002_supplier_fields
Revises: 0001_initial
Create Date: 2026-11-06 12:50:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_supplier_fields'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('suppliers', sa.Column('company_name', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('suppliers', sa.Column('contact_email', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('suppliers', sa.Column('contact_phone', sa.String(length=50), nullable=True))
    op.add_column('suppliers', sa.Column('address', sa.String(length=500), nullable=True))
    op.add_column('suppliers', sa.Column('city', sa.String(length=100), nullable=False, server_default='Colombo'))
    op.add_column('suppliers', sa.Column('country', sa.String(length=100), nullable=False, server_default='Sri Lanka'))
    op.add_column('suppliers', sa.Column('category', sa.String(length=100), nullable=False, server_default='Raw Materials'))
    op.add_column('suppliers', sa.Column('tax_id', sa.String(length=100), nullable=True))
    op.add_column('suppliers', sa.Column('rating', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('suppliers', sa.Column('tier', sa.String(length=50), nullable=False, server_default='TIER_2'))
    op.add_column('suppliers', sa.Column('compliance_status', sa.String(length=50), nullable=False, server_default='VERIFIED'))
    op.add_column('suppliers', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('suppliers', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_suppliers_company_name', 'suppliers', ['company_name'])
    op.create_index('ix_suppliers_category', 'suppliers', ['category'])

def downgrade() -> None:
    op.drop_index('ix_suppliers_category', table_name='suppliers')
    op.drop_index('ix_suppliers_company_name', table_name='suppliers')
    op.drop_column('suppliers', 'updated_at')
    op.drop_column('suppliers', 'is_active')
    op.drop_column('suppliers', 'compliance_status')
    op.drop_column('suppliers', 'tier')
    op.drop_column('suppliers', 'rating')
    op.drop_column('suppliers', 'tax_id')
    op.drop_column('suppliers', 'category')
    op.drop_column('suppliers', 'country')
    op.drop_column('suppliers', 'city')
    op.drop_column('suppliers', 'address')
    op.drop_column('suppliers', 'contact_phone')
    op.drop_column('suppliers', 'contact_email')
    op.drop_column('suppliers', 'company_name')

