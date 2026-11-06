"""Add items, candidates, audit events and outbox tables

Revision ID: 0003_procurement_entities
Revises: 0002_procurement_quotes
Create Date: 2026-11-06 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_procurement_entities'
down_revision = '0002_procurement_quotes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. New columns on purchase_requests
    op.add_column('purchase_requests', sa.Column('evaluation_criteria', sa.Text(), nullable=True))

    # 2. purchase_request_items
    op.create_table(
        'purchase_request_items',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('purchase_request_id', sa.CHAR(length=36), sa.ForeignKey('purchase_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('specification', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False, server_default='UNITS'),
        sa.Column('target_unit_price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 3. candidate_suppliers
    op.create_table(
        'candidate_suppliers',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('purchase_request_id', sa.CHAR(length=36), sa.ForeignKey('purchase_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('supplier_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=False),
        sa.Column('supplier_email', sa.String(length=255), nullable=True),
        sa.Column('invitation_status', sa.String(length=50), nullable=False, server_default='INVITED'),
        sa.Column('invited_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 4. New columns on quotations
    op.add_column('quotations', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('quotations', sa.Column('submitted_date', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column('quotations', sa.Column('metadata_notes', sa.Text(), nullable=True))

    # 5. quotation_items
    op.create_table(
        'quotation_items',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('quotation_id', sa.CHAR(length=36), sa.ForeignKey('quotations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False, server_default='UNITS'),
        sa.Column('unit_price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('lead_time_days', sa.Integer(), nullable=False, server_default='14'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 6. procurement_audit_events
    op.create_table(
        'procurement_audit_events',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('purchase_request_id', sa.CHAR(length=36), sa.ForeignKey('purchase_requests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('performed_by', sa.CHAR(length=36), nullable=False),
        sa.Column('old_state', sa.Text(), nullable=True),
        sa.Column('new_state', sa.Text(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 7. outbox_events
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('aggregate_type', sa.String(length=100), nullable=False),
        sa.Column('aggregate_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_outbox_events_status', 'outbox_events', ['status'])

def downgrade() -> None:
    op.drop_table('outbox_events')
    op.drop_table('procurement_audit_events')
    op.drop_table('quotation_items')
    op.drop_column('quotations', 'metadata_notes')
    op.drop_column('quotations', 'submitted_date')
    op.drop_column('quotations', 'version')
    op.drop_table('candidate_suppliers')
    op.drop_table('purchase_request_items')
    op.drop_column('purchase_requests', 'evaluation_criteria')

