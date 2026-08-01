"""
Create agent engine goals and execution schemas in Alembic migration.

Revision ID: 007_create_agent_tables
Revises: 006_create_workflow_tables
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa

revision = "007_create_agent_tables"
down_revision = "006_create_workflow_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create agent_goals table
    op.create_table(
        "agent_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(50), default="medium", nullable=False),
        sa.Column("status", sa.String(50), default="PENDING", nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=True),
        sa.Column("success_criteria", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    # 2. Create goal_tasks table
    op.create_table(
        "goal_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("parent_task_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), default="PENDING", nullable=False),
        sa.Column("priority", sa.String(50), default="medium", nullable=False),
        sa.Column("order", sa.Integer(), default=0, nullable=False),
        sa.Column("estimated_cost", sa.Float(), default=0.0, nullable=False),
        sa.Column("estimated_tokens", sa.Integer(), default=0, nullable=False),
        sa.Column("execution_type", sa.String(100), default="AI", nullable=False),
        sa.Column("retry_count", sa.Integer(), default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["agent_goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["goal_tasks.id"], ondelete="SET NULL"),
    )

    # 3. Create agent_executions table
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), default="RUNNING", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("execution_context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["agent_goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("agent_executions")
    op.drop_table("goal_tasks")
    op.drop_table("agent_goals")
