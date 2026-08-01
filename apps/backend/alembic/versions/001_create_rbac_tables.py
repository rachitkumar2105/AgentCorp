"""
Create RBAC tables.

Revision ID: 001_create_rbac_tables
Revises:
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa


revision = "001_create_rbac_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_index(
        "ix_roles_name",
        "roles",
        ["name"],
        unique=True,
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_index(
        "ix_permissions_name",
        "permissions",
        ["name"],
        unique=True,
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_role",
        ),
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission",
        ),
    )


def downgrade():

    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_index("ix_permissions_name")
    op.drop_table("permissions")
    op.drop_index("ix_roles_name")
    op.drop_table("roles")