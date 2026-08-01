"""
Create tool execution logs migration.

Revision ID: 003_create_tool_execution_logs
Revises: 002_add_message_ai_metadata
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa

revision = "003_create_tool_execution_logs"
down_revision = "002_add_message_ai_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_execution_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("latency_seconds", sa.Float(), nullable=False),
        sa.Column("arguments", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tool_execution_logs")
