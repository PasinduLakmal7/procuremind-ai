"""Initial identity tables

Revision ID: 0001_initial_identity
Revises: 
Create Date: 2026-11-05 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '0001_initial_identity'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('registration_number', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=False, server_default='Manufacturing'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_organizations_name', 'organizations', ['name'], unique=True)

    # 2. roles
    op.create_table(
        'roles',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
    )
    op.create_index('ix_roles_name', 'roles', ['name'], unique=True)

    # Seed initial roles
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.CHAR(36)),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
    )
    op.bulk_insert(
        roles_table,
        [
            {'id': str(uuid.uuid4()), 'name': 'admin', 'description': 'System administrator'},
            {'id': str(uuid.uuid4()), 'name': 'procurement_manager', 'description': 'Procurement manager with approval authority'},
            {'id': str(uuid.uuid4()), 'name': 'procurement_officer', 'description': 'Procurement operational officer'},
            {'id': str(uuid.uuid4()), 'name': 'supply_chain_analyst', 'description': 'Supply chain risk analyst'},
            {'id': str(uuid.uuid4()), 'name': 'auditor', 'description': 'Compliance and audit reviewer'},
        ]
    )

    # 3. users
    op.create_table(
        'users',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('organization_id', sa.CHAR(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_organization_id', 'users', ['organization_id'])

    # 4. user_roles
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.CHAR(36), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    )

    # 5. refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_refresh_tokens_jti', 'refresh_tokens', ['jti'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    # 6. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), nullable=True),
        sa.Column('organization_id', sa.CHAR(36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUCCESS'),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('organizations')

