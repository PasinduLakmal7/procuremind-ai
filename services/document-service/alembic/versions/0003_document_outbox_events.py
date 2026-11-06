"""Add document outbox events table

Revision ID: 0003_doc_outbox
Revises: 0002_doc_fields
Create Date: 2026-11-06 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_doc_outbox'
down_revision = '0002_doc_fields'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'document_outbox_events',
        sa.Column('id', sa.CHAR(length=36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('aggregate_type', sa.String(length=100), nullable=False, server_default='DocumentRecord'),
        sa.Column('aggregate_id', sa.CHAR(length=36), nullable=False, index=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_doc_outbox_status', 'document_outbox_events', ['status'])

def downgrade() -> None:
    op.drop_table('document_outbox_events')

