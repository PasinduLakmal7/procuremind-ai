"""Add procurement fields and quotations table

Revision ID: 0002_procurement_quotes
Revises: 0001_initial
Create Date: 2026-11-06 12:55:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_procurement_quotes'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Update purchase_requests
    op.add_column('purchase_requests', sa.Column('created_by_user_id', sa.CHAR(36), nullable=False, server_default='system'))
    op.add_column('purchase_requests', sa.Column('request_number', sa.String(length=50), nullable=False, server_default='PR-2026-0000'))
    op.add_column('purchase_requests', sa.Column('title', sa.String(length=255), nullable=False, server_default='Untitled Request'))
    op.add_column('purchase_requests', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('purchase_requests', sa.Column('category', sa.String(length=100), nullable=False, server_default='Raw Materials'))
    op.add_column('purchase_requests', sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'))
    op.add_column('purchase_requests', sa.Column('budget_limit', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('purchase_requests', sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'))
    op.add_column('purchase_requests', sa.Column('required_delivery_date', sa.DateTime(), nullable=True))
    op.add_column('purchase_requests', sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'))
    op.add_column('purchase_requests', sa.Column('items_json', sa.Text(), nullable=True))
    op.add_column('purchase_requests', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_purchase_requests_req_num', 'purchase_requests', ['request_number'])
    op.create_index('ix_purchase_requests_cat', 'purchase_requests', ['category'])
    op.create_index('ix_purchase_requests_status', 'purchase_requests', ['status'])

    # 2. Create quotations
    op.create_table(
        'quotations',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(36), nullable=False),
        sa.Column('purchase_request_id', sa.CHAR(36), sa.ForeignKey('purchase_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('supplier_id', sa.CHAR(36), nullable=False),
        sa.Column('quotation_number', sa.String(length=100), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('validity_date', sa.DateTime(), nullable=True),
        sa.Column('estimated_delivery_days', sa.Integer(), nullable=False, server_default='14'),
        sa.Column('warranty_terms', sa.String(length=255), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True, server_default='Net 30'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUBMITTED'),
        sa.Column('document_id', sa.CHAR(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_quotations_org', 'quotations', ['organization_id'])
    op.create_index('ix_quotations_pr', 'quotations', ['purchase_request_id'])
    op.create_index('ix_quotations_sup', 'quotations', ['supplier_id'])

def downgrade() -> None:
    op.drop_table('quotations')
    op.drop_index('ix_purchase_requests_status', table_name='purchase_requests')
    op.drop_index('ix_purchase_requests_cat', table_name='purchase_requests')
    op.drop_index('ix_purchase_requests_req_num', table_name='purchase_requests')
    op.drop_column('purchase_requests', 'updated_at')
    op.drop_column('purchase_requests', 'items_json')
    op.drop_column('purchase_requests', 'status')
    op.drop_column('purchase_requests', 'required_delivery_date')
    op.drop_column('purchase_requests', 'currency')
    op.drop_column('purchase_requests', 'budget_limit')
    op.drop_column('purchase_requests', 'priority')
    op.drop_column('purchase_requests', 'category')
    op.drop_column('purchase_requests', 'description')
    op.drop_column('purchase_requests', 'title')
    op.drop_column('purchase_requests', 'request_number')
    op.drop_column('purchase_requests', 'created_by_user_id')

