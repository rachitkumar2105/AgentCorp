"""add runtime_version to conversations

Revision ID: 010_add_runtime_version_to_conversations
Revises: 009_create_security_tables
Create Date: 2026-08-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "010_add_runtime_version_to_conversations"
down_revision = "009_create_security_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "runtime_version",
            sa.String(length=50),
            nullable=False,
            server_default="AgentCorp V1",
        ),
    )
    op.alter_column("conversations", "runtime_version", server_default=None)


def downgrade() -> None:
    op.drop_column("conversations", "runtime_version")
