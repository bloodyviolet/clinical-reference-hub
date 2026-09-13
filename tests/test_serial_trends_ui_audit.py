from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import subprocess

import pytest


ROOT = Path(
    __file__
).resolve().parents[1]

APP = (
    ROOT
    / "assets"
    / "app.js"
)

I18N = (
    ROOT
    / "assets"
    / "i18n.js"
)

INDEX = (
    ROOT
    / "index.html"
)

SW = (
    ROOT
    / "sw.js"
)

REGISTRY = (
    ROOT
    / "data"
    / "clinical-sources"
    / "serial_trends_instrument_registry.json"
)

BROWSER_REGISTRY = (
    ROOT
    / "assets"
    / "serial-trends-instrument-registry.json"
)

RUNTIME = (
    ROOT
    / "assets"
    / "serial-trends-runtime.js"
)

GOVERNANCE = (
    ROOT
    / "data"
    / "brazil_clinical_harmonization.json"
)

JS_AUDIT = (
    ROOT
    / "tests"
    / "serial_trends_ui_semantics.js"
)

EXPECTED_REGISTRY_SHA = (
    "5b53d89bfb88a844f6baf0a3d9202d7565ab6f63737f5a000d79340b5dd8bf54"
)

EXPECTED_RUNTIME_SHA = (
    "aa29106e2caa20eff1104ba853ecc59d0dc752ec18c5a272a2b0dfa06fe5f2b4"
)

CACHE_NAME = (
    "clinical-reference-v24-v2-serial-trends-ui"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_ui_uses_qualified_runtime_and_byte_identical_registry():
    assert sha256(
        RUNTIME
    ) == EXPECTED_RUNTIME_SHA

    assert sha256(
        REGISTRY
    ) == EXPECTED_REGISTRY_SHA

    assert sha256(
        BROWSER_REGISTRY
    ) == EXPECTED_REGISTRY_SHA

    assert (
        BROWSER_REGISTRY.read_bytes()
        == REGISTRY.read_bytes()
    )


def test_serial_view_accessibility_contract():
    html = text(
        INDEX
    )

    app = text(
        APP
    )

    tab_ids = [
        "tab-btn-sae",
        "tab-btn-policy",
        "tab-btn-calc",
        "tab-btn-scales",
        "tab-btn-trends",
    ]

    panel_ids = [
        "view-sae",
        "view-policy",
        "view-calc",
        "view-scales",
        "view-trends",
    ]

    for index, (
        tab_id,
        panel_id,
    ) in enumerate(
        zip(
            tab_ids,
            panel_ids,
        )
    ):
        match = re.search(
            rf'<button\b[^>]*'
            rf'\bid="{re.escape(tab_id)}"'
            rf'[^>]*>',
            html,
        )

        assert match

        tag = match.group(
            0
        )

        assert (
            'role="tab"'
            in tag
        )

        assert (
            f'aria-controls="{panel_id}"'
            in tag
        )

        if index == 0:
            assert (
                'aria-selected="true"'
                in tag
            )

            assert (
                'tabindex="0"'
                in tag
            )

        else:
            assert (
                'aria-selected="false"'
                in tag
            )

            assert (
                'tabindex="-1"'
                in tag
            )

        panel = re.search(
            rf'<section\b[^>]*'
            rf'\bid="{re.escape(panel_id)}"'
            rf'[^>]*>',
            html,
        )

        assert panel

        assert (
            'role="tabpanel"'
            in panel.group(0)
        )

        assert (
            f'aria-labelledby="{tab_id}"'
            in panel.group(0)
        )

    assert (
        "button.setAttribute('tabindex', '-1');"
        in app
    )

    assert (
        ".setAttribute('tabindex', '0');"
        in app
    )

    assert (
        "tabs[next].focus();"
        in app
    )

    assert (
        "switchTab(tabs[next].dataset.tab);"
        in app
    )

    assert (
        'id="serial-table-heading"'
        in html
    )

    assert (
        'id="serial-table-note"'
        in html
    )

    assert re.search(
        r'<table\b[^>]*'
        r'aria-labelledby="serial-table-heading"'
        r'[^>]*'
        r'aria-describedby="serial-table-note"',
        html,
    )

    assert (
        html.count(
            'scope="col"'
        )
        >= 8
    )


def test_serial_time_identity_and_persistence_boundaries():
    html = text(
        INDEX
    )

    app = text(
        APP
    )

    start = app.index(
        "// ITEM11_SERIAL_TRENDS_UI_START"
    )

    end = app.index(
        "// ITEM11_SERIAL_TRENDS_UI_END"
    )

    serial = app[
        start:end
    ]

    observed = re.search(
        r'<input\b[^>]*'
        r'\bid="serial-observed-at"'
        r'[^>]*>',
        html,
    )

    offset = re.search(
        r'<input\b[^>]*'
        r'\bid="serial-offset"'
        r'[^>]*>',
        html,
    )

    assert observed
    assert offset

    assert (
        'type="datetime-local"'
        in observed.group(0)
    )

    assert (
        "value="
        not in observed.group(0)
    )

    assert (
        "value="
        not in offset.group(0)
    )

    assert (
        'aria-describedby="serial-offset-note"'
        in offset.group(0)
    )

    assert (
        "/^(?:Z|[+-]\\d{2}:\\d{2})$/"
        in serial
    )

    assert (
        "getTimezoneOffset("
        not in serial
    )

    for forbidden in (
        "patient_id",
        "encounter_id",
        "person_id",
        "localStorage",
        "sessionStorage",
        "indexedDB",
    ):
        assert (
            forbidden
            not in serial
        )


def test_serial_plot_and_capture_boundaries():
    app = text(
        APP
    )

    start = app.index(
        "// ITEM11_SERIAL_TRENDS_UI_START"
    )

    end = app.index(
        "// ITEM11_SERIAL_TRENDS_UI_END"
    )

    serial = app[
        start:end
    ]

    assert (
        "instrument.plot_groups"
        in serial
    )

    assert (
        "plotField.plot_value"
        in serial
    )

    assert (
        "Number.isFinite("
        in serial
    )

    assert (
        "<circle"
        in serial
    )

    assert (
        "<polyline"
        not in serial
    )

    assert (
        "<path"
        not in serial
    )

    assert (
        "function serialSnapshotRequestPayload("
        in app
    )

    helper_start = app.index(
        "function serialSnapshotRequestPayload("
    )

    helper_end = app.index(
        "\n\nasync function runClinicalCalculator(",
        helper_start,
    )

    helper = app[
        helper_start:
        helper_end
    ]

    assert (
        "SerialTrendsRuntime"
        in helper
    )

    assert (
        "snapshotClinicalJson"
        in helper
    )

    assert (
        "return null;"
        in helper
    )

    assert (
        "capture.request === null"
        in serial
    )

    assert (
        "capture.result === null"
        in serial
    )


def test_serial_i18n_and_language_rerender_contract():
    i18n = text(
        I18N
    )

    app = text(
        APP
    )

    start = app.index(
        "// ITEM11_SERIAL_TRENDS_UI_START"
    )

    end = app.index(
        "// ITEM11_SERIAL_TRENDS_UI_END"
    )

    serial = app[
        start:end
    ]

    assert (
        "'clinical-language-change'"
        in i18n
    )

    assert (
        "new CustomEvent("
        in i18n
    )

    assert (
        "'clinical-language-change'"
        in serial
    )

    for required in (
        "serialPopulateInstrumentOptions();",
        "serialPopulatePlotOptions();",
        "serialRender();",
    ):
        assert (
            required
            in serial
        )

    pattern = re.compile(
        r'^\s*["\']'
        r'(?P<key>'
        r'(?:serial\.[^"\']+|nav\.trends)'
        r')'
        r'["\']\s*:',
        flags=re.MULTILINE,
    )

    keys = [
        match.group(
            "key"
        )
        for match
        in pattern.finditer(
            i18n
        )
    ]

    counts = Counter(
        keys
    )

    assert len(
        counts
    ) == 66

    assert all(
        count == 2
        for count
        in counts.values()
    )

    assert len([
        key
        for key
        in counts
        if key.startswith(
            "serial.instrument."
        )
    ]) == 18


def test_serial_pwa_delivery_contract():
    sw = text(
        SW
    )

    assert (
        f"const CACHE_NAME = '{CACHE_NAME}';"
        in sw
    )

    assert (
        sw.count(
            "'/assets/serial-trends-runtime.js'"
        )
        == 1
    )

    assert (
        sw.count(
            "'/assets/serial-trends-instrument-registry.json'"
        )
        == 1
    )

    assert (
        "new Request(url, { cache: 'reload' })"
        in sw
    )

    assert (
        "keys.filter((key) => key !== CACHE_NAME)"
        in sw
    )


def test_governance_remains_release_recheck_gated():
    governance = json.loads(
        text(
            GOVERNANCE
        )
    )

    assert (
        governance[
            "future_items"
        ][
            "11"
        ][
            "feature"
        ]
        == "Serial trends"
    )

    assert (
        governance[
            "release_gate"
        ][
            "final_recheck_required_before_v2_release"
        ]
        is True
    )


def test_serial_ui_runtime_semantics_execute():
    try:
        completed = subprocess.run(
            [
                "node",
                str(
                    JS_AUDIT
                ),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    except FileNotFoundError:
        pytest.fail(
            "node executable unavailable"
        )

    output = (
        completed.stdout
        + completed.stderr
    )

    assert (
        "serial_trends_ui_semantics:"
        in output
    )

    assert (
        "registry-only plotting and clear isolation PASS"
        in output
    )
