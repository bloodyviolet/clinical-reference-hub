from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(
    PROJECT_ROOT
) not in sys.path:
    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


import main  # noqa: E402


client = TestClient(
    main.app
)


def test_gcs_api_numeric_result():
    response = client.post(
        "/api/v1/tools/gcs",
        json={
            "eye":
                4,
            "verbal":
                5,
            "motor":
                6,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "tool"
    ] == "gcs"

    assert (
        payload[
            "evaluable"
        ]
        is True
    )

    assert payload[
        "total"
    ] == 15

    assert payload[
        "components"
    ] == {
        "eye":
            4,
        "verbal":
            5,
        "motor":
            6,
    }

    assert payload[
        "nt_components"
    ] == []

    assert (
        payload[
            "incomplete_reason"
        ]
        is None
    )


def test_gcs_api_nt_is_successful_non_evaluable_state():
    response = client.post(
        "/api/v1/tools/gcs",
        json={
            "eye":
                4,
            "verbal":
                "NT",
            "motor":
                6,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "evaluable"
        ]
        is False
    )

    assert (
        payload[
            "total"
        ]
        is None
    )

    assert payload[
        "nt_components"
    ] == [
        "verbal",
    ]

    assert (
        payload[
            "incomplete_reason"
        ]
        == "not_testable_component"
    )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        (
            "eye",
            0,
        ),
        (
            "eye",
            5,
        ),
        (
            "verbal",
            6,
        ),
        (
            "motor",
            7,
        ),
        (
            "eye",
            True,
        ),
        (
            "verbal",
            3.5,
        ),
        (
            "motor",
            "T",
        ),
    ],
)
def test_gcs_api_rejects_invalid_supplied_values(
    field,
    value,
):
    request = {
        "eye":
            4,
        "verbal":
            5,
        "motor":
            6,
    }

    request[
        field
    ] = value

    response = client.post(
        "/api/v1/tools/gcs",
        json=request,
    )

    assert response.status_code == 422


def test_gcs_api_requires_raw_components_not_direct_total():
    response = client.post(
        "/api/v1/tools/gcs",
        json={
            "total":
                15,
        },
    )

    assert response.status_code == 422


def test_gcsp_api_constructs_canonical_gcs_server_side():
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "eye":
                4,
            "verbal":
                5,
            "motor":
                6,
            "unreactive_pupils":
                2,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "tool"
    ] == "gcs_p"

    assert (
        payload[
            "evaluable"
        ]
        is True
    )

    assert payload[
        "gcs_total"
    ] == 15

    assert payload[
        "pupil_reactivity_score"
    ] == 2

    assert payload[
        "total"
    ] == 13

    assert payload[
        "gcs"
    ][
        "components"
    ] == {
        "eye":
            4,
        "verbal":
            5,
        "motor":
            6,
    }


def test_gcsp_api_unknown_pupils_is_successful_non_evaluable_state():
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "eye":
                4,
            "verbal":
                5,
            "motor":
                6,
            "unreactive_pupils":
                None,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "evaluable"
        ]
        is False
    )

    assert (
        payload[
            "total"
        ]
        is None
    )

    assert (
        payload[
            "pupil_reactivity_score"
        ]
        is None
    )

    assert payload[
        "incomplete_reasons"
    ] == [
        "pupil_reactivity_unknown",
    ]


def test_gcsp_api_nt_gcs_never_gets_numeric_total():
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "eye":
                4,
            "verbal":
                "NT",
            "motor":
                6,
            "unreactive_pupils":
                0,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "evaluable"
        ]
        is False
    )

    assert (
        payload[
            "gcs_total"
        ]
        is None
    )

    assert (
        payload[
            "total"
        ]
        is None
    )

    assert payload[
        "incomplete_reasons"
    ] == [
        "gcs_not_numeric",
    ]


def test_gcsp_api_can_preserve_both_incomplete_reasons():
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "eye":
                "NT",
            "verbal":
                5,
            "motor":
                6,
            "unreactive_pupils":
                None,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "total"
        ]
        is None
    )

    assert payload[
        "incomplete_reasons"
    ] == [
        "gcs_not_numeric",
        "pupil_reactivity_unknown",
    ]


@pytest.mark.parametrize(
    "value",
    [
        -1,
        3,
        True,
        1.5,
        "1",
    ],
)
def test_gcsp_api_rejects_invalid_pupil_category(
    value,
):
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "eye":
                4,
            "verbal":
                5,
            "motor":
                6,
            "unreactive_pupils":
                value,
        },
    )

    assert response.status_code == 422


def test_gcsp_api_requires_explicit_pupil_state():
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "eye":
                4,
            "verbal":
                5,
            "motor":
                6,
        },
    )

    assert response.status_code == 422


def test_gcsp_api_does_not_accept_derived_gcs_as_substitute():
    response = client.post(
        "/api/v1/tools/gcs-p",
        json={
            "gcs_total":
                15,
            "gcs_result":
                {
                    "tool":
                        "gcs",
                    "total":
                        15,
                },
            "unreactive_pupils":
                0,
        },
    )

    assert response.status_code == 422


def test_four_api_numeric_result():
    response = client.post(
        "/api/v1/tools/four-score",
        json={
            "eye":
                4,
            "motor":
                4,
            "brainstem":
                4,
            "respiration":
                4,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "tool"
    ] == "four"

    assert (
        payload[
            "evaluable"
        ]
        is True
    )

    assert payload[
        "total"
    ] == 16

    assert payload[
        "missing_domains"
    ] == []

    assert (
        payload[
            "incomplete_reason"
        ]
        is None
    )


def test_four_api_explicit_missing_domain_has_no_total():
    response = client.post(
        "/api/v1/tools/four-score",
        json={
            "eye":
                4,
            "motor":
                4,
            "brainstem":
                None,
            "respiration":
                4,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "evaluable"
        ]
        is False
    )

    assert (
        payload[
            "total"
        ]
        is None
    )

    assert payload[
        "missing_domains"
    ] == [
        "brainstem",
    ]

    assert (
        payload[
            "incomplete_reason"
        ]
        == "domain_unavailable"
    )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        (
            "eye",
            -1,
        ),
        (
            "eye",
            5,
        ),
        (
            "motor",
            5,
        ),
        (
            "brainstem",
            -1,
        ),
        (
            "respiration",
            5,
        ),
        (
            "eye",
            True,
        ),
        (
            "motor",
            2.5,
        ),
        (
            "brainstem",
            "2",
        ),
    ],
)
def test_four_api_rejects_invalid_supplied_values(
    field,
    value,
):
    request = {
        "eye":
            4,
        "motor":
            4,
        "brainstem":
            4,
        "respiration":
            4,
    }

    request[
        field
    ] = value

    response = client.post(
        "/api/v1/tools/four-score",
        json=request,
    )

    assert response.status_code == 422


def test_four_api_requires_explicit_domain_fields():
    response = client.post(
        "/api/v1/tools/four-score",
        json={
            "eye":
                4,
            "motor":
                4,
            "respiration":
                4,
        },
    )

    assert response.status_code == 422


def test_item10_routes_have_typed_response_models():
    assert (
        main.api_v1.prefix
        == "/api/v1"
    )

    routes = {
        route.path:
            route
        for route in main.api_v1.routes
        if hasattr(
            route,
            "path",
        )
    }

    assert (
        routes[
            "/api/v1/tools/gcs"
        ].response_model
        is main.schemas.GCSResponse
    )

    assert (
        routes[
            "/api/v1/tools/gcs-p"
        ].response_model
        is main.schemas.GCSPResponse
    )

    assert (
        routes[
            "/api/v1/tools/four-score"
        ].response_model
        is main.schemas.FOURResponse
    )


def test_openapi_exposes_item10_request_and_response_models():
    document = main.app.openapi()

    expected = {
        "/api/v1/tools/gcs":
            (
                "GCSInput",
                "GCSResponse",
            ),

        "/api/v1/tools/gcs-p":
            (
                "GCSPInput",
                "GCSPResponse",
            ),

        "/api/v1/tools/four-score":
            (
                "FOURInput",
                "FOURResponse",
            ),
    }

    for path, (
        input_name,
        response_name,
    ) in expected.items():
        operation = document[
            "paths"
        ][
            path
        ][
            "post"
        ]

        request_schema = operation[
            "requestBody"
        ][
            "content"
        ][
            "application/json"
        ][
            "schema"
        ]

        response_schema = operation[
            "responses"
        ][
            "200"
        ][
            "content"
        ][
            "application/json"
        ][
            "schema"
        ]

        assert (
            request_schema[
                "$ref"
            ]
            == (
                "#/components/schemas/"
                + input_name
            )
        )

        assert (
            response_schema[
                "$ref"
            ]
            == (
                "#/components/schemas/"
                + response_name
            )
        )


def test_item10_api_does_not_add_browser_metadata_or_compat_routes():
    api_paths = {
        route.path
        for route in main.api_v1.routes
        if hasattr(
            route,
            "path",
        )
    }

    app_paths = {
        route.path
        for route in main.app.routes
        if hasattr(
            route,
            "path",
        )
    }

    assert (
        "/api/v1/tools/gcs"
        in api_paths
    )

    assert (
        "/api/v1/tools/gcs-p"
        in api_paths
    )

    assert (
        "/api/v1/tools/four-score"
        in api_paths
    )

    assert (
        "/api/v1/tools/gcs/meta"
        not in api_paths
    )

    assert (
        "/api/v1/tools/gcs-p/meta"
        not in api_paths
    )

    assert (
        "/api/v1/tools/four-score/meta"
        not in api_paths
    )

    assert "/gcs" not in app_paths
    assert "/gcs-p" not in app_paths
    assert "/four-score" not in app_paths
