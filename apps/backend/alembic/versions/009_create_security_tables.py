"""create security tables

Revision ID: 009_create_security_tables
Revises: 008_create_multi_agent_tables
Create Date: 2026-08-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_create_security_tables'
down_revision = '008_create_multi_agent_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 1. security_policy table
    op.create_table(
        'security_policy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('resource', sa.String(length=256), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('effect', sa.String(length=32), nullable=False),
        sa.Column('condition', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_policy_id'), 'security_policy', ['id'], unique=False)
    op.create_index(op.f('ix_security_policy_name'), 'security_policy', ['name'], unique=True)

    # 2. quota_usage table
    op.create_table(
        'quota_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('quota_type', sa.String(length=64), nullable=False),
        sa.Column('used', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('limit', sa.BigInteger(), nullable=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quota_usage_id'), 'quota_usage', ['id'], unique=False)
    op.create_index(op.f('ix_quota_usage_entity_id'), 'quota_usage', ['entity_id'], unique=False)
    op.create_index(op.f('ix_quota_usage_quota_type'), 'quota_usage', ['quota_type'], unique=False)

    # 3. audit_security_event table
    op.create_table(
        'audit_security_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_security_event_id'), 'audit_security_event', ['id'], unique=False)
    op.create_index(op.f('ix_audit_security_event_timestamp'), 'audit_security_event', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_audit_security_event_timestamp'), table_name='audit_security_event')
    op.drop_index(op.f('ix_audit_security_event_id'), table_name='audit_security_event')
    op.drop_table('audit_security_event')

    op.drop_index(op.f('ix_quota_usage_quota_type'), table_name='quota_usage')
    op.drop_index(op.f('ix_quota_usage_entity_id'), table_name='quota_usage')
    op.drop_index(op.f('ix_quota_usage_id'), table_name='quota_usage')
    op.drop_table('quota_usage')

    op.drop_index(op.f('ix_security_policy_name'), table_name='security_policy')
    op.drop_index(op.f('ix_security_policy_id'), table_name='security_policy')
    op.drop_table('security_policy')
