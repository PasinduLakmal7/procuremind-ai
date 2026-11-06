"""Add supplier contacts, categories, delivery records and quality records

Revision ID: 0003_supplier_entities
Revises: 0002_supplier_fields
Create Date: 2026-11-06 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_supplier_entities'
down_revision = '0002_supplier_fields'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Contacts
    op.create_table(
        'supplier_contacts',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('supplier_id', sa.CHAR(length=36), sa.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('designation', sa.String(length=100), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 2. Categories
    op.create_table(
        'supplier_categories',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=100), nullable=False, index=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 3. Delivery Records
    op.create_table(
        'supplier_delivery_records',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('supplier_id', sa.CHAR(length=36), sa.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('po_reference', sa.String(length=100), nullable=False),
        sa.Column('promised_delivery_date', sa.DateTime(), nullable=False),
        sa.Column('actual_delivery_date', sa.DateTime(), nullable=False),
        sa.Column('on_time', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('delay_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_by', sa.CHAR(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 4. Quality Records
    op.create_table(
        'supplier_quality_records',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('supplier_id', sa.CHAR(length=36), sa.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('batch_reference', sa.String(length=100), nullable=False),
        sa.Column('defect_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('incident_severity', sa.String(length=50), nullable=False, server_default='NONE'),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('incident_details', sa.Text(), nullable=True),
        sa.Column('recorded_by', sa.CHAR(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('supplier_quality_records')
    op.drop_table('supplier_delivery_records')
    op.drop_table('supplier_categories')
    op.drop_table('supplier_contacts')

