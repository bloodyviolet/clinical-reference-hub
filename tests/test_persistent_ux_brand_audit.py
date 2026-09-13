from pathlib import Path
import json

from fastapi.testclient import TestClient


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def _relative_luminance(
    value: str,
) -> float:
    value = value.lstrip("#")

    channels = [
        int(
            value[index:index + 2],
            16,
        )
        / 255.0
        for index
        in (
            0,
            2,
            4,
        )
    ]

    def linearise(
        channel: float,
    ) -> float:
        if channel <= 0.04045:
            return (
                channel
                / 12.92
            )

        return (
            (
                channel
                + 0.055
            )
            / 1.055
        ) ** 2.4

    red, green, blue = [
        linearise(
            channel
        )
        for channel
        in channels
    ]

    return (
        0.2126 * red
        + 0.7152 * green
        + 0.0722 * blue
    )


def _contrast(
    first: str,
    second: str,
) -> float:
    first_luminance = (
        _relative_luminance(
            first
        )
    )

    second_luminance = (
        _relative_luminance(
            second
        )
    )

    lighter = max(
        first_luminance,
        second_luminance,
    )

    darker = min(
        first_luminance,
        second_luminance,
    )

    return (
        lighter
        + 0.05
    ) / (
        darker
        + 0.05
    )


def test_persistent_ux_and_bloodviolet_static_contract():
    html = (
        ROOT
        / "index.html"
    ).read_text(
        encoding="utf-8"
    )

    app = (
        ROOT
        / "assets"
        / "app.js"
    ).read_text(
        encoding="utf-8"
    )

    session = (
        ROOT
        / "assets"
        / "ui-session.js"
    ).read_text(
        encoding="utf-8"
    )

    theme = (
        ROOT
        / "assets"
        / "bloodviolet-theme.css"
    ).read_text(
        encoding="utf-8"
    )

    sw = (
        ROOT
        / "sw.js"
    ).read_text(
        encoding="utf-8"
    )

    manifest = json.loads(
        (
            ROOT
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        'id="brand-home"'
        in html
    )

    assert (
        '/assets/icons/icon-192.png'
        in html
    )

    assert (
        '/assets/bloodviolet-theme.css'
        in html
    )

    assert (
        '/assets/ui-session.js'
        in html
    )

    assert (
        "clinical-reference-v2-ui-session-v1"
        in session
    )

    assert (
        "sessionStorage"
        in session
    )

    assert (
        "localStorage"
        not in session
    )

    assert (
        "indexedDB"
        not in session
    )

    assert (
        "fetch("
        not in session
    )

    assert (
        "XMLHttpRequest"
        not in session
    )

    assert (
        "TOOL_RESULT_SURFACES"
        in session
    )

    assert (
        "TOOL_SERIAL_KEYS"
        in session
    )

    assert (
        "MutationObserver"
        in session
    )

    assert (
        "ClinicalSerialCaptureBridge"
        in app
    )

    assert (
        "serialCaptureRestoreBindings"
        in app
    )

    assert (
        "--bv-blood-main: #a40a2f"
        in theme
    )

    assert (
        "--bv-violet: #5b21a6"
        in theme
    )

    assert (
        "--bv-text: #fff9ff"
        in theme
    )

    assert (
        manifest[
            "theme_color"
        ]
        == "#5A0B32"
    )

    assert (
        manifest[
            "background_color"
        ]
        == "#09030F"
    )

    assert (
        "clinical-reference-v30-v2-pcdt-ux-bilingual"
        in sw
    )


def test_bloodviolet_core_contrast_ratios():
    assert (
        _contrast(
            "#FFF9FF",
            "#09030F",
        )
        >= 7.0
    )

    assert (
        _contrast(
            "#EEE3F5",
            "#1D082D",
        )
        >= 7.0
    )

    assert (
        _contrast(
            "#C9B5D6",
            "#09030F",
        )
        >= 7.0
    )

    assert (
        _contrast(
            "#FFF9FF",
            "#A40A2F",
        )
        >= 4.5
    )

    assert (
        _contrast(
            "#FFF9FF",
            "#5B21A6",
        )
        >= 4.5
    )


def test_new_runtime_assets_are_served_same_origin():
    import main

    with TestClient(
        main.app
    ) as client:
        for path in (
            "/assets/bloodviolet-theme.css",
            "/assets/ui-session.js",
            "/assets/icons/icon-192.png",
            "/manifest.json",
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
        ).json()

        assert (
            ready[
                "api_version"
            ]
            == "2.0.0"
        )

        assert (
            ready[
                "database_revision"
            ]
            == "0007"
        )

        assert (
            ready[
                "clinical_content"
            ]
            == "certified"
        )
