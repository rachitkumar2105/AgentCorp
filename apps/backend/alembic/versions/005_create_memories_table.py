"""
Create memories schema in Alembic migration.

Revision ID: 005_create_memories_table
Revises: 004_create_knowledge_tables
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa

revision = "005_create_memories_table"
down_revision = "004_create_knowledge_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("importance_score", sa.Float(), default=0.5, nullable=False),
        sa.Column("confidence_score", sa.Float(), default=0.5, nullable=False),
        sa.Column("source", sa.String(100), default="extraction", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("memories")
