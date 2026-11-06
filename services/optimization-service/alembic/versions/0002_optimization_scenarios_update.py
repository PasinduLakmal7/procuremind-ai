"""Update optimization_scenarios schema

Revision ID: 0002_opt_scenarios_update
Revises: 0001_initial
Create Date: 2026-11-06 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_opt_scenarios_update'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('optimization_scenarios', sa.Column('request_id', sa.CHAR(36), nullable=False, server_default=''))
    op.add_column('optimization_scenarios', sa.Column('algorithm', sa.String(100), nullable=False, server_default='mcda_weighted_scoring_v1.0'))
    op.add_column('optimization_scenarios', sa.Column('total_evaluated', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('optimization_scenarios', sa.Column('top_supplier_id', sa.CHAR(36), nullable=True))
    op.add_column('optimization_scenarios', sa.Column('weights_json', sa.Text(), nullable=False, server_default='{}'))
    op.add_column('optimization_scenarios', sa.Column('rankings_json', sa.Text(), nullable=False, server_default='[]'))
    op.add_column('optimization_scenarios', sa.Column('decision_summary', sa.Text(), nullable=True))
    op.create_index('ix_optimization_scenarios_request', 'optimization_scenarios', ['request_id'])

def downgrade() -> None:
    op.drop_index('ix_optimization_scenarios_request', 'optimization_scenarios')
    op.drop_column('optimization_scenarios', 'decision_summary')
    op.drop_column('optimization_scenarios', 'rankings_json')
    op.drop_column('optimization_scenarios', 'weights_json')
    op.drop_column('optimization_scenarios', 'top_supplier_id')
    op.drop_column('optimization_scenarios', 'total_evaluated')
    op.drop_column('optimization_scenarios', 'algorithm')
    op.drop_column('optimization_scenarios', 'request_id')

