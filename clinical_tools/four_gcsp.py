"""Canonical FOUR Score, GCS, and GCS-P clinical scoring core."""

from __future__ import annotations

from typing import Literal, TypeAlias


GCSNotTestable = Literal["NT"]
GCSComponent: TypeAlias = int | GCSNotTestable


def _validate_gcs_component(
    *,
    name: str,
    value: GCSComponent,
    minimum: int,
    maximum: int,
) -> GCSComponent:
    if value == "NT":
        return value

    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
        or not minimum
        <= value
        <= maximum
    ):
        raise ValueError(
            f"{name} must be an integer "
            f"from {minimum} through {maximum} "
            "or the explicit value 'NT'."
        )

    return value


def _validate_four_domain(
    *,
    name: str,
    value: int | None,
) -> int | None:
    if value is None:
        return None

    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
        or not 0
        <= value
        <= 4
    ):
        raise ValueError(
            f"{name} must be an integer "
            "from 0 through 4 or None "
            "when the domain is not available."
        )

    return value


def score_gcs(
    *,
    eye: GCSComponent,
    verbal: GCSComponent,
    motor: GCSComponent,
) -> dict:
    """Score GCS while preserving explicit non-testable components."""

    components = {
        "eye":
            _validate_gcs_component(
                name="eye",
                value=eye,
                minimum=1,
                maximum=4,
            ),

        "verbal":
            _validate_gcs_component(
                name="verbal",
                value=verbal,
                minimum=1,
                maximum=5,
            ),

        "motor":
            _validate_gcs_component(
                name="motor",
                value=motor,
                minimum=1,
                maximum=6,
            ),
    }

    nt_components = [
        name
        for name, value
        in components.items()
        if value == "NT"
    ]

    if nt_components:
        return {
            "tool":
                "gcs",

            "evaluable":
                False,

            "total":
                None,

            "components":
                components,

            "nt_components":
                nt_components,

            "incomplete_reason":
                "not_testable_component",
        }

    total = sum(
        components.values()
    )

    assert (
        isinstance(
            total,
            int,
        )
        and 3
        <= total
        <= 15
    )

    return {
        "tool":
            "gcs",

        "evaluable":
            True,

        "total":
            total,

        "components":
            components,

        "nt_components":
            [],

        "incomplete_reason":
            None,
    }


def _canonicalize_gcs_result(
    gcs_result: dict,
) -> dict:
    if not isinstance(
        gcs_result,
        dict,
    ):
        raise ValueError(
            "gcs_result must be a result returned by score_gcs()."
        )

    if (
        gcs_result.get(
            "tool"
        )
        != "gcs"
    ):
        raise ValueError(
            "gcs_result must identify the GCS tool."
        )

    components = gcs_result.get(
        "components"
    )

    if (
        not isinstance(
            components,
            dict,
        )
        or set(
            components
        )
        != {
            "eye",
            "verbal",
            "motor",
        }
    ):
        raise ValueError(
            "gcs_result must contain eye, verbal, "
            "and motor components."
        )

    canonical = score_gcs(
        eye=components[
            "eye"
        ],
        verbal=components[
            "verbal"
        ],
        motor=components[
            "motor"
        ],
    )

    fields = (
        "evaluable",
        "total",
        "nt_components",
        "incomplete_reason",
    )

    for field in fields:
        if (
            gcs_result.get(
                field
            )
            != canonical[
                field
            ]
        ):
            raise ValueError(
                "gcs_result is inconsistent "
                "with its component observations."
            )

    return canonical


def score_gcsp(
    *,
    gcs_result: dict,
    unreactive_pupils: int | None,
) -> dict:
    """Calculate GCS-P from a canonical GCS result and pupil findings."""

    gcs = _canonicalize_gcs_result(
        gcs_result
    )

    if unreactive_pupils is not None:
        if (
            isinstance(
                unreactive_pupils,
                bool,
            )
            or not isinstance(
                unreactive_pupils,
                int,
            )
            or unreactive_pupils
            not in {
                0,
                1,
                2,
            }
        ):
            raise ValueError(
                "unreactive_pupils must be "
                "0, 1, 2, or None when pupil "
                "reactivity is unavailable."
            )

    incomplete_reasons = []

    if not gcs[
        "evaluable"
    ]:
        incomplete_reasons.append(
            "gcs_not_numeric"
        )

    if unreactive_pupils is None:
        incomplete_reasons.append(
            "pupil_reactivity_unknown"
        )

    pupil_reactivity_score = (
        unreactive_pupils
    )

    if incomplete_reasons:
        return {
            "tool":
                "gcs_p",

            "evaluable":
                False,

            "total":
                None,

            "gcs":
                gcs,

            "gcs_total":
                gcs[
                    "total"
                ],

            "unreactive_pupils":
                unreactive_pupils,

            "pupil_reactivity_score":
                pupil_reactivity_score,

            "incomplete_reasons":
                incomplete_reasons,
        }

    assert (
        isinstance(
            gcs[
                "total"
            ],
            int,
        )
    )

    assert (
        isinstance(
            pupil_reactivity_score,
            int,
        )
    )

    total = (
        gcs[
            "total"
        ]
        - pupil_reactivity_score
    )

    assert 1 <= total <= 15

    return {
        "tool":
            "gcs_p",

        "evaluable":
            True,

        "total":
            total,

        "gcs":
            gcs,

        "gcs_total":
            gcs[
                "total"
            ],

        "unreactive_pupils":
            unreactive_pupils,

        "pupil_reactivity_score":
            pupil_reactivity_score,

        "incomplete_reasons":
            [],
    }


def score_four(
    *,
    eye: int | None,
    motor: int | None,
    brainstem: int | None,
    respiration: int | None,
) -> dict:
    """Score FOUR while preserving explicitly unavailable domains."""

    components = {
        "eye":
            _validate_four_domain(
                name="eye",
                value=eye,
            ),

        "motor":
            _validate_four_domain(
                name="motor",
                value=motor,
            ),

        "brainstem":
            _validate_four_domain(
                name="brainstem",
                value=brainstem,
            ),

        "respiration":
            _validate_four_domain(
                name="respiration",
                value=respiration,
            ),
    }

    missing_domains = [
        name
        for name, value
        in components.items()
        if value is None
    ]

    if missing_domains:
        return {
            "tool":
                "four",

            "evaluable":
                False,

            "total":
                None,

            "components":
                components,

            "missing_domains":
                missing_domains,

            "incomplete_reason":
                "domain_unavailable",
        }

    total = sum(
        components.values()
    )

    assert (
        isinstance(
            total,
            int,
        )
        and 0
        <= total
        <= 16
    )

    return {
        "tool":
            "four",

        "evaluable":
            True,

        "total":
            total,

        "components":
            components,

        "missing_domains":
            [],

        "incomplete_reason":
            None,
    }
