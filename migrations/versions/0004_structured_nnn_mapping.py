"""Add structured current-edition NANDA/NIC/NOC mapping metadata.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "sae_diagnostics" not in inspector.get_table_names():
        return
    with op.batch_alter_table("sae_diagnostics") as batch:
        batch.add_column(sa.Column("nanda_edition", sa.Text(), nullable=True))
        batch.add_column(sa.Column("nanda_domain", sa.String(length=4), nullable=True))
        batch.add_column(sa.Column("nanda_class", sa.String(length=4), nullable=True))
        batch.add_column(sa.Column("nanda_source_page", sa.String(length=12), nullable=True))
        batch.add_column(sa.Column("nanda_pdf_page", sa.String(length=12), nullable=True))
        batch.add_column(sa.Column("nic_edition", sa.Text(), nullable=True))
        batch.add_column(sa.Column("nic_code", sa.String(length=8), nullable=True))
        batch.add_column(sa.Column("nic_label_en", sa.Text(), nullable=True))
        batch.add_column(sa.Column("nic_label_pt", sa.Text(), nullable=True))
        batch.add_column(sa.Column("noc_edition", sa.Text(), nullable=True))
        batch.add_column(sa.Column("noc_code", sa.String(length=8), nullable=True))
        batch.add_column(sa.Column("noc_label_en", sa.Text(), nullable=True))
        batch.add_column(sa.Column("noc_label_pt", sa.Text(), nullable=True))
        batch.add_column(sa.Column("mapping_confidence", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("mapping_reference", sa.Text(), nullable=True))
        batch.add_column(sa.Column("mapping_rationale", sa.Text(), nullable=True))
        batch.create_index("ix_sae_diagnostics_nic_code", ["nic_code"], unique=False)
        batch.create_index("ix_sae_diagnostics_noc_code", ["noc_code"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "sae_diagnostics" not in inspector.get_table_names():
        return
    with op.batch_alter_table("sae_diagnostics") as batch:
        batch.drop_index("ix_sae_diagnostics_noc_code")
        batch.drop_index("ix_sae_diagnostics_nic_code")
        for name in (
            "mapping_rationale", "mapping_reference", "mapping_confidence",
            "noc_label_pt", "noc_label_en", "noc_code", "noc_edition",
            "nic_label_pt", "nic_label_en", "nic_code", "nic_edition",
            "nanda_pdf_page", "nanda_source_page", "nanda_class", "nanda_domain", "nanda_edition",
        ):
            batch.drop_column(name)
