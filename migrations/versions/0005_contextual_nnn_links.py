"""Add context-aware one-to-many NIC/NOC links.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "sae_classification_links" not in inspector.get_table_names():
        op.create_table(
            "sae_classification_links",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sae_diagnostic_id", sa.Integer(), sa.ForeignKey("sae_diagnostics.id", ondelete="CASCADE"), nullable=False),
            sa.Column("classification", sa.String(length=3), nullable=False),
            sa.Column("code", sa.String(length=8), nullable=False),
            sa.Column("label_en", sa.Text(), nullable=False),
            sa.Column("label_pt", sa.Text(), nullable=False),
            sa.Column("edition", sa.Text(), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("applicability", sa.Text(), nullable=False),
            sa.Column("confidence", sa.String(length=20), nullable=False),
            sa.Column("verification_status", sa.String(length=40), nullable=False),
            sa.Column("source_language", sa.String(length=10), nullable=False, server_default="es"),
            sa.Column("source_reference", sa.Text(), nullable=False),
            sa.Column("source_page", sa.String(length=40), nullable=True),
            sa.Column("review_date", sa.String(length=10), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
            sa.UniqueConstraint("sae_diagnostic_id", "classification", "code", "role", name="uq_sae_classification_link"),
        )
        op.create_index("ix_sae_classification_links_sae_diagnostic_id", "sae_classification_links", ["sae_diagnostic_id"])
        op.create_index("ix_sae_classification_links_classification", "sae_classification_links", ["classification"])
        op.create_index("ix_sae_classification_links_code", "sae_classification_links", ["code"])

    # Backfill one primary NIC and one primary NOC from the Pass-4 compatibility fields.
    # The Pass-5 seed replaces/augments these with curated contextual alternatives.
    bind = op.get_bind()
    if "sae_diagnostics" in sa.inspect(bind).get_table_names():
        bind.execute(sa.text("""
            INSERT OR IGNORE INTO sae_classification_links
            (sae_diagnostic_id, classification, code, label_en, label_pt, edition, role,
             applicability, confidence, verification_status, source_language, source_reference,
             source_page, review_date, notes, sort_order)
            SELECT id, 'NIC', nic_code, nic_label_en, nic_label_pt, nic_edition, 'primary',
                   'Compatibility primary migrated from the pre-contextual mapping.',
                   COALESCE(mapping_confidence, 'moderate'), 'migrated_primary', 'es',
                   COALESCE(mapping_reference, 'Legacy Pass-4 mapping'), NULL,
                   COALESCE(mapping_review_date, '2026-09-07'),
                   'Run seed_sae.py to install the curated Pass-5 contextual link set.', 0
            FROM sae_diagnostics
            WHERE nic_code IS NOT NULL AND nic_label_en IS NOT NULL AND nic_label_pt IS NOT NULL AND nic_edition IS NOT NULL
        """))
        bind.execute(sa.text("""
            INSERT OR IGNORE INTO sae_classification_links
            (sae_diagnostic_id, classification, code, label_en, label_pt, edition, role,
             applicability, confidence, verification_status, source_language, source_reference,
             source_page, review_date, notes, sort_order)
            SELECT id, 'NOC', noc_code, noc_label_en, noc_label_pt, noc_edition, 'primary',
                   'Compatibility primary migrated from the pre-contextual mapping.',
                   COALESCE(mapping_confidence, 'moderate'), 'migrated_primary', 'es',
                   COALESCE(mapping_reference, 'Legacy Pass-4 mapping'), NULL,
                   COALESCE(mapping_review_date, '2026-09-07'),
                   'Run seed_sae.py to install the curated Pass-5 contextual link set.', 0
            FROM sae_diagnostics
            WHERE noc_code IS NOT NULL AND noc_label_en IS NOT NULL AND noc_label_pt IS NOT NULL AND noc_edition IS NOT NULL
        """))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "sae_classification_links" not in inspector.get_table_names():
        return
    op.drop_index("ix_sae_classification_links_code", table_name="sae_classification_links")
    op.drop_index("ix_sae_classification_links_classification", table_name="sae_classification_links")
    op.drop_index("ix_sae_classification_links_sae_diagnostic_id", table_name="sae_classification_links")
    op.drop_table("sae_classification_links")
