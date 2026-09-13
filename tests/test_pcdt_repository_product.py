from __future__ import annotations

from pathlib import Path
import json
import unicodedata

from fastapi.testclient import TestClient

import main
from clinical_tools.pcdt_repository import (
    PCDTRepository,
)


ROOT = Path(
    __file__
).resolve().parents[1]

REGISTRY = (
    ROOT
    / "data"
    / "clinical-sources"
    / "sus_pcdt_registry.json"
)

MANIFEST = (
    ROOT
    / "data"
    / "clinical-sources"
    / "sus_pcdt_archive_manifest.json"
)


def repository():
    return PCDTRepository.from_files(
        REGISTRY,
        MANIFEST,
    )


def unaccent(
    value: str,
) -> str:
    return "".join(
        character
        for character
        in unicodedata.normalize(
            "NFD",
            value,
        )
        if unicodedata.category(
            character
        )
        != "Mn"
    )


def test_repository_counts_match_item9a():
    summary = repository().summary()

    assert summary[
        "pcdt_count"
    ] == 132

    assert summary[
        "approval_version_count"
    ] == 145

    assert summary[
        "logical_document_count"
    ] == 387

    assert summary[
        "archive_object_count"
    ] == 376

    assert summary[
        "servable_archive_object_count"
    ] == 376


def test_search_is_metadata_only_and_accent_insensitive():
    registry = json.loads(
        REGISTRY.read_text(
            encoding="utf-8"
        )
    )

    candidate = next(
        pcdt
        for pcdt
        in registry[
            "pcdts"
        ]
        if (
            unaccent(
                pcdt[
                    "canonical_title_pt"
                ]
            )
            != pcdt[
                "canonical_title_pt"
            ]
        )
    )

    query = unaccent(
        candidate[
            "canonical_title_pt"
        ]
    )

    result = repository().search(
        q=query,
        limit=100,
        offset=0,
    )

    assert any(
        item[
            "pcdt_id"
        ]
        == candidate[
            "pcdt_id"
        ]
        for item
        in result[
            "items"
        ]
    )


def test_runtime_document_urls_are_sha_addressed():
    repo = repository()

    first = repo.search(
        limit=1,
        offset=0,
    )[
        "items"
    ][0]

    documents = repo.documents(
        first[
            "pcdt_id"
        ]
    )

    urls = [
        item[
            "self_hosted_url"
        ]
        for item
        in documents[
            "items"
        ]
        if item[
            "self_hosted_url"
        ]
    ]

    assert urls

    for url in urls:
        assert url.startswith(
            "/documents/pcdt/"
        )

        name = url.rsplit(
            "/",
            1,
        )[
            1
        ]

        assert name.endswith(
            ".pdf"
        )

        digest = name[
            :-4
        ]

        assert len(
            digest
        ) == 64

        assert all(
            character
            in "0123456789abcdef"
            for character
            in digest
        )


def test_api_list_detail_and_document_graph_do_not_expose_local_paths():
    with TestClient(
        main.app
    ) as client:
        index = client.get(
            "/api/v1/pcdt",
            params={
                "limit":
                    1,
            },
        )

        assert index.status_code == 200

        payload = index.json()

        assert payload[
            "total"
        ] == 132

        pcdt_id = payload[
            "items"
        ][0][
            "pcdt_id"
        ]

        detail = client.get(
            f"/api/v1/pcdt/{pcdt_id}"
        )

        assert detail.status_code == 200

        documents = client.get(
            f"/api/v1/pcdt/{pcdt_id}/documents"
        )

        assert documents.status_code == 200

        serialized = json.dumps(
            documents.json(),
            ensure_ascii=False,
        )

        assert (
            "/var/lib/medical-api"
            not in serialized
        )

        assert (
            "local_relative_path"
            not in serialized
        )


def test_api_bounds_fail_closed():
    with TestClient(
        main.app
    ) as client:
        assert client.get(
            "/api/v1/pcdt",
            params={
                "limit":
                    101,
            },
        ).status_code == 422

        assert client.get(
            "/api/v1/pcdt",
            params={
                "offset":
                    -1,
            },
        ).status_code == 422

        assert client.get(
            "/api/v1/pcdt",
            params={
                "q":
                    "x"
                    * 121,
            },
        ).status_code == 422


def test_unknown_pcdt_fails_closed():
    with TestClient(
        main.app
    ) as client:
        assert client.get(
            "/api/v1/pcdt/does-not-exist"
        ).status_code == 404

        assert client.get(
            "/api/v1/pcdt/does-not-exist/documents"
        ).status_code == 404


def test_document_route_rejects_invalid_and_unknown_hashes():
    with TestClient(
        main.app
    ) as client:
        assert client.get(
            "/documents/pcdt/not-a-hash.pdf"
        ).status_code == 404

        assert client.get(
            "/documents/pcdt/"
            + (
                "0"
                * 64
            )
            + ".pdf"
        ).status_code == 404


def test_repository_source_preserves_clinical_firewall():
    source = (
        ROOT
        / "clinical_tools"
        / "pcdt_repository.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "import database"
        not in source
    )

    assert (
        "from database"
        not in source
    )

    assert (
        "calculate_dose"
        not in source
    )

    assert (
        "select_treatment"
        not in source
    )

    assert (
        "eligibility_rule"
        not in source
    )
