"""Add SAE mapping provenance, normalize NANDA codes, and policy evidence level.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "sae_diagnostics" in tables:
        with op.batch_alter_table("sae_diagnostics") as batch:
            batch.add_column(sa.Column("mapping_status", sa.String(length=30), nullable=False, server_default="suggested_unverified"))
            batch.add_column(sa.Column("mapping_methodology", sa.Text(), nullable=False, server_default="Local curated/suggested NANDA-to-NIC/NOC linkage; not an official crosswalk."))
            batch.add_column(sa.Column("mapping_review_date", sa.String(length=10), nullable=True))
            batch.add_column(sa.Column("mapping_notes", sa.Text(), nullable=True))
        bind.execute(sa.text("UPDATE sae_diagnostics SET code = printf('%05d', CAST(code AS INTEGER)) WHERE code GLOB '[0-9]*'"))
    if "public_health_policies" in tables:
        with op.batch_alter_table("public_health_policies") as batch:
            batch.add_column(sa.Column("evidence_level", sa.String(length=30), nullable=False, server_default="policy_level"))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "public_health_policies" in tables:
        with op.batch_alter_table("public_health_policies") as batch:
            batch.drop_column("evidence_level")
    if "sae_diagnostics" in tables:
        with op.batch_alter_table("sae_diagnostics") as batch:
            batch.drop_column("mapping_notes")
            batch.drop_column("mapping_review_date")
            batch.drop_column("mapping_methodology")
            batch.drop_column("mapping_status")
