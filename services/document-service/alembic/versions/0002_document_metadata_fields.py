"""Add document metadata fields

Revision ID: 0002_doc_fields
Revises: 0001_initial
Create Date: 2026-11-06 12:55:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_doc_fields'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('document_records', sa.Column('file_name', sa.String(length=255), nullable=False, server_default='document.pdf'))
    op.add_column('document_records', sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('document_records', sa.Column('content_type', sa.String(length=100), nullable=False, server_default='application/pdf'))
    op.add_column('document_records', sa.Column('storage_path', sa.String(length=500), nullable=False, server_default=''))
    op.add_column('document_records', sa.Column('status', sa.String(length=50), nullable=False, server_default='UPLOADED'))
    op.add_column('document_records', sa.Column('purchase_request_id', sa.CHAR(36), nullable=True))
    op.add_column('document_records', sa.Column('supplier_id', sa.CHAR(36), nullable=True))
    op.add_column('document_records', sa.Column('quotation_id', sa.CHAR(36), nullable=True))
    op.add_column('document_records', sa.Column('checksum_sha256', sa.String(length=64), nullable=True))
    op.add_column('document_records', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_document_records_pr', 'document_records', ['purchase_request_id'])
    op.create_index('ix_document_records_sup', 'document_records', ['supplier_id'])

def downgrade() -> None:
    op.drop_index('ix_document_records_sup', table_name='document_records')
    op.drop_index('ix_document_records_pr', table_name='document_records')
    op.drop_column('document_records', 'updated_at')
    op.drop_column('document_records', 'checksum_sha256')
    op.drop_column('document_records', 'quotation_id')
    op.drop_column('document_records', 'supplier_id')
    op.drop_column('document_records', 'purchase_request_id')
    op.drop_column('document_records', 'status')
    op.drop_column('document_records', 'storage_path')
    op.drop_column('document_records', 'content_type')
    op.drop_column('document_records', 'file_size')
    op.drop_column('document_records', 'file_name')

