import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_uses_only_local_pwa_icons():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    icons = manifest["icons"]
    assert {icon["sizes"] for icon in icons} == {"192x192", "512x512"}
    assert all(icon["src"].startswith("/assets/icons/") for icon in icons)
    assert all("://" not in icon["src"] for icon in icons)
    for icon in icons:
        assert (ROOT / icon["src"].lstrip("/")).is_file()

    expected_sizes = {
        "icon-192.png": (192, 192),
        "icon-512.png": (512, 512),
        "apple-touch-icon.png": (180, 180),
        "favicon-32.png": (32, 32),
        "favicon-16.png": (16, 16),
    }
    for name, expected in expected_sizes.items():
        path = ROOT / "assets" / "icons" / name
        assert path.is_file(), name
        raw = path.read_bytes()
        assert raw[:8] == b"\x89PNG\r\n\x1a\n", name
        width = int.from_bytes(raw[16:20], "big")
        height = int.from_bytes(raw[20:24], "big")
        assert (width, height) == expected, name
    assert (ROOT / "assets" / "icons" / "favicon.ico").is_file()
    assert (ROOT / "brand" / "nursing-clinical-hub-original.png").is_file()
    assert (ROOT / "brand" / "nursing-clinical-hub-icon-master.png").is_file()


def test_offline_bundles_are_complete_and_match_database():
    sae = json.loads((ROOT / "assets/offline/sae.json").read_text(encoding="utf-8"))
    policies = json.loads((ROOT / "assets/offline/policies.json").read_text(encoding="utf-8"))

    assert sae["api_version"] == "1.4.5"
    assert sae["database_revision"] == "0007"
    assert sae["count"] == len(sae["items"]) == 277
    assert policies["api_version"] == "1.4.5"
    assert policies["database_revision"] == "0007"
    assert policies["count"] == 54
    assert sum(group["returned"] for group in policies["policies"].values()) == 54
    assert len(policies["policies"]) == 7

    by_code = {item["code"]: item for item in sae["items"]}
    assert by_code["00068"]["description_pt"] == "Prontidão para um maior bem-estar espiritual"
    assert "readiness for enhanced spiritual well-being" not in by_code["00068"]["intervention_pt"].lower()
    assert by_code["00068"]["intervention_pt"].strip()

    for item in sae["items"]:
        assert item["intervention_pt"].strip(), item["code"]
        assert (
            item["description_en"].lower()
            not in item["intervention_pt"].lower()
        ), item["code"]
        assert item["description_en"].lower() not in item["intervention_pt"].lower()

    with sqlite3.connect(ROOT / "medical.db") as db:
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert db.execute("SELECT COUNT(*) FROM sae_diagnostics").fetchone()[0] == 277
        assert db.execute("SELECT COUNT(*) FROM sae_classification_links").fetchone()[0] == 627
        assert db.execute("SELECT COUNT(*) FROM public_health_policies").fetchone()[0] == 54


def test_service_worker_precaches_offline_data_and_local_icons():
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")
    assert "clinical-reference-v20-v2-brazil-methanol" in sw
    for path in (
        "/assets/offline/sae.json",
        "/assets/offline/policies.json",
        "/assets/i18n.js",
        "/assets/clinical-tools.js",
        "/assets/icons/icon-192.png",
        "/assets/icons/icon-512.png",
        "/assets/icons/apple-touch-icon.png",
        "/assets/icons/favicon-32.png",
        "/assets/icons/favicon-16.png",
        "/favicon.ico",
    ):
        assert path in sw
    assert "X-Clinical-Offline" in sw


def test_pass61_static_assets_are_served_same_origin():
    from fastapi.testclient import TestClient
    import main

    with TestClient(main.app) as client:
        for path in (
            "/manifest.json",
            "/assets/icons/icon-192.png",
            "/assets/icons/icon-512.png",
            "/assets/icons/apple-touch-icon.png",
            "/assets/icons/favicon-32.png",
            "/assets/icons/favicon-16.png",
            "/favicon.ico",
            "/assets/offline/sae.json",
            "/assets/offline/policies.json",
        ):
            response = client.get(path)
            assert response.status_code == 200, path
        assert client.get("/api/v1/readyz").json()["api_version"] == "1.4.5"
