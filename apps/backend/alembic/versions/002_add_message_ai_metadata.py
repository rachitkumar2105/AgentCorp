"""
Add AI metadata columns to the messages table.

These columns store per-message provenance so that every assistant turn
carries full observability data (provider, model, tokens, finish_reason).

Revision ID: 002_add_message_ai_metadata
Revises: 001_create_rbac_tables
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa


revision = "002_add_message_ai_metadata"
down_revision = "001_create_rbac_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("provider", sa.String(100), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("model_used", sa.String(200), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("finish_reason", sa.String(50), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("total_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "total_tokens")
    op.drop_column("messages", "completion_tokens")
    op.drop_column("messages", "prompt_tokens")
    op.drop_column("messages", "finish_reason")
    op.drop_column("messages", "model_used")
    op.drop_column("messages", "provider")
