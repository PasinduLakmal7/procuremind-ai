"""Add risk_assessments table

Revision ID: 0002_risk_assessments
Revises: 0001_initial
Create Date: 2026-11-06 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_risk_assessments'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(36), nullable=False),
        sa.Column('supplier_id', sa.CHAR(36), nullable=False),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_category', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('data_sufficiency', sa.String(50), nullable=False),
        sa.Column('observation_count', sa.Integer(), nullable=False),
        sa.Column('metrics_breakdown', sa.Text(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_risk_assessments_org', 'risk_assessments', ['organization_id'])
    op.create_index('ix_risk_assessments_supplier', 'risk_assessments', ['supplier_id'])
    op.create_index('ix_risk_assessments_category', 'risk_assessments', ['risk_category'])

def downgrade() -> None:
    op.drop_table('risk_assessments')

