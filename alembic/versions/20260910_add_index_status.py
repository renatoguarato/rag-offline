"""Add document indexing status.

Revision ID: 20260910_index_status
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260910_index_status"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("api_key", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key"),
        )
        op.create_index("ix_tenants_api_key", "tenants", ["api_key"], unique=True)

    if not inspector.has_table("documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "index_status", sa.String(length=20), nullable=False, server_default="pending"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"], unique=False)
    elif "index_status" not in {column["name"] for column in inspector.get_columns("documents")}:
        op.add_column(
            "documents",
            sa.Column(
                "index_status", sa.String(length=20), nullable=False, server_default="pending"
            ),
        )


def downgrade() -> None:
    op.drop_column("documents", "index_status")
