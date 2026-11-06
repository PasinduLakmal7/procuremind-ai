"""Add workflow execution fields and step logs

Revision ID: 0002_orchestrator_checkpoints
Revises: 0001_initial
Create Date: 2026-11-06 13:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_orchestrator_checkpoints'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('agent_workflow_executions', sa.Column('correlation_id', sa.CHAR(36), nullable=False, server_default=''))
    op.add_column('agent_workflow_executions', sa.Column('purchase_request_id', sa.CHAR(36), nullable=False, server_default=''))
    op.add_column('agent_workflow_executions', sa.Column('document_id', sa.CHAR(36), nullable=True))
    op.add_column('agent_workflow_executions', sa.Column('supplier_id', sa.CHAR(36), nullable=True))
    op.add_column('agent_workflow_executions', sa.Column('workflow_name', sa.String(100), nullable=False, server_default='PROCUREMENT_EVALUATION'))
    op.add_column('agent_workflow_executions', sa.Column('status', sa.String(50), nullable=False, server_default='STARTED'))
    op.add_column('agent_workflow_executions', sa.Column('current_step', sa.String(100), nullable=False, server_default='document_intelligence'))
    op.add_column('agent_workflow_executions', sa.Column('requires_human_review', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_workflow_executions', sa.Column('human_review_reason', sa.Text(), nullable=True))
    op.add_column('agent_workflow_executions', sa.Column('state_snapshot', sa.Text(), nullable=False, server_default='{}'))
    op.add_column('agent_workflow_executions', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_agent_wf_pr', 'agent_workflow_executions', ['purchase_request_id'])

    op.create_table(
        'workflow_step_logs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('workflow_id', sa.CHAR(36), sa.ForeignKey('agent_workflow_executions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', sa.CHAR(36), nullable=False),
        sa.Column('step_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('workflow_step_logs')
    op.drop_index('ix_agent_wf_pr', table_name='agent_workflow_executions')
    op.drop_column('agent_workflow_executions', 'updated_at')
    op.drop_column('agent_workflow_executions', 'state_snapshot')
    op.drop_column('agent_workflow_executions', 'human_review_reason')
    op.drop_column('agent_workflow_executions', 'requires_human_review')
    op.drop_column('agent_workflow_executions', 'current_step')
    op.drop_column('agent_workflow_executions', 'status')
    op.drop_column('agent_workflow_executions', 'workflow_name')
    op.drop_column('agent_workflow_executions', 'supplier_id')
    op.drop_column('agent_workflow_executions', 'document_id')
    op.drop_column('agent_workflow_executions', 'purchase_request_id')
    op.drop_column('agent_workflow_executions', 'correlation_id')

