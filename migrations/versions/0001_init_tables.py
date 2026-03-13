"""init tables

Revision ID: 0001_init
Revises:
Create Date: 2026-03-03

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_case",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=True),
        sa.Column(
            "is_quarantined",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_test_case_external_id", "test_case", ["external_id"], unique=True
    )

    op.create_table(
        "test_run",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("branch", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "test_result",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["test_run.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_test_result_run_id", "test_result", ["run_id"])
    op.create_index("ix_test_result_external_id", "test_result", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_test_result_external_id", table_name="test_result")
    op.drop_index("ix_test_result_run_id", table_name="test_result")
    op.drop_table("test_result")

    op.drop_table("test_run")

    op.drop_index("ix_test_case_external_id", table_name="test_case")
    op.drop_table("test_case")
