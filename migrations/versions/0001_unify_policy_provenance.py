"""Unify policy tables and add provenance/version metadata.

Revision ID: 0001
Revises: None
Create Date: 2026-09-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _create_sae_table() -> None:
    op.create_table(
        "sae_diagnostics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("description_pt", sa.Text(), nullable=False),
        sa.Column("intervention_en", sa.Text(), nullable=False),
        sa.Column("intervention_pt", sa.Text(), nullable=False),
        sa.Column("outcome_en", sa.Text(), nullable=False),
        sa.Column("outcome_pt", sa.Text(), nullable=False),
    )
    op.create_index("ix_sae_diagnostics_code", "sae_diagnostics", ["code"], unique=True)


def _create_policy_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_name", sa.String(length=20), nullable=False),
        sa.Column("directive", sa.String(), nullable=False),
        sa.Column("target_demographic", sa.String(), nullable=False),
        sa.Column("clinical_guideline", sa.Text(), nullable=False),
        sa.Column("source_title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_page", sa.String(length=40), nullable=True),
        sa.Column("source_publication_date", sa.String(length=10), nullable=True),
        sa.Column("effective_from", sa.String(length=10), nullable=True),
        sa.Column("effective_until", sa.String(length=10), nullable=True),
        sa.Column("last_clinical_review", sa.String(length=10), nullable=False),
        sa.Column("source_version", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("policy_name", "directive", name="uq_policy_directive"),
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "sae_diagnostics" not in tables:
        _create_sae_table()

    # Rebuild the policy table rather than ALTERing it piecemeal. This works on
    # SQLite and allows the same migration to upgrade the legacy two-table schema.
    if "public_health_policies" in tables:
        _create_policy_table("public_health_policies_v2")
        bind.execute(sa.text("""
            INSERT INTO public_health_policies_v2 (
                id, policy_name, directive, target_demographic, clinical_guideline,
                source_title, source_url, source_page, source_publication_date,
                effective_from, effective_until, last_clinical_review,
                source_version, status, review_notes
            )
            SELECT
                id, policy_name, directive, target_demographic, clinical_guideline,
                'Legacy imported policy record', '', NULL, NULL,
                NULL, NULL, '2026-09-07', 'legacy-pre-provenance',
                'needs_review', 'Imported by migration 0001; reseed from curated policy_data.py.'
            FROM public_health_policies
        """))

        if "pnaism_policies" in tables:
            bind.execute(sa.text("""
                INSERT INTO public_health_policies_v2 (
                    policy_name, directive, target_demographic, clinical_guideline,
                    source_title, source_url, source_page, source_publication_date,
                    effective_from, effective_until, last_clinical_review,
                    source_version, status, review_notes
                )
                SELECT
                    'PNAISM', directive, target_demographic, clinical_guideline,
                    'Legacy imported PNAISM record', '', NULL, NULL,
                    NULL, NULL, '2026-09-07', 'legacy-pre-provenance',
                    'needs_review', 'Imported by migration 0001; reseed from curated policy_data.py.'
                FROM pnaism_policies
            """))

        op.drop_table("public_health_policies")
        op.rename_table("public_health_policies_v2", "public_health_policies")
    else:
        _create_policy_table("public_health_policies")
        if "pnaism_policies" in tables:
            bind.execute(sa.text("""
                INSERT INTO public_health_policies (
                    policy_name, directive, target_demographic, clinical_guideline,
                    source_title, source_url, last_clinical_review,
                    source_version, status, review_notes
                )
                SELECT
                    'PNAISM', directive, target_demographic, clinical_guideline,
                    'Legacy imported PNAISM record', '', '2026-09-07',
                    'legacy-pre-provenance', 'needs_review',
                    'Imported by migration 0001; reseed from curated policy_data.py.'
                FROM pnaism_policies
            """))

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "pnaism_policies" in tables:
        op.drop_table("pnaism_policies")

    op.create_index(
        "ix_public_health_policies_policy_name",
        "public_health_policies",
        ["policy_name"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "public_health_policies" not in tables:
        return

    op.create_table(
        "pnaism_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("directive", sa.String(), nullable=False),
        sa.Column("target_demographic", sa.String(), nullable=False),
        sa.Column("clinical_guideline", sa.Text(), nullable=False),
    )
    bind.execute(sa.text("""
        INSERT INTO pnaism_policies (directive, target_demographic, clinical_guideline)
        SELECT directive, target_demographic, clinical_guideline
        FROM public_health_policies WHERE policy_name = 'PNAISM'
        ORDER BY id
    """))

    op.create_table(
        "public_health_policies_legacy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_name", sa.String(), nullable=False),
        sa.Column("directive", sa.String(), nullable=False),
        sa.Column("target_demographic", sa.String(), nullable=False),
        sa.Column("clinical_guideline", sa.Text(), nullable=False),
    )
    bind.execute(sa.text("""
        INSERT INTO public_health_policies_legacy
            (policy_name, directive, target_demographic, clinical_guideline)
        SELECT policy_name, directive, target_demographic, clinical_guideline
        FROM public_health_policies WHERE policy_name <> 'PNAISM'
        ORDER BY id
    """))
    op.drop_index("ix_public_health_policies_policy_name", table_name="public_health_policies")
    op.drop_table("public_health_policies")
    op.rename_table("public_health_policies_legacy", "public_health_policies")
    op.create_index(
        "ix_public_health_policies_policy_name",
        "public_health_policies",
        ["policy_name"],
        unique=False,
    )
