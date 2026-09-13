from __future__ import annotations

import inspect
import json
import os
from pathlib import Path

import pytest

from clinical_tools.four_gcsp import (
    score_four,
    score_gcs,
    score_gcsp,
)


ROOT = Path(
    __file__
).resolve().parents[1]

SOURCE_PATH = Path(
    os.environ.get(
        "FOUR_GCSP_SOURCE_PATH",
        str(
            ROOT
            / "data"
            / "clinical-sources"
            / "four_gcsp.json"
        ),
    )
)


def source():
    return json.loads(
        SOURCE_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_public_surface_is_exact_and_keyword_only():
    gcs = inspect.signature(
        score_gcs
    )

    gcsp = inspect.signature(
        score_gcsp
    )

    four = inspect.signature(
        score_four
    )

    assert list(
        gcs.parameters
    ) == [
        "eye",
        "verbal",
        "motor",
    ]

    assert list(
        gcsp.parameters
    ) == [
        "gcs_result",
        "unreactive_pupils",
    ]

    assert list(
        four.parameters
    ) == [
        "eye",
        "motor",
        "brainstem",
        "respiration",
    ]

    for signature in (
        gcs,
        gcsp,
        four,
    ):
        assert all(
            parameter.kind
            is inspect.Parameter.KEYWORD_ONLY
            for parameter
            in signature.parameters.values()
        )


def test_gcs_source_vectors():
    for vector in source()[
        "reference_vectors"
    ][
        "gcs"
    ]:
        result = score_gcs(
            eye=vector[
                "eye"
            ],
            verbal=vector[
                "verbal"
            ],
            motor=vector[
                "motor"
            ],
        )

        assert (
            result[
                "total"
            ]
            == vector[
                "expected_total"
            ]
        )

        assert (
            result[
                "evaluable"
            ]
            is (
                vector[
                    "expected_total"
                ]
                is not None
            )
        )


@pytest.mark.parametrize(
    (
        "eye",
        "verbal",
        "motor",
        "expected_total",
    ),
    [
        (
            4,
            5,
            6,
            15,
        ),
        (
            1,
            1,
            1,
            3,
        ),
        (
            2,
            3,
            4,
            9,
        ),
    ],
)
def test_gcs_numeric_totals(
    eye,
    verbal,
    motor,
    expected_total,
):
    result = score_gcs(
        eye=eye,
        verbal=verbal,
        motor=motor,
    )

    assert result[
        "tool"
    ] == "gcs"

    assert (
        result[
            "evaluable"
        ]
        is True
    )

    assert (
        result[
            "total"
        ]
        == expected_total
    )

    assert (
        result[
            "nt_components"
        ]
        == []
    )

    assert (
        result[
            "incomplete_reason"
        ]
        is None
    )


def test_gcs_nt_preserves_available_components_without_total():
    result = score_gcs(
        eye=4,
        verbal="NT",
        motor=6,
    )

    assert (
        result[
            "evaluable"
        ]
        is False
    )

    assert (
        result[
            "total"
        ]
        is None
    )

    assert result[
        "components"
    ] == {
        "eye":
            4,
        "verbal":
            "NT",
        "motor":
            6,
    }

    assert result[
        "nt_components"
    ] == [
        "verbal",
    ]

    assert (
        result[
            "incomplete_reason"
        ]
        == "not_testable_component"
    )


def test_gcs_multiple_nt_components_are_retained():
    result = score_gcs(
        eye="NT",
        verbal=5,
        motor="NT",
    )

    assert (
        result[
            "total"
        ]
        is None
    )

    assert result[
        "nt_components"
    ] == [
        "eye",
        "motor",
    ]


@pytest.mark.parametrize(
    (
        "component",
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
            0,
        ),
        (
            "verbal",
            6,
        ),
        (
            "motor",
            0,
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
            3.0,
        ),
        (
            "motor",
            "T",
        ),
    ],
)
def test_gcs_rejects_invalid_component_values(
    component,
    value,
):
    payload = {
        "eye":
            4,
        "verbal":
            5,
        "motor":
            6,
    }

    payload[
        component
    ] = value

    with pytest.raises(
        ValueError,
        match=component,
    ):
        score_gcs(
            **payload
        )


def test_gcs_has_no_direct_total_parameter():
    assert (
        "total"
        not in inspect.signature(
            score_gcs
        ).parameters
    )


def test_gcsp_source_vectors():
    for vector in source()[
        "reference_vectors"
    ][
        "gcsp"
    ]:
        gcs_total = vector[
            "gcs_total"
        ]

        if gcs_total is None:
            gcs = score_gcs(
                eye=4,
                verbal="NT",
                motor=6,
            )
        else:
            # Construct canonical component combinations
            # that reproduce each source-vector total.
            if gcs_total == 15:
                components = (
                    4,
                    5,
                    6,
                )

            elif gcs_total == 8:
                components = (
                    2,
                    2,
                    4,
                )

            elif gcs_total == 3:
                components = (
                    1,
                    1,
                    1,
                )

            else:
                raise AssertionError(
                    "Unhandled persisted GCS-P vector."
                )

            gcs = score_gcs(
                eye=components[
                    0
                ],
                verbal=components[
                    1
                ],
                motor=components[
                    2
                ],
            )

            assert (
                gcs[
                    "total"
                ]
                == gcs_total
            )

        result = score_gcsp(
            gcs_result=gcs,
            unreactive_pupils=vector[
                "prs"
            ],
        )

        assert (
            result[
                "total"
            ]
            == vector[
                "expected"
            ]
        )

        assert (
            result[
                "evaluable"
            ]
            is (
                vector[
                    "expected"
                ]
                is not None
            )
        )


@pytest.mark.parametrize(
    (
        "gcs_total",
        "unreactive_pupils",
        "expected",
    ),
    [
        (
            15,
            0,
            15,
        ),
        (
            15,
            1,
            14,
        ),
        (
            15,
            2,
            13,
        ),
        (
            8,
            1,
            7,
        ),
        (
            3,
            2,
            1,
        ),
    ],
)
def test_gcsp_numeric_formula(
    gcs_total,
    unreactive_pupils,
    expected,
):
    combinations = {
        15:
            (
                4,
                5,
                6,
            ),

        8:
            (
                2,
                2,
                4,
            ),

        3:
            (
                1,
                1,
                1,
            ),
    }

    (
        eye,
        verbal,
        motor,
    ) = combinations[
        gcs_total
    ]

    gcs = score_gcs(
        eye=eye,
        verbal=verbal,
        motor=motor,
    )

    result = score_gcsp(
        gcs_result=gcs,
        unreactive_pupils=unreactive_pupils,
    )

    assert (
        result[
            "evaluable"
        ]
        is True
    )

    assert (
        result[
            "gcs_total"
        ]
        == gcs_total
    )

    assert (
        result[
            "pupil_reactivity_score"
        ]
        == unreactive_pupils
    )

    assert (
        result[
            "total"
        ]
        == expected
    )


def test_gcsp_nt_gcs_never_gets_numeric_total():
    gcs = score_gcs(
        eye=4,
        verbal="NT",
        motor=6,
    )

    result = score_gcsp(
        gcs_result=gcs,
        unreactive_pupils=0,
    )

    assert (
        result[
            "evaluable"
        ]
        is False
    )

    assert (
        result[
            "total"
        ]
        is None
    )

    assert (
        result[
            "gcs_total"
        ]
        is None
    )

    assert (
        result[
            "incomplete_reasons"
        ]
        == [
            "gcs_not_numeric",
        ]
    )


def test_gcsp_unknown_pupils_never_gets_numeric_total():
    gcs = score_gcs(
        eye=4,
        verbal=5,
        motor=6,
    )

    result = score_gcsp(
        gcs_result=gcs,
        unreactive_pupils=None,
    )

    assert (
        result[
            "evaluable"
        ]
        is False
    )

    assert (
        result[
            "total"
        ]
        is None
    )

    assert (
        result[
            "pupil_reactivity_score"
        ]
        is None
    )

    assert (
        result[
            "incomplete_reasons"
        ]
        == [
            "pupil_reactivity_unknown",
        ]
    )


def test_gcsp_can_preserve_both_incomplete_reasons():
    gcs = score_gcs(
        eye="NT",
        verbal=5,
        motor=6,
    )

    result = score_gcsp(
        gcs_result=gcs,
        unreactive_pupils=None,
    )

    assert (
        result[
            "total"
        ]
        is None
    )

    assert result[
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
        1.0,
        "1",
    ],
)
def test_gcsp_rejects_invalid_pupil_category(
    value,
):
    gcs = score_gcs(
        eye=4,
        verbal=5,
        motor=6,
    )

    with pytest.raises(
        ValueError,
        match="unreactive_pupils",
    ):
        score_gcsp(
            gcs_result=gcs,
            unreactive_pupils=value,
        )


def test_gcsp_rejects_tampered_gcs_total():
    gcs = score_gcs(
        eye=4,
        verbal=5,
        motor=6,
    )

    gcs[
        "total"
    ] = 3

    with pytest.raises(
        ValueError,
        match="inconsistent",
    ):
        score_gcsp(
            gcs_result=gcs,
            unreactive_pupils=0,
        )


def test_gcsp_rejects_wrong_tool_result():
    fake = {
        "tool":
            "four",

        "components":
            {
                "eye":
                    4,
                "verbal":
                    5,
                "motor":
                    6,
            },

        "evaluable":
            True,

        "total":
            15,

        "nt_components":
            [],

        "incomplete_reason":
            None,
    }

    with pytest.raises(
        ValueError,
        match="GCS tool",
    ):
        score_gcsp(
            gcs_result=fake,
            unreactive_pupils=0,
        )


def test_four_source_vectors():
    for vector in source()[
        "reference_vectors"
    ][
        "four"
    ]:
        result = score_four(
            eye=vector[
                "eye"
            ],
            motor=vector[
                "motor"
            ],
            brainstem=vector[
                "brainstem"
            ],
            respiration=vector[
                "respiration"
            ],
        )

        assert (
            result[
                "total"
            ]
            == vector[
                "expected_total"
            ]
        )

        assert (
            result[
                "evaluable"
            ]
            is (
                vector[
                    "expected_total"
                ]
                is not None
            )
        )


@pytest.mark.parametrize(
    (
        "components",
        "expected",
    ),
    [
        (
            {
                "eye":
                    4,
                "motor":
                    4,
                "brainstem":
                    4,
                "respiration":
                    4,
            },
            16,
        ),
        (
            {
                "eye":
                    0,
                "motor":
                    0,
                "brainstem":
                    0,
                "respiration":
                    0,
            },
            0,
        ),
        (
            {
                "eye":
                    2,
                "motor":
                    3,
                "brainstem":
                    2,
                "respiration":
                    2,
            },
            9,
        ),
    ],
)
def test_four_numeric_totals(
    components,
    expected,
):
    result = score_four(
        **components
    )

    assert (
        result[
            "evaluable"
        ]
        is True
    )

    assert (
        result[
            "total"
        ]
        == expected
    )

    assert (
        result[
            "missing_domains"
        ]
        == []
    )

    assert (
        result[
            "incomplete_reason"
        ]
        is None
    )


def test_four_missing_domain_has_no_numeric_total():
    result = score_four(
        eye=4,
        motor=4,
        brainstem=None,
        respiration=4,
    )

    assert (
        result[
            "evaluable"
        ]
        is False
    )

    assert (
        result[
            "total"
        ]
        is None
    )

    assert result[
        "missing_domains"
    ] == [
        "brainstem",
    ]

    assert (
        result[
            "components"
        ][
            "brainstem"
        ]
        is None
    )

    assert (
        result[
            "incomplete_reason"
        ]
        == "domain_unavailable"
    )


def test_four_multiple_missing_domains_are_preserved():
    result = score_four(
        eye=None,
        motor=4,
        brainstem=None,
        respiration=4,
    )

    assert result[
        "missing_domains"
    ] == [
        "eye",
        "brainstem",
    ]

    assert (
        result[
            "total"
        ]
        is None
    )


@pytest.mark.parametrize(
    (
        "domain",
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
            -1,
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
            "brainstem",
            5,
        ),
        (
            "respiration",
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
            1.0,
        ),
        (
            "brainstem",
            "2",
        ),
    ],
)
def test_four_rejects_invalid_domain_values(
    domain,
    value,
):
    payload = {
        "eye":
            4,
        "motor":
            4,
        "brainstem":
            4,
        "respiration":
            4,
    }

    payload[
        domain
    ] = value

    with pytest.raises(
        ValueError,
        match=domain,
    ):
        score_four(
            **payload
        )


def test_four_is_independent_of_gcs():
    signature = inspect.signature(
        score_four
    )

    assert (
        "gcs"
        not in signature.parameters
    )

    assert (
        "gcs_result"
        not in signature.parameters
    )


def test_core_does_not_encode_prognostic_cutoffs():
    module_text = (
        Path(
            inspect.getsourcefile(
                score_four
            )
        )
        .read_text(
            encoding="utf-8"
        )
    )

    forbidden = (
        "mortality",
        "treatment_cutoff",
        "disposition",
        "low_risk",
        "high_risk",
    )

    for marker in forbidden:
        assert (
            marker
            not in module_text
        )


def test_persisted_contract_and_core_boundaries_match():
    data = source()

    assert (
        data[
            "gcs_contract"
        ][
            "direct_total_without_components_allowed"
        ]
        is False
    )

    assert (
        data[
            "gcsp_contract"
        ][
            "requires_numeric_gcs_total"
        ]
        is True
    )

    assert (
        data[
            "gcsp_contract"
        ][
            "unknown_pupil_state_numeric_result"
        ]
        is False
    )

    assert (
        data[
            "four_contract"
        ][
            "all_domains_required_for_numeric_total"
        ]
        is True
    )

    assert (
        data[
            "four_contract"
        ][
            "derived_from_gcs"
        ]
        is False
    )

    assert (
        data[
            "four_contract"
        ][
            "mortality_or_treatment_cutoff"
        ]
        is None
    )
