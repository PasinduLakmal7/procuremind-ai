"""Add quotation extractions and correction audits tables

Revision ID: 0004_doc_extractions
Revises: 0003_doc_outbox
Create Date: 2026-11-06 13:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_doc_extractions'
down_revision = '0003_doc_outbox'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'quotation_extractions',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('document_id', sa.CHAR(length=36), sa.ForeignKey('document_records.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('purchase_request_id', sa.CHAR(length=36), nullable=True, index=True),
        sa.Column('supplier_id', sa.CHAR(length=36), nullable=True, index=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('quotation_number', sa.String(length=100), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('arithmetic_valid', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', sa.CHAR(length=36), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('structured_data_json', sa.Text(), nullable=False),
        sa.Column('flagged_reasons_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'extraction_correction_audits',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('extraction_id', sa.CHAR(length=36), sa.ForeignKey('quotation_extractions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('corrected_by', sa.CHAR(length=36), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('extraction_correction_audits')
    op.drop_table('quotation_extractions')

