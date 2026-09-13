from pathlib import Path
import hashlib

from fastapi.testclient import TestClient


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


NNN_HASHES = {
    "sae_bilingual_final.csv":
        "e7b301c1bfb1dfb71756371da5d1d675b9caceb156a2af2d5fbb302fc0821293",

    "data/sae_nnn_links.csv":
        "952a3b3c6774552494018c4454a069f9a51805118ffb90ae0e8d3618dd568943",

    "sae_mapping_review.csv":
        "ac496fc3b8cfa48b0fd9d411ddd1caa5dec799946e2263d3d0abb30c31df5323",

    "nnn_link_review.csv":
        "5517000b84a40c7482d0bb07698db50441693a6b7a7409e8b72f82b91f96ae4c",

    "data/nnn_source_manifest.json":
        "d303bd5eb3280d9589657d389c509e038c10d7bc65eff01dcd5cac19d0059e6c",

    "assets/offline/sae.json":
        "28da875e9a39d4d6d4d4203df84c64082bd7474d871210151619a7ea7d83ce74",
}


def _sha256(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def test_nnn_data_hard_freeze():
    for relative, expected in (
        NNN_HASHES.items()
    ):
        assert (
            _sha256(
                ROOT
                / relative
            )
            == expected
        )


def test_bilingual_runtime_assets_declared():
    index = (
        ROOT
        / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    sw = (
        ROOT
        / "sw.js"
    ).read_text(
        encoding="utf-8"
    )

    main = (
        ROOT
        / "main.py"
    ).read_text(
        encoding="utf-8"
    )

    preflight = (
        ROOT
        / "scripts"
        / "preflight.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "/manifest.json?v=30"
        in index
    )

    assert (
        "/assets/policy-translations-en.js"
        in index
    )

    assert (
        "/assets/bilingual-presentation.js"
        in index
    )

    assert (
        "clinical-reference-v30-v2-pcdt-ux-bilingual"
        in sw
    )

    for asset in (
        "policy-translations-en.js",
        "bilingual-presentation.js",
    ):
        assert asset in main
        assert asset in preflight
        assert asset in sw


def test_bilingual_runtime_assets_served():
    import main

    with TestClient(
        main.app
    ) as client:
        for path in (
            "/assets/policy-translations-en.js",
            "/assets/bilingual-presentation.js",
            "/assets/i18n.js",
            "/assets/app.js",
            "/sw.js",
        ):
            response = client.get(
                path
            )

            assert (
                response.status_code
                == 200
            ), path

        ready = client.get(
            "/api/v1/readyz"
        )

        assert (
            ready.status_code
            == 200
        )

        payload = ready.json()

        assert (
            payload[
                "api_version"
            ]
            == "2.0.0"
        )

        assert (
            payload[
                "database_revision"
            ]
            == "0007"
        )

        assert (
            payload[
                "clinical_content"
            ]
            == "certified"
        )
