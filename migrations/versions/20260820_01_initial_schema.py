"""Crée le schéma relationnel initial.

Revision ID: 20260820_01
Revises: None
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("rda", sa.String(length=255), nullable=False),
        sa.Column("possession", sa.Date(), nullable=True),
        sa.Column("type_app", sa.String(length=50), nullable=False),
        sa.Column("hosting", sa.String(length=50), nullable=False),
        sa.Column("criticite", sa.Integer(), nullable=False),
        sa.Column("disponibilite", sa.String(length=2), nullable=False),
        sa.Column("integrite", sa.String(length=2), nullable=False),
        sa.Column("confidentialite", sa.String(length=2), nullable=False),
        sa.Column("perennite", sa.String(length=2), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("answered_questions", sa.Integer(), nullable=True),
        sa.Column("last_evaluation", sa.DateTime(), nullable=True),
        sa.Column("responses", sa.JSON(), nullable=False),
        sa.Column("comments", sa.JSON(), nullable=False),
        sa.Column("evaluator_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("answered_questions", sa.Integer(), nullable=False),
        sa.Column("last_evaluation", sa.DateTime(), nullable=False),
        sa.Column("evaluator_name", sa.String(length=255), nullable=False),
        sa.Column("responses", sa.JSON(), nullable=False),
        sa.Column("comments", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_table("applications")
