"""
Create workflow schemas in Alembic migration.

Revision ID: 006_create_workflow_tables
Revises: 005_create_memories_table
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa

revision = "006_create_workflow_tables"
down_revision = "005_create_memories_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), default="1.0.0", nullable=False),
        sa.Column("status", sa.String(50), default="draft", nullable=False),
        sa.Column("enabled", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    # 2. Create workflow_nodes table
    op.create_table(
        "workflow_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("node_type", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("timeout", sa.Float(), default=60.0, nullable=False),
        sa.Column("retry_policy", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
    )

    # 3. Create workflow_edges table
    op.create_table(
        "workflow_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("source_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=False),
        sa.Column("transition_condition", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_node_id"], ["workflow_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_node_id"], ["workflow_nodes.id"], ondelete="CASCADE"),
    )

    # 4. Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), default="PENDING", nullable=False),
        sa.Column("current_node_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("execution_context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
    )

    # 5. Create workflow_steps table
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("execution_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), default="RUNNING", nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("latency_seconds", sa.Float(), nullable=True),
        sa.Column("retries", sa.Integer(), default=0, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["workflow_executions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["node_id"], ["workflow_nodes.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("workflow_steps")
    op.drop_table("workflow_executions")
    op.drop_table("workflow_edges")
    op.drop_table("workflow_nodes")
    op.drop_table("workflows")
