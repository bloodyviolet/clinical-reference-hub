from hashlib import sha256
from pathlib import Path
import json

import pytest

from clinical_tools.pcdt_metadata import (
    ARCHIVE_OBJECT_RE,
    build_approval_version_id,
    build_discovery_plan,
    manifest_object_relative_path,
    parse_conitec_catalog_html,
    slugify_pt,
    validate_manifest,
    validate_registry,
)


ROOT = Path(
    __file__
).resolve().parents[
    1
]

REGISTRY_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "sus_pcdt_registry.json"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "clinical-sources"
    / "sus_pcdt_archive_manifest.json"
)


def load(
    path,
):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def test_semantic_slug_is_deterministic():
    assert (
        slugify_pt(
            "Artrite Reumatoide"
        )
        == "artrite-reumatoide"
    )

    assert (
        slugify_pt(
            "Atenção Integral às Pessoas com "
            "Infecções Sexualmente Transmissíveis (IST)"
        )
        == (
            "atencao-integral-as-pessoas-com-"
            "infeccoes-sexualmente-transmissiveis-ist"
        )
    )


def test_approval_version_id_is_act_based():
    value = build_approval_version_id(
        act_type="Portaria Conjunta",
        issuing_units=[
            "SAES",
            "SCTIE",
            "MS",
        ],
        act_number="33",
        act_year=2026,
    )

    assert (
        value
        == "portaria-conjunta-saes-sctie-ms-33-2026"
    )


def test_registry_and_populated_manifest_validate():
    registry = load(REGISTRY_PATH)
    manifest = load(MANIFEST_PATH)
    summary = validate_registry(registry, manifest=manifest)
    assert summary['pcdt_count'] >= 100
    assert summary['approval_version_count'] >= 90
    assert summary['document_count'] >= 375
    assert summary['manifest_object_count'] == len(manifest['objects'])


def test_manifest_is_controlled_archive_state():
    manifest = load(MANIFEST_PATH)
    summary = validate_manifest(manifest)
    assert summary['object_count'] == len(manifest['objects'])
    assert manifest['bulk_download_performed'] is True
    object_ids = {obj['archive_object_id'] for obj in manifest['objects']}
    assert len(object_ids) == len(manifest['objects'])
    for obj in manifest['objects']:
        assert obj['availability_state'] == 'archived'
        assert obj['redistribution_state'] == 'public_verified'
        assert obj['public_url'] is None


def test_known_current_catalog_entries_are_present():
    registry = load(
        REGISTRY_PATH
    )

    records = {
        item[
            "pcdt_id"
        ]:
            item
        for item in registry[
            "pcdts"
        ]
    }

    for expected in (
        "artrite-reumatoide",
        "asma",
        "cancer-de-mama",
        (
            "atencao-integral-as-pessoas-com-"
            "infeccoes-sexualmente-transmissiveis-ist"
        ),
    ):
        assert expected in records


def test_artrite_reumatoide_current_approval_and_annex_event():
    registry = load(REGISTRY_PATH)
    record = next((item for item in registry['pcdts'] if item['pcdt_id'] == 'artrite-reumatoide'))
    version = next((item for item in record['approval_versions'] if item['approval_version_id'] == 'portaria-conjunta-saes-sctie-ms-33-2026'))
    assert version['act_date'] == '2026-01-19'
    assert version['dou_publication_date'] == '2026-01-23'
    assert any((event['event_type'] == 'annex_amended' and event['event_date'] == '2026-05-20' for event in version['revision_events']))
    assert any((document['document_role'] == 'protocol_text' for document in version['documents']))


def test_cancer_de_mama_rectification_is_structured():
    registry = load(
        REGISTRY_PATH
    )

    record = next(
        item
        for item in registry[
            "pcdts"
        ]
        if item[
            "pcdt_id"
        ] == "cancer-de-mama"
    )

    version = record[
        "approval_versions"
    ][
        0
    ]

    assert any(
        event[
            "event_type"
        ] == "rectified"
        and event[
            "event_date"
        ] == "2024-12-05"
        for event in version[
            "revision_events"
        ]
    )


def test_ist_protocol_is_public_verified_but_not_served_before_route_qc():
    registry = load(
        REGISTRY_PATH
    )

    record = next(
        item
        for item in registry["pcdts"]
        if item["pcdt_id"] == (
            "atencao-integral-as-pessoas-com-"
            "infeccoes-sexualmente-transmissiveis-ist"
        )
    )

    protocol = next(
        document
        for version in record["approval_versions"]
        for document in version["documents"]
        if document["document_role"] == "protocol_text"
    )

    assert protocol["archive_object_id"] is not None

    assert (
        protocol["availability_state"]
        == "archived"
    )

    assert (
        protocol["redistribution_state"]
        == "public_verified"
    )

    assert (
        protocol["self_hosted_public_url"]
        is None
    )

    assert (
        protocol["license_evidence"]["evidence_type"]
        == "inherited_from_official_page"
    )

    assert (
        protocol["license_evidence"]["evidence_report_sha256"]
        == "497cacf2f0415528c88297f6a5609ec43138f4aa4cbea088e28e3335bb4d1199"
    )


def test_discovery_plan_is_review_only():
    registry = load(
        REGISTRY_PATH
    )

    plan = build_discovery_plan(
        registry
    )

    assert plan == []

    assert all(
        item[
            "action"
        ] == "review_before_fetch"
        for item in plan
    )


def test_content_addressed_path():
    digest = (
        "a"
        * 64
    )

    assert (
        manifest_object_relative_path(
            digest
        )
        == (
            "objects/sha256/aa/"
            + digest
            + ".pdf"
        )
    )


def test_public_url_requires_public_verified_archived_object():
    manifest = {
        "schema_version":
            1,

        "archive_root":
            "/var/lib/medical-api/documents/pcdt",

        "public_prefix":
            "/documents/pcdt",

        "objects": [
            {
                "archive_object_id":
                    "sha256:"
                    + "a" * 64,

                "sha256":
                    "a" * 64,

                "size_bytes":
                    100,

                "mime_type":
                    "application/pdf",

                "local_relative_path":
                    (
                        "objects/sha256/aa/"
                        + "a" * 64
                        + ".pdf"
                    ),

                "availability_state":
                    "metadata_only",

                "redistribution_state":
                    "unknown_requires_review",

                "public_url":
                    (
                        "/documents/pcdt/objects/sha256/"
                        + "a" * 64
                        + ".pdf"
                    ),
            }
        ],
    }

    with pytest.raises(
        ValueError
    ):
        validate_manifest(
            manifest
        )


def test_synthetic_catalog_parser_preserves_role_and_revision():
    html = """
    <html>
      <body>
        <p>Modificado em 09/09/2026 14:01</p>
        <table>
          <tr>
            <td>
              <a href="/protocol.pdf">Artrite Reumatoide</a>
            </td>
            <td>
              Portaria Conjunta SAES/SCTIE/MS nº 33 -
              19/01/2026 (Publicada em
              <a href="/dou">23/01/2026</a>) -
              Anexo alterado em 20/05/2026
            </td>
            <td></td>
            <td>
              <a href="/summary.pdf">PCDT Resumido</a>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    registry = parse_conitec_catalog_html(
        html,
        source_url="https://example.gov.br/catalog",
        source_snapshot_date="2026-09-12",
        source_html_sha256=sha256(
            html.encode(
                "utf-8"
            )
        ).hexdigest(),
    )

    summary = validate_registry(
        registry
    )

    assert summary[
        "pcdt_count"
    ] == 1

    record = registry[
        "pcdts"
    ][
        0
    ]

    assert (
        record[
            "canonical_title_pt"
        ]
        == "Artrite Reumatoide"
    )

    version = record[
        "approval_versions"
    ][
        0
    ]

    roles = {
        item[
            "document_role"
        ]
        for item in version[
            "documents"
        ]
    }

    assert "protocol_text" in roles
    assert "approval_act" in roles
    assert "protocol_summary" in roles

    assert any(
        item[
            "event_type"
        ] == "annex_amended"
        for item in version[
            "revision_events"
        ]
    )


def test_no_archive_object_id_regex_shortcuts():
    assert ARCHIVE_OBJECT_RE.fullmatch(
        "sha256:"
        + "a" * 64
    )

    assert not ARCHIVE_OBJECT_RE.fullmatch(
        "sha256:"
        + "a" * 63
    )


def test_catalog_parser_accepts_hyphenated_issuing_units_for_osteoporose():
    html = """
    <html>
      <body>
        <table>
          <tr>
            <td>
              <a href="/pcdt-osteoporose.pdf">
                Osteoporose
              </a>
              - Portaria atualizada em 29/01/2026
            </td>

            <td>
              Portaria Conjunta SAES-SECTICS nº 22 -
              22/10/2025
              (
                Republicada em
                <a href="/portaria-22.pdf">31/10/2025</a>
              )
            </td>

            <td></td>
            <td></td>
          </tr>
        </table>
      </body>
    </html>
    """

    registry = parse_conitec_catalog_html(
        html,
        source_url="https://www.gov.br/conitec/catalog",
        source_snapshot_date="2026-09-12",
    )

    summary = validate_registry(
        registry
    )

    assert summary[
        "pcdt_count"
    ] == 1

    record = registry[
        "pcdts"
    ][
        0
    ]

    assert (
        record[
            "pcdt_id"
        ]
        == "osteoporose"
    )

    assert (
        record[
            "manual_review_required"
        ]
        is False
    )

    assert (
        record[
            "known_gaps"
        ]
        == []
    )

    assert (
        record[
            "unresolved_documents"
        ]
        == []
    )

    version = record[
        "approval_versions"
    ][
        0
    ]

    assert (
        version[
            "approval_version_id"
        ]
        == "portaria-conjunta-saes-sectics-22-2025"
    )

    assert (
        version[
            "issuing_units"
        ]
        == [
            "SAES",
            "SECTICS",
        ]
    )

    assert (
        version[
            "act_number"
        ]
        == "22"
    )

    assert (
        version[
            "act_year"
        ]
        == 2025
    )

    assert (
        version[
            "act_date"
        ]
        == "2025-10-22"
    )

    event_types = {
        event[
            "event_type"
        ]
        for event in version[
            "revision_events"
        ]
    }

    assert (
        "approval_act_updated"
        in event_types
    )

    assert (
        "approval_act_republished"
        in event_types
    )



def test_first_controlled_protocol_archive_tranche_is_public_verified_but_not_served():
    registry = load(
        REGISTRY_PATH
    )

    manifest = load(
        MANIFEST_PATH
    )

    selected = {
        "artrite-reumatoide",
        "asma",
        "cancer-de-mama",
        "osteoporose",
        (
            "atencao-integral-as-pessoas-com-"
            "infeccoes-sexualmente-transmissiveis-ist"
        ),
    }

    archived = {}

    for pcdt in registry["pcdts"]:
        if pcdt["pcdt_id"] not in selected:
            continue

        protocol = next(
            document
            for version in pcdt["approval_versions"]
            for document in version["documents"]
            if document["document_role"] == "protocol_text"
        )

        assert (
            protocol["availability_state"]
            == "archived"
        )

        assert (
            protocol["redistribution_state"]
            == "public_verified"
        )

        assert protocol[
            "archive_object_id"
        ] is not None

        assert protocol[
            "self_hosted_public_url"
        ] is None

        archived[
            pcdt["pcdt_id"]
        ] = protocol[
            "archive_object_id"
        ]

    assert set(
        archived
    ) == selected

    manifest_ids = {
        obj["archive_object_id"]
        for obj in manifest["objects"]
    }

    assert set(
        archived.values()
    ) <= manifest_ids



def test_current_protocol_text_corpus_is_fully_archived_public_verified_and_not_served():
    registry = load(REGISTRY_PATH)
    manifest = load(MANIFEST_PATH)
    protocols = [document for pcdt in registry['pcdts'] for version in pcdt['approval_versions'] for document in version['documents'] if document['document_role'] == 'protocol_text']
    assert len(protocols) == 132
    manifest_ids = {obj['archive_object_id'] for obj in manifest['objects']}
    protocol_ids = {document['archive_object_id'] for document in protocols}
    assert None not in protocol_ids
    assert len(protocol_ids) == 132
    assert protocol_ids <= manifest_ids
    for document in protocols:
        assert document['availability_state'] == 'archived'
        assert document['redistribution_state'] == 'public_verified'
        assert document['self_hosted_public_url'] is None



def test_represented_current_associated_assets_are_archived_public_verified_and_not_served():
    registry = load(REGISTRY_PATH)
    manifest = load(MANIFEST_PATH)
    current_versions = [version for pcdt in registry['pcdts'] for version in pcdt['approval_versions'] if any((document['document_role'] == 'protocol_text' for document in version['documents']))]
    associated = [document for version in current_versions for document in version['documents'] if document['document_role'] != 'protocol_text']
    assert len(associated) == 243
    linked_ids = {document['archive_object_id'] for document in associated}
    assert None not in linked_ids
    assert len(linked_ids) == 235
    manifest_ids = {obj['archive_object_id'] for obj in manifest['objects']}
    assert linked_ids <= manifest_ids
    for document in associated:
        assert document['availability_state'] == 'archived'
        assert document['redistribution_state'] == 'public_verified'
        assert document['self_hosted_public_url'] is None
        assert document['license_evidence']['evidence_type'] == 'inherited_from_official_page'
        assert document['license_evidence']['evidence_report_sha256'] == 'f2d9752ae6424ba3acdc834281c3b2785b6314d773172b86780ef690aee63269'
    bulk_objects = [obj for obj in manifest['objects'] if obj['license']['evidence_report_sha256'] == 'f2d9752ae6424ba3acdc834281c3b2785b6314d773172b86780ef690aee63269']
    assert len(bulk_objects) == 234

def test_qualified_historical_approval_act_tranche_is_preserved_when_present():
    registry = load(REGISTRY_PATH)
    manifest = load(MANIFEST_PATH)
    expected_ids = {'artrite-idiopatica-juvenil-aij--portaria-conjunta-saes-sctie-ms-5-2020--approval-act--001', 'artrite-idiopatica-juvenil-aij--portaria-conjunta-saes-sctie-ms-14-2020--approval-act--001', 'artrite-idiopatica-juvenil-aij--portaria-conjunta-saes-sctie-ms-16-2021--approval-act--001', 'artrite-reumatoide--portaria-conjunta-sas-sctie-ms-15-2017--approval-act--001', 'artrite-reumatoide--portaria-conjunta-saes-sctie-ms-16-2019--approval-act--001', 'artrite-reumatoide--portaria-conjunta-saes-sctie-ms-5-2020--approval-act--001', 'artrite-reumatoide--portaria-conjunta-saes-sctie-ms-14-2020--approval-act--001', 'artrite-reumatoide--portaria-conjunta-saes-sctie-ms-16-2021--approval-act--001', 'asma--portaria-conjunta-saes-sctie-ms-14-2021--approval-act--001', 'esclerose-multipla--portaria-conjunta-saes-sctie-ms-1-2022--approval-act--001', 'fibrose-cistica--portaria-conjunta-saes-sctie-ms-25-2021--approval-act--001', 'retocolite-ulcerativa--portaria-conjunta-saes-sctie-ms-6-2020--approval-act--001', 'retocolite-ulcerativa--portaria-conjunta-saes-sctie-ms-22-2021--approval-act--001'}
    all_documents = [document for pcdt in registry['pcdts'] for version in pcdt['approval_versions'] for document in version['documents']]
    by_id = {document['document_id']: document for document in all_documents}
    present = expected_ids & set(by_id)
    assert len(present) in {0, 13}
    if not present:
        return
    assert present == expected_ids
    documents = [by_id[document_id] for document_id in expected_ids]
    archive_ids = {document['archive_object_id'] for document in documents}
    assert len(archive_ids) == 10
    manifest_ids = {obj['archive_object_id'] for obj in manifest['objects']}
    assert archive_ids <= manifest_ids
    assert all((document['document_role'] == 'approval_act' for document in documents))
    assert all((document['availability_state'] == 'archived' for document in documents))
    assert all((document['redistribution_state'] == 'public_verified' for document in documents))
    assert all((document['self_hosted_public_url'] is None for document in documents))
