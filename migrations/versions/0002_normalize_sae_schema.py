"""Normalize legacy SAE nullability and indexes.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "sae_diagnostics" not in inspector.get_table_names():
        return

    # Rebuild to make the SQLite schema exactly match SQLAlchemy metadata.
    op.create_table(
        "sae_diagnostics_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("description_pt", sa.Text(), nullable=False),
        sa.Column("intervention_en", sa.Text(), nullable=False),
        sa.Column("intervention_pt", sa.Text(), nullable=False),
        sa.Column("outcome_en", sa.Text(), nullable=False),
        sa.Column("outcome_pt", sa.Text(), nullable=False),
    )
    bind.execute(sa.text("""
        INSERT INTO sae_diagnostics_v2 (
            id, code, description_en, description_pt,
            intervention_en, intervention_pt, outcome_en, outcome_pt
        )
        SELECT
            id, code, description_en, description_pt,
            intervention_en, intervention_pt, outcome_en, outcome_pt
        FROM sae_diagnostics
    """))
    op.drop_table("sae_diagnostics")
    op.rename_table("sae_diagnostics_v2", "sae_diagnostics")
    op.create_index("ix_sae_diagnostics_code", "sae_diagnostics", ["code"], unique=True)


def downgrade() -> None:
    # 0001's logical data shape is the same; restoring the legacy nullable/index
    # quirks would only recreate a defect, so data/schema remains normalized.
    pass
