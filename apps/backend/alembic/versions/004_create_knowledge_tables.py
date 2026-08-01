"""
Create knowledge base, document and chunk schemas in Alembic migration.

Revision ID: 004_create_knowledge_tables
Revises: 003_create_tool_execution_logs
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa

revision = "004_create_knowledge_tables"
down_revision = "003_create_tool_execution_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create knowledge_bases table
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), default="active", nullable=False),
        sa.Column("visibility", sa.String(50), default="private", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    # 2. Create knowledge_documents table
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("knowledge_base_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("status", sa.String(50), default="active", nullable=False),
        sa.Column("processing_status", sa.String(50), default="UPLOADED", nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
    )
    op.create_index("ix_knowledge_documents_checksum", "knowledge_documents", ["checksum"])

    # 3. Create knowledge_chunks table
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("embedding_status", sa.String(50), default="PENDING", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_index("ix_knowledge_documents_checksum", "knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_table("knowledge_bases")
