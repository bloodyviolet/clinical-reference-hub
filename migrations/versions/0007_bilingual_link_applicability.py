"""Add bilingual applicability to contextual NIC/NOC links.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-08

The legacy ``applicability`` column remains the EN compatibility
field.  This revision adds explicit EN-GB and reviewed PT-BR fields.

The migration validates the expected 627-link F-04 source corpus
before altering the schema.  Alternative PT-BR values come only from
the reviewed, hash-pinned F-04 artifact packaged with this release.
"""

from hashlib import sha256
import json
from pathlib import Path

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


REVIEW_SHA256 = (
    "115a7658c4ec8a4b0f97d15306d45d9e"
    "bf9a3f41ea2990e502134911b65ba399"
)

PRIMARY_EN = (
    "Compatibility primary selected for the diagnosis; "
    "consider alternative/context-specific links before "
    "finalising a care plan."
)

PRIMARY_PT = (
    "Mapeamento primário de compatibilidade selecionado para "
    "o diagnóstico; considerar vínculos alternativos/específicos "
    "ao contexto antes de finalizar o plano de cuidados."
)


def _review_mapping() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]

    path = (
        root
        / "data"
        / "f04_review"
        / "f04_applicability_review_20260908.json"
    )

    raw = path.read_bytes()

    actual = sha256(raw).hexdigest()

    if actual != REVIEW_SHA256:
        raise RuntimeError(
            "F-04 applicability review artifact hash mismatch: "
            f"{actual}"
        )

    payload = json.loads(
        raw.decode("utf-8")
    )

    items = payload.get("items", [])

    mapping = {
        item["applicability_en"].strip():
        item["applicability_pt"].strip()
        for item in items
    }

    if len(items) != 50 or len(mapping) != 50:
        raise RuntimeError(
            "F-04 review artifact must contain exactly "
            "50 unique EN→PT-BR mappings."
        )

    if not all(mapping.values()):
        raise RuntimeError(
            "F-04 review artifact contains blank PT-BR text."
        )

    return mapping


def _validated_rows(
    connection,
    translations: dict[str, str],
):
    rows = connection.execute(
        sa.text(
            """
            SELECT id, role, applicability
            FROM sae_classification_links
            ORDER BY id
            """
        )
    ).mappings().all()

    # Fresh and legacy schema-only migrations may legitimately
    # reach revision 0006 before SAE classification links have
    # been seeded.  There is no existing applicability content
    # to translate in that state, so allow the schema migration
    # to proceed.  Any non-empty link table remains fail-closed
    # against the complete reviewed F-04 corpus below.
    if not rows:
        return []

    if len(rows) != 627:
        raise RuntimeError(
            "F-04 expected either an empty schema-only "
            "classification-link table or exactly 627 reviewed "
            "classification links; "
            f"found {len(rows)}."
        )

    primary = 0
    alternative = 0
    alternative_strings = set()
    prepared = []

    for row in rows:
        role = row["role"]
        applicability = row["applicability"]

        if not applicability:
            raise RuntimeError(
                f"Blank applicability on link id={row['id']}"
            )

        if role == "primary":
            primary += 1

            if applicability != PRIMARY_EN:
                raise RuntimeError(
                    "Unexpected primary applicability on "
                    f"link id={row['id']}: "
                    f"{applicability!r}"
                )

            pt = PRIMARY_PT

        elif role == "alternative":
            alternative += 1
            alternative_strings.add(applicability)

            try:
                pt = translations[applicability]
            except KeyError as exc:
                raise RuntimeError(
                    "Unreviewed alternative applicability on "
                    f"link id={row['id']}: "
                    f"{applicability!r}"
                ) from exc

        else:
            raise RuntimeError(
                f"Unexpected link role on id={row['id']}: "
                f"{role!r}"
            )

        prepared.append(
            {
                "id": row["id"],
                "en": applicability,
                "pt": pt,
            }
        )

    if primary != 554:
        raise RuntimeError(
            f"F-04 expected 554 primary links; found {primary}."
        )

    if alternative != 73:
        raise RuntimeError(
            "F-04 expected 73 alternative links; "
            f"found {alternative}."
        )

    if len(alternative_strings) != 50:
        raise RuntimeError(
            "F-04 expected 50 unique alternative "
            "applicability strings; "
            f"found {len(alternative_strings)}."
        )

    if alternative_strings != set(translations):
        missing = alternative_strings - set(translations)
        extra = set(translations) - alternative_strings

        raise RuntimeError(
            "F-04 translation/source mismatch. "
            f"missing={sorted(missing)!r}; "
            f"extra={sorted(extra)!r}"
        )

    return prepared


def upgrade() -> None:
    connection = op.get_bind()

    translations = _review_mapping()

    # Critical safety property:
    # validate the complete existing dataset BEFORE DDL.
    prepared = _validated_rows(
        connection,
        translations,
    )

    with op.batch_alter_table(
        "sae_classification_links"
    ) as batch:
        batch.add_column(
            sa.Column(
                "applicability_en",
                sa.Text(),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column(
                "applicability_pt",
                sa.Text(),
                nullable=True,
            )
        )

    update = sa.text(
        """
        UPDATE sae_classification_links
        SET
            applicability_en = :en,
            applicability_pt = :pt
        WHERE id = :id
        """
    )

    for row in prepared:
        connection.execute(
            update,
            row,
        )

    invalid = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM sae_classification_links
            WHERE
                applicability_en IS NULL
                OR TRIM(applicability_en) = ''
                OR applicability_pt IS NULL
                OR TRIM(applicability_pt) = ''
                OR applicability_en != applicability
            """
        )
    ).scalar_one()

    if invalid:
        raise RuntimeError(
            "F-04 bilingual applicability backfill "
            f"failed validation for {invalid} rows."
        )

    with op.batch_alter_table(
        "sae_classification_links"
    ) as batch:
        batch.alter_column(
            "applicability_en",
            existing_type=sa.Text(),
            nullable=False,
        )
        batch.alter_column(
            "applicability_pt",
            existing_type=sa.Text(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "sae_classification_links"
    ) as batch:
        batch.drop_column(
            "applicability_pt"
        )
        batch.drop_column(
            "applicability_en"
        )
