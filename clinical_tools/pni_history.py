from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any


DIPHTHERIA_TOXOID = (
    "diphtheria_toxoid"
)

TETANUS_TOXOID = (
    "tetanus_toxoid"
)

PERTUSSIS_ANTIGEN = (
    "pertussis_antigen"
)


TOXOID_VACCINE_COMPONENTS = {
    "dtpa": (
        DIPHTHERIA_TOXOID,
        TETANUS_TOXOID,
        PERTUSSIS_ANTIGEN,
    ),

    "dt": (
        DIPHTHERIA_TOXOID,
        TETANUS_TOXOID,
    ),

    "dtp": (
        DIPHTHERIA_TOXOID,
        TETANUS_TOXOID,
        PERTUSSIS_ANTIGEN,
    ),

    "pentavalent": (
        DIPHTHERIA_TOXOID,
        TETANUS_TOXOID,
        PERTUSSIS_ANTIGEN,
    ),

    "hexa_acellular_rie": (
        DIPHTHERIA_TOXOID,
        TETANUS_TOXOID,
        PERTUSSIS_ANTIGEN,
    ),
}


SPECIAL_PATHWAY_VACCINE_KEYS = {
    "hexa_acellular_rie",
}


KNOWN_NON_TOXOID_VACCINE_KEYS = {
    "vvsr",
    "hepatitis_b",
    "bcg",
    "ipv",
    "rotavirus",
    "pneumococcal_20",
    "pneumococcal_10",
    "meningococcal_c",
    "influenza",
    "covid19",
    "yellow_fever",
    "meningococcal_acwy",
    "mmr",
    "varicella",
    "hepatitis_a",
    "hpv4",
    "dengue",
}


ALLOWED_HISTORY_STATES = {
    "documented_zero_dose",
    "documented_doses",
    "partial_record",
    "unknown",
}


ALLOWED_HISTORY_SCOPES = {
    "complete",
    "partial",
    "unknown",
}


ALLOWED_DOCUMENTATION_SOURCES = {
    "official_registry",
    "vaccination_card",
    "other_health_document",
    "patient_or_caregiver_report",
}


def _as_plain_dict(
    value: Any,
) -> dict[str, Any]:
    if isinstance(
        value,
        dict,
    ):
        return value

    model_dump = getattr(
        value,
        "model_dump",
        None,
    )

    if model_dump is not None:
        return model_dump()

    raise ValueError(
        "history/dose must be a mapping or Pydantic model"
    )


def _as_date(
    value: Any,
) -> date:
    if isinstance(
        value,
        date,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        return date.fromisoformat(
            value
        )

    raise ValueError(
        "invalid administration_date"
    )


def normalize_diphtheria_tetanus_toxoid_history(
    *,
    assessment_date: date,
    histories: list[Any],
    history_scope: str,
) -> dict[str, Any]:
    """
    Normalize documented cross-vaccine D/T toxoid exposures.

    This does not decide whether dTpa is due and does not apply
    recommended/minimum interval rules.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if (
        history_scope
        not in ALLOWED_HISTORY_SCOPES
    ):
        raise ValueError(
            "invalid history_scope"
        )

    seen_history_keys: set[str] = set()

    exposures: list[dict[str, Any]] = []

    unmapped_vaccine_keys: set[str] = set()

    source_history_incomplete = False


    for raw_history in histories:
        history = _as_plain_dict(
            raw_history
        )

        vaccine_key = history.get(
            "vaccine_key"
        )

        if (
            not isinstance(
                vaccine_key,
                str,
            )
            or not vaccine_key
        ):
            raise ValueError(
                "history requires vaccine_key"
            )

        if (
            vaccine_key
            in seen_history_keys
        ):
            raise ValueError(
                "duplicate vaccine history entries are not allowed"
            )

        seen_history_keys.add(
            vaccine_key
        )


        if (
            vaccine_key
            in KNOWN_NON_TOXOID_VACCINE_KEYS
        ):
            continue


        components = (
            TOXOID_VACCINE_COMPONENTS.get(
                vaccine_key
            )
        )

        if components is None:
            unmapped_vaccine_keys.add(
                vaccine_key
            )

            continue


        state = history.get(
            "history_state"
        )

        if (
            state
            not in ALLOWED_HISTORY_STATES
        ):
            raise ValueError(
                f"invalid history_state for {vaccine_key}"
            )


        if state in {
            "partial_record",
            "unknown",
        }:
            source_history_incomplete = True


        doses = (
            history.get(
                "doses"
            )
            or []
        )


        for raw_dose in doses:
            dose = _as_plain_dict(
                raw_dose
            )

            administration_date = _as_date(
                dose.get(
                    "administration_date"
                )
            )

            if (
                administration_date
                > assessment_date
            ):
                raise ValueError(
                    "toxoid administration_date cannot follow assessment_date"
                )


            documentation_source = (
                dose.get(
                    "documentation_source"
                )
            )

            if (
                documentation_source
                not in ALLOWED_DOCUMENTATION_SOURCES
            ):
                raise ValueError(
                    "invalid toxoid documentation_source"
                )


            exposures.append({
                "administration_date":
                    administration_date,

                "gestational_age_weeks_at_administration":
                    dose.get(
                        "gestational_age_weeks_at_administration"
                    ),

                "antigen_components":
                    list(
                        components
                    ),

                "source_vaccine_key":
                    vaccine_key,

                "source_product_key":
                    dose.get(
                        "product_key"
                    ),

                "documentation_source":
                    documentation_source,

                "pregnancy_episode_key":
                    dose.get(
                        "pregnancy_episode_key"
                    ),

                "special_pathway_product":
                    (
                        vaccine_key
                        in SPECIAL_PATHWAY_VACCINE_KEYS
                    ),
            })


    exposures.sort(
        key=lambda item: (
            item[
                "administration_date"
            ],
            item[
                "source_vaccine_key"
            ],
            item.get(
                "source_product_key"
            )
            or "",
        )
    )


    dates = [
        exposure[
            "administration_date"
        ]
        for exposure
        in exposures
    ]


    ambiguous_same_day_exposure_dates = sorted(
        date_value
        for (
            date_value,
            count,
        )
        in Counter(
            dates
        ).items()
        if count > 1
    )


    has_ambiguity = bool(
        source_history_incomplete
        or unmapped_vaccine_keys
        or ambiguous_same_day_exposure_dates
    )


    safe = (
        history_scope == "complete"
        and not has_ambiguity
    )


    if history_scope == "unknown":
        history_state = "unknown"

    elif (
        history_scope == "partial"
        or has_ambiguity
    ):
        history_state = (
            "partial_record"
            if exposures
            else "unknown"
        )

    elif exposures:
        history_state = (
            "documented_exposures"
        )

    else:
        history_state = (
            "documented_zero_exposure"
        )


    return {
        "target_antigens": [
            DIPHTHERIA_TOXOID,
            TETANUS_TOXOID,
        ],

        "history_scope":
            history_scope,

        "history_state":
            history_state,

        "exposures":
            exposures,

        "exposure_event_count":
            len(
                exposures
            ),

        "last_exposure_date":
            (
                exposures[
                    -1
                ][
                    "administration_date"
                ]
                if exposures
                else None
            ),

        "ambiguous_same_day_exposure_dates":
            ambiguous_same_day_exposure_dates,

        "unmapped_vaccine_keys":
            sorted(
                unmapped_vaccine_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "safe_for_interval_evaluation":
            safe,

        "safe_for_basic_series_count":
            safe,
    }



# ------------------------------------------------------------------
# Brazil PNI 2026 — poliomyelitis cross-product history normalization
# ------------------------------------------------------------------
#
# This layer normalizes exposure history only.
# It deliberately does NOT decide whether VIP is due.
#
# Separate normalized vaccine keys preserve clinically relevant
# product identity:
#   - current standalone VIP;
#   - legacy bivalent oral polio vaccine;
#   - supported IPV-containing combination products.
#
# Product identity matters because historical VOPb boosters have
# transition rules that differ from current VIP doses.


POLIO_IPV_EQUIVALENT = "ipv_equivalent"
POLIO_LEGACY_VOPB = "legacy_vopb"


POLIO_VACCINE_COMPONENTS = {
    "ipv": {
        "exposure_class":
            POLIO_IPV_EQUIVALENT,

        "contains_ipv":
            True,

        "legacy_oral":
            False,

        "special_pathway_product":
            False,
    },

    "opv_bivalent_legacy": {
        "exposure_class":
            POLIO_LEGACY_VOPB,

        "contains_ipv":
            False,

        "legacy_oral":
            True,

        "special_pathway_product":
            False,
    },

    "penta_acellular_ipv": {
        "exposure_class":
            POLIO_IPV_EQUIVALENT,

        "contains_ipv":
            True,

        "legacy_oral":
            False,

        "special_pathway_product":
            False,
    },

    "tetra_acellular_ipv": {
        "exposure_class":
            POLIO_IPV_EQUIVALENT,

        "contains_ipv":
            True,

        "legacy_oral":
            False,

        "special_pathway_product":
            False,
    },

    "hexa_acellular_ipv": {
        "exposure_class":
            POLIO_IPV_EQUIVALENT,

        "contains_ipv":
            True,

        "legacy_oral":
            False,

        "special_pathway_product":
            False,
    },

    "hexa_acellular_rie": {
        "exposure_class":
            POLIO_IPV_EQUIVALENT,

        "contains_ipv":
            True,

        "legacy_oral":
            False,

        "special_pathway_product":
            True,
    },
}


# Cross-domain safety boundary:
#
# The federal evidence used by this tranche establishes these
# combination products as IPV-containing poliovirus exposures.
# It does NOT, by itself, extend the canonical D/T toxoid-history
# source contract.
#
# Therefore they remain intentionally absent from
# TOXOID_VACCINE_COMPONENTS.  If supplied to the D/T normalizer,
# they fail closed as unmapped until independently supported by
# authoritative D/T-domain evidence.


# Legacy oral poliovirus vaccine has no D/T/P component and must be
# known to the toxoid normalizer so that it is skipped rather than
# misclassified as an unknown toxoid-family product.
KNOWN_NON_TOXOID_VACCINE_KEYS.add(
    "opv_bivalent_legacy"
)


def normalize_polio_history(
    *,
    assessment_date: date,
    histories: list[Any],
    history_scope: str,
) -> dict[str, Any]:
    """
    Normalize language-neutral poliovirus vaccine exposures.

    This function preserves vaccine/product identity and chronology.
    It does not decide whether a routine VIP dose or booster is due.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if (
        history_scope
        not in ALLOWED_HISTORY_SCOPES
    ):
        raise ValueError(
            "invalid history_scope"
        )

    seen_history_keys: set[str] = set()

    present_history_keys: set[str] = set()

    exposures: list[dict[str, Any]] = []

    unmapped_vaccine_keys: set[str] = set()

    source_history_incomplete = False


    known_non_polio_keys = (
        set(
            KNOWN_NON_TOXOID_VACCINE_KEYS
        )
        | set(
            TOXOID_VACCINE_COMPONENTS
        )
    ) - set(
        POLIO_VACCINE_COMPONENTS
    )


    for raw_history in histories:
        history = _as_plain_dict(
            raw_history
        )

        vaccine_key = history.get(
            "vaccine_key"
        )

        if (
            not isinstance(
                vaccine_key,
                str,
            )
            or not vaccine_key
        ):
            raise ValueError(
                "history requires vaccine_key"
            )

        if (
            vaccine_key
            in seen_history_keys
        ):
            raise ValueError(
                "duplicate vaccine history entries are not allowed"
            )

        seen_history_keys.add(
            vaccine_key
        )


        mapping = POLIO_VACCINE_COMPONENTS.get(
            vaccine_key
        )


        if mapping is None:
            if (
                vaccine_key
                in known_non_polio_keys
            ):
                continue

            unmapped_vaccine_keys.add(
                vaccine_key
            )

            continue


        present_history_keys.add(
            vaccine_key
        )


        state = history.get(
            "history_state"
        )

        if (
            state
            not in ALLOWED_HISTORY_STATES
        ):
            raise ValueError(
                f"invalid history_state for {vaccine_key}"
            )


        doses = (
            history.get(
                "doses"
            )
            or []
        )

        undated = int(
            history.get(
                "reported_prior_doses_without_exact_dates",
                0,
            )
            or 0
        )


        if state == "unknown":
            if doses or undated:
                raise ValueError(
                    f"unknown history for {vaccine_key} "
                    "cannot contain dose evidence"
                )

            source_history_incomplete = True


        elif state == "documented_zero_dose":
            if doses or undated:
                raise ValueError(
                    f"documented zero-dose history for "
                    f"{vaccine_key} cannot contain dose evidence"
                )


        elif state == "documented_doses":
            if not doses:
                raise ValueError(
                    f"documented_doses for {vaccine_key} "
                    "requires at least one dated dose"
                )

            if undated:
                source_history_incomplete = True


        elif state == "partial_record":
            if (
                not doses
                and undated == 0
            ):
                raise ValueError(
                    f"partial_record for {vaccine_key} "
                    "requires dose evidence"
                )

            source_history_incomplete = True


        for raw_dose in doses:
            dose = _as_plain_dict(
                raw_dose
            )

            administration_date = _as_date(
                dose.get(
                    "administration_date"
                )
            )

            if (
                administration_date
                > assessment_date
            ):
                raise ValueError(
                    f"{vaccine_key} administration_date "
                    "cannot follow assessment_date"
                )


            documentation_source = dose.get(
                "documentation_source"
            )

            if (
                documentation_source
                not in ALLOWED_DOCUMENTATION_SOURCES
            ):
                raise ValueError(
                    f"invalid documentation_source for "
                    f"{vaccine_key}"
                )


            product_key = dose.get(
                "product_key"
            )


            # The polio normalizer uses distinct history keys to
            # preserve product identity.  Cross-labelling a VOPb
            # event inside an IPV history (or vice versa) would
            # defeat that safety property.
            if (
                product_key is not None
                and product_key != vaccine_key
            ):
                raise ValueError(
                    f"{vaccine_key} history contains incompatible "
                    f"product_key={product_key}"
                )


            exposures.append({
                "administration_date":
                    administration_date,

                "source_vaccine_key":
                    vaccine_key,

                "source_product_key":
                    product_key,

                "product_name":
                    dose.get(
                        "product_name"
                    ),

                "dose_number":
                    dose.get(
                        "dose_number"
                    ),

                "dose_label":
                    dose.get(
                        "dose_label"
                    ),

                "documentation_source":
                    documentation_source,

                "exposure_class":
                    mapping[
                        "exposure_class"
                    ],

                "contains_ipv":
                    mapping[
                        "contains_ipv"
                    ],

                "legacy_oral":
                    mapping[
                        "legacy_oral"
                    ],

                "special_pathway_product":
                    mapping[
                        "special_pathway_product"
                    ],
            })


    exposures.sort(
        key=lambda item: (
            item[
                "administration_date"
            ],
            item[
                "source_vaccine_key"
            ],
        )
    )


    date_counts = Counter(
        exposure[
            "administration_date"
        ]
        for exposure in exposures
    )


    ambiguous_same_day_exposure_dates = sorted(
        exposure_date
        for exposure_date, count
        in date_counts.items()
        if count > 1
    )


    ipv_equivalent_exposure_count = sum(
        1
        for exposure in exposures
        if exposure[
            "contains_ipv"
        ]
    )


    legacy_vopb_exposure_count = sum(
        1
        for exposure in exposures
        if exposure[
            "legacy_oral"
        ]
    )


    special_pathway_exposure_present = any(
        exposure[
            "special_pathway_product"
        ]
        for exposure in exposures
    )


    if (
        history_scope
        == "unknown"
    ):
        history_state = "unknown"

    elif (
        history_scope
        == "partial"
        or source_history_incomplete
        or unmapped_vaccine_keys
        or ambiguous_same_day_exposure_dates
    ):
        history_state = "partial_or_uncertain"

    elif exposures:
        history_state = "documented_exposures"

    else:
        history_state = "documented_zero_exposure"


    safe_base = (
        history_scope
        == "complete"
        and not source_history_incomplete
        and not unmapped_vaccine_keys
        and not ambiguous_same_day_exposure_dates
    )


    return {
        "target_antigen":
            "poliovirus",

        "history_scope":
            history_scope,

        "history_state":
            history_state,

        "present_history_keys":
            sorted(
                present_history_keys
            ),

        "ipv_history_supplied":
            "ipv"
            in present_history_keys,

        "legacy_vopb_history_supplied":
            "opv_bivalent_legacy"
            in present_history_keys,

        "combination_history_keys_supplied":
            sorted(
                present_history_keys
                & {
                    "penta_acellular_ipv",
                    "tetra_acellular_ipv",
                    "hexa_acellular_ipv",
                    "hexa_acellular_rie",
                }
            ),

        "exposures":
            exposures,

        "exposure_event_count":
            len(
                exposures
            ),

        "ipv_equivalent_exposure_count":
            ipv_equivalent_exposure_count,

        "legacy_vopb_exposure_count":
            legacy_vopb_exposure_count,

        "last_exposure_date": (
            exposures[
                -1
            ][
                "administration_date"
            ]
            if exposures
            else None
        ),

        "ambiguous_same_day_exposure_dates":
            ambiguous_same_day_exposure_dates,

        "unmapped_vaccine_keys":
            sorted(
                unmapped_vaccine_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "special_pathway_exposure_present":
            special_pathway_exposure_present,

        "safe_for_interval_evaluation":
            safe_base,

        "safe_for_primary_series_count":
            safe_base,

        "safe_for_transition_evaluation": (
            safe_base
            and not special_pathway_exposure_present
        ),
    }



# ------------------------------------------------------------------
# Brazil PNI 2026 — routine pneumococcal VPC10/VPC20 history
# ------------------------------------------------------------------
#
# The 2026 transition intentionally uses VPC10 and VPC20 in
# different schedule roles. This layer merges chronology while
# preserving product identity.
#
# It performs history normalization only. It does NOT decide which
# dose is due, and it does NOT resolve the authoritative ambiguity
# in the exact-11-month/no-history branch.


PNEUMOCOCCAL_ROUTINE_PRODUCTS = {
    "pneumococcal_10": {
        "official_acronym":
            "VPC10",

        "valency":
            10,
    },

    "pneumococcal_20": {
        "official_acronym":
            "VPC20",

        "valency":
            20,
    },
}


def normalize_pneumococcal_history(
    *,
    assessment_date: date,
    histories: list[Any],
    history_scope: str,
) -> dict[str, Any]:
    """
    Normalize routine-child VPC10/VPC20 history.

    Product identity and chronology are preserved. This function
    does not assign D1/D2/booster roles and does not consume
    VPC13/VPP23/RIE pathways.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if (
        history_scope
        not in ALLOWED_HISTORY_SCOPES
    ):
        raise ValueError(
            "invalid history_scope"
        )

    seen_history_keys: set[str] = set()

    present_history_keys: set[str] = set()

    exposures: list[dict[str, Any]] = []

    unmapped_vaccine_keys: set[str] = set()

    source_history_incomplete = False


    known_non_target_keys = (
        set(
            KNOWN_NON_TOXOID_VACCINE_KEYS
        )
        | set(
            TOXOID_VACCINE_COMPONENTS
        )
        | set(
            globals().get(
                "POLIO_VACCINE_COMPONENTS",
                {},
            )
        )
    ) - set(
        PNEUMOCOCCAL_ROUTINE_PRODUCTS
    )


    for raw_history in histories:
        history = _as_plain_dict(
            raw_history
        )

        vaccine_key = history.get(
            "vaccine_key"
        )

        if (
            not isinstance(
                vaccine_key,
                str,
            )
            or not vaccine_key
        ):
            raise ValueError(
                "history requires vaccine_key"
            )

        if (
            vaccine_key
            in seen_history_keys
        ):
            raise ValueError(
                "duplicate vaccine history entries are not allowed"
            )

        seen_history_keys.add(
            vaccine_key
        )


        mapping = PNEUMOCOCCAL_ROUTINE_PRODUCTS.get(
            vaccine_key
        )


        if mapping is None:
            if (
                vaccine_key
                in known_non_target_keys
            ):
                continue

            unmapped_vaccine_keys.add(
                vaccine_key
            )

            continue


        present_history_keys.add(
            vaccine_key
        )


        state = history.get(
            "history_state"
        )

        if (
            state
            not in ALLOWED_HISTORY_STATES
        ):
            raise ValueError(
                f"invalid history_state for {vaccine_key}"
            )


        doses = (
            history.get(
                "doses"
            )
            or []
        )

        undated = int(
            history.get(
                "reported_prior_doses_without_exact_dates",
                0,
            )
            or 0
        )


        if state == "unknown":
            if doses or undated:
                raise ValueError(
                    f"unknown history for {vaccine_key} "
                    "cannot contain dose evidence"
                )

            source_history_incomplete = True


        elif state == "documented_zero_dose":
            if doses or undated:
                raise ValueError(
                    f"documented zero-dose history for "
                    f"{vaccine_key} cannot contain dose evidence"
                )


        elif state == "documented_doses":
            if not doses:
                raise ValueError(
                    f"documented_doses for {vaccine_key} "
                    "requires at least one dated dose"
                )

            if undated:
                source_history_incomplete = True


        elif state == "partial_record":
            if (
                not doses
                and undated == 0
            ):
                raise ValueError(
                    f"partial_record for {vaccine_key} "
                    "requires dose evidence"
                )

            source_history_incomplete = True


        for raw_dose in doses:
            dose = _as_plain_dict(
                raw_dose
            )

            administration_date = _as_date(
                dose.get(
                    "administration_date"
                )
            )

            if (
                administration_date
                > assessment_date
            ):
                raise ValueError(
                    f"{vaccine_key} administration_date "
                    "cannot follow assessment_date"
                )


            documentation_source = dose.get(
                "documentation_source"
            )

            if (
                documentation_source
                not in ALLOWED_DOCUMENTATION_SOURCES
            ):
                raise ValueError(
                    f"invalid documentation_source for "
                    f"{vaccine_key}"
                )


            product_key = dose.get(
                "product_key"
            )


            if (
                product_key is not None
                and product_key != vaccine_key
            ):
                raise ValueError(
                    f"{vaccine_key} history contains incompatible "
                    f"product_key={product_key}"
                )


            exposures.append({
                "administration_date":
                    administration_date,

                "source_vaccine_key":
                    vaccine_key,

                "source_product_key":
                    product_key,

                "official_acronym":
                    mapping[
                        "official_acronym"
                    ],

                "valency":
                    mapping[
                        "valency"
                    ],

                "product_name":
                    dose.get(
                        "product_name"
                    ),

                "dose_number":
                    dose.get(
                        "dose_number"
                    ),

                "dose_label":
                    dose.get(
                        "dose_label"
                    ),

                "documentation_source":
                    documentation_source,
            })


    exposures.sort(
        key=lambda item: (
            item[
                "administration_date"
            ],
            item[
                "source_vaccine_key"
            ],
        )
    )


    date_counts = Counter(
        exposure[
            "administration_date"
        ]
        for exposure in exposures
    )


    ambiguous_same_day_exposure_dates = sorted(
        exposure_date
        for exposure_date, count
        in date_counts.items()
        if count > 1
    )


    vpc10_count = sum(
        1
        for exposure in exposures
        if exposure[
            "source_vaccine_key"
        ]
        == "pneumococcal_10"
    )


    vpc20_count = sum(
        1
        for exposure in exposures
        if exposure[
            "source_vaccine_key"
        ]
        == "pneumococcal_20"
    )


    if (
        history_scope
        == "unknown"
    ):
        history_state = "unknown"

    elif (
        history_scope
        == "partial"
        or source_history_incomplete
        or unmapped_vaccine_keys
        or ambiguous_same_day_exposure_dates
    ):
        history_state = "partial_or_uncertain"

    elif exposures:
        history_state = "documented_exposures"

    else:
        history_state = "documented_zero_exposure"


    safe_base = (
        history_scope
        == "complete"
        and not source_history_incomplete
        and not unmapped_vaccine_keys
        and not ambiguous_same_day_exposure_dates
    )


    return {
        "target_family":
            "pneumococcal_conjugate_routine_child",

        "history_scope":
            history_scope,

        "history_state":
            history_state,

        "present_history_keys":
            sorted(
                present_history_keys
            ),

        "vpc10_history_supplied":
            "pneumococcal_10"
            in present_history_keys,

        "vpc20_history_supplied":
            "pneumococcal_20"
            in present_history_keys,

        "exposures":
            exposures,

        "exposure_event_count":
            len(
                exposures
            ),

        "vpc10_exposure_count":
            vpc10_count,

        "vpc20_exposure_count":
            vpc20_count,

        "mixed_vpc10_vpc20_history":
            (
                vpc10_count > 0
                and vpc20_count > 0
            ),

        "last_exposure_date": (
            exposures[
                -1
            ][
                "administration_date"
            ]
            if exposures
            else None
        ),

        "ambiguous_same_day_exposure_dates":
            ambiguous_same_day_exposure_dates,

        "unmapped_vaccine_keys":
            sorted(
                unmapped_vaccine_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "safe_for_chronology_evaluation":
            safe_base,

        "safe_for_role_assignment":
            safe_base,

        "source_hold_11m_no_history":
            True,
    }



INFLUENZA_CYCLE_HISTORY_STATES = frozenset(
    {
        "documented_zero_dose",
        "documented_doses",
        "unknown",
        "partial_record",
    }
)

INFLUENZA_PRIOR_CYCLE_VACCINATION_STATES = frozenset(
    {
        "documented_prior",
        "documented_none",
        "unknown",
    }
)

INFLUENZA_STRATEGY_LAYERS = frozenset(
    {
        "routine",
        "special",
    }
)

INFLUENZA_PUBLIC_ROUTINE_PRODUCT_KEYS = frozenset(
    {
        "influenza",
    }
)


def _influenza_plain_mapping(
    value,
    *,
    field_name,
):
    if hasattr(
        value,
        "model_dump",
    ):
        value = value.model_dump()

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"{field_name} must be a mapping or model"
        )

    return dict(
        value
    )


def normalize_influenza_history(
    *,
    assessment_date,
    history,
    history_scope,
    current_cycle_key,
    current_cycle_history_state,
    current_cycle_events,
    prior_cycle_vaccination_state,
):
    """
    Normalize influenza lifetime and explicit cycle evidence.

    The cycle key is opaque and source-supplied. This function
    never derives cycle identity from administration year, parses
    geography from the key, or assigns D1/D2/DU roles.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if history_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "invalid influenza history_scope"
        )

    if (
        not isinstance(
            current_cycle_key,
            str,
        )
        or not current_cycle_key.strip()
    ):
        raise ValueError(
            "current_cycle_key must be a non-empty opaque string"
        )

    current_cycle_key = (
        current_cycle_key.strip()
    )

    if (
        current_cycle_history_state
        not in INFLUENZA_CYCLE_HISTORY_STATES
    ):
        raise ValueError(
            "invalid current_cycle_history_state"
        )

    if (
        prior_cycle_vaccination_state
        not in INFLUENZA_PRIOR_CYCLE_VACCINATION_STATES
    ):
        raise ValueError(
            "invalid prior_cycle_vaccination_state"
        )

    if not isinstance(
        current_cycle_events,
        (list, tuple),
    ):
        raise ValueError(
            "current_cycle_events must be a list or tuple"
        )

    lifetime = _influenza_plain_mapping(
        history,
        field_name="history",
    )

    if (
        lifetime.get(
            "vaccine_key"
        )
        != "influenza"
    ):
        raise ValueError(
            "influenza history must use vaccine_key influenza"
        )

    lifetime_history_state = lifetime.get(
        "history_state"
    )

    if lifetime_history_state not in {
        "documented_zero_dose",
        "documented_doses",
        "unknown",
        "partial_record",
    }:
        raise ValueError(
            "invalid influenza lifetime history_state"
        )

    raw_lifetime_doses = list(
        lifetime.get(
            "doses"
        )
        or []
    )

    reported_undated = int(
        lifetime.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if reported_undated < 0:
        raise ValueError(
            "reported prior influenza dose count cannot be negative"
        )

    lifetime_events = []
    lifetime_dates = []
    unsupported_product_keys = set()

    for index, raw_dose in enumerate(
        raw_lifetime_doses
    ):
        dose = _influenza_plain_mapping(
            raw_dose,
            field_name=(
                f"history.doses[{index}]"
            ),
        )

        administration_date = dose.get(
            "administration_date"
        )

        if not isinstance(
            administration_date,
            date,
        ):
            raise ValueError(
                "influenza lifetime administration_date "
                "must be a date"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "influenza lifetime administration_date "
                "cannot follow assessment_date"
            )

        product_key = dose.get(
            "product_key"
        )

        if (
            product_key
            not in INFLUENZA_PUBLIC_ROUTINE_PRODUCT_KEYS
        ):
            unsupported_product_keys.add(
                (
                    product_key
                    if isinstance(
                        product_key,
                        str,
                    )
                    else "<missing>"
                )
            )

        event = {
            "administration_date":
                administration_date,

            "source_product_key":
                product_key,

            "documentation_source":
                dose.get(
                    "documentation_source"
                ),
        }

        lifetime_events.append(
            event
        )

        lifetime_dates.append(
            administration_date
        )

    if (
        lifetime_history_state
        == "documented_zero_dose"
        and (
            lifetime_events
            or reported_undated
        )
    ):
        raise ValueError(
            "documented zero influenza lifetime history "
            "cannot contain prior-dose evidence"
        )

    if (
        lifetime_history_state
        == "documented_doses"
        and not lifetime_events
        and reported_undated == 0
    ):
        raise ValueError(
            "documented influenza lifetime doses require evidence"
        )

    lifetime_date_counts = {}

    for event_date in lifetime_dates:
        lifetime_date_counts[
            event_date
        ] = (
            lifetime_date_counts.get(
                event_date,
                0,
            )
            + 1
        )

    ambiguous_lifetime_same_day_dates = sorted(
        event_date
        for event_date, count
        in lifetime_date_counts.items()
        if count > 1
    )

    normalized_cycle_events = []
    seen_cycle_dates = set()

    for index, raw_event in enumerate(
        current_cycle_events
    ):
        event = _influenza_plain_mapping(
            raw_event,
            field_name=(
                f"current_cycle_events[{index}]"
            ),
        )

        administration_date = event.get(
            "administration_date"
        )

        strategy_layer = event.get(
            "strategy_layer"
        )

        if not isinstance(
            administration_date,
            date,
        ):
            raise ValueError(
                "influenza current-cycle administration_date "
                "must be a date"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "influenza current-cycle administration_date "
                "cannot follow assessment_date"
            )

        if (
            strategy_layer
            not in INFLUENZA_STRATEGY_LAYERS
        ):
            raise ValueError(
                "invalid influenza strategy_layer"
            )

        if (
            administration_date
            in seen_cycle_dates
        ):
            raise ValueError(
                "duplicate influenza current-cycle event date"
            )

        seen_cycle_dates.add(
            administration_date
        )

        matching_lifetime_events = [
            lifetime_event
            for lifetime_event
            in lifetime_events
            if lifetime_event[
                "administration_date"
            ]
            == administration_date
        ]

        if (
            len(
                matching_lifetime_events
            )
            != 1
        ):
            raise ValueError(
                "influenza current-cycle event must reconcile "
                "to exactly one lifetime dated event"
            )

        lifetime_event = (
            matching_lifetime_events[
                0
            ]
        )

        normalized_cycle_events.append(
            {
                "administration_date":
                    administration_date,

                "strategy_layer":
                    strategy_layer,

                "source_product_key":
                    lifetime_event[
                        "source_product_key"
                    ],

                "documentation_source":
                    lifetime_event[
                        "documentation_source"
                    ],
            }
        )

    if (
        current_cycle_history_state
        == "documented_zero_dose"
        and normalized_cycle_events
    ):
        raise ValueError(
            "documented zero influenza current cycle "
            "cannot contain events"
        )

    if (
        current_cycle_history_state
        == "documented_doses"
        and not normalized_cycle_events
    ):
        raise ValueError(
            "documented influenza current-cycle doses "
            "require events"
        )

    if (
        current_cycle_history_state
        == "unknown"
        and normalized_cycle_events
    ):
        raise ValueError(
            "unknown influenza current-cycle history "
            "cannot contain asserted cycle events"
        )

    routine_events = [
        event
        for event in normalized_cycle_events
        if event[
            "strategy_layer"
        ]
        == "routine"
    ]

    special_events = [
        event
        for event in normalized_cycle_events
        if event[
            "strategy_layer"
        ]
        == "special"
    ]

    cycle_dates = {
        event[
            "administration_date"
        ]
        for event in normalized_cycle_events
    }

    unassigned_lifetime_events = [
        event
        for event in lifetime_events
        if event[
            "administration_date"
        ]
        not in cycle_dates
    ]

    generic_history_incomplete = (
        history_scope
        != "complete"
        or lifetime_history_state
        in {
            "unknown",
            "partial_record",
        }
    )

    cycle_history_incomplete = (
        current_cycle_history_state
        in {
            "unknown",
            "partial_record",
        }
    )

    priming_history_incomplete = (
        prior_cycle_vaccination_state
        == "unknown"
    )

    unsupported_product_identity = bool(
        unsupported_product_keys
    )

    chronology_ambiguous = bool(
        ambiguous_lifetime_same_day_dates
    )

    excess_routine_cycle_events = (
        len(
            routine_events
        )
        > 2
    )

    source_history_incomplete = (
        generic_history_incomplete
        or cycle_history_incomplete
        or priming_history_incomplete
    )

    safe_for_chronology_evaluation = (
        not generic_history_incomplete
        and not cycle_history_incomplete
        and not chronology_ambiguous
        and not unsupported_product_identity
    )

    safe_for_routine_child_evaluation = (
        safe_for_chronology_evaluation
        and not priming_history_incomplete
        and not special_events
        and not excess_routine_cycle_events
    )

    return {
        "target_family":
            "influenza_routine_child",

        "history_scope":
            history_scope,

        "lifetime_history_state":
            lifetime_history_state,

        "lifetime_dated_event_count":
            len(
                lifetime_events
            ),

        "lifetime_reported_prior_doses_without_exact_dates":
            reported_undated,

        "current_cycle_key":
            current_cycle_key,

        "cycle_key_opaque":
            True,

        "cycle_key_parsed":
            False,

        "cycle_identity_derived_from_calendar_year":
            False,

        "geography_inferred_from_cycle_key":
            False,

        "current_cycle_history_state":
            current_cycle_history_state,

        "prior_cycle_vaccination_state":
            prior_cycle_vaccination_state,

        "current_cycle_events":
            normalized_cycle_events,

        "current_cycle_event_count":
            len(
                normalized_cycle_events
            ),

        "routine_event_count":
            len(
                routine_events
            ),

        "special_event_count":
            len(
                special_events
            ),

        "special_strategy_present":
            bool(
                special_events
            ),

        "unassigned_lifetime_events":
            unassigned_lifetime_events,

        "unassigned_lifetime_event_count":
            len(
                unassigned_lifetime_events
            ),

        "ambiguous_lifetime_same_day_dates":
            ambiguous_lifetime_same_day_dates,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "generic_history_incomplete":
            generic_history_incomplete,

        "cycle_history_incomplete":
            cycle_history_incomplete,

        "priming_history_incomplete":
            priming_history_incomplete,

        "source_history_incomplete":
            source_history_incomplete,

        "excess_routine_cycle_events":
            excess_routine_cycle_events,

        "safe_for_chronology_evaluation":
            safe_for_chronology_evaluation,

        "safe_for_routine_child_evaluation":
            safe_for_routine_child_evaluation,

        "normalizer_assigns_dose_roles":
            False,

        "special_condition_inferred":
            False,
    }



COVID_CHILD_PRODUCT_PFIZER = (
    "covid_pfizer_comirnaty_pediatric_under5"
)

COVID_CHILD_PRODUCT_MODERNA = (
    "covid_moderna_spikevax"
)

COVID_CHILD_PRODUCT_CORONAVAC = (
    "covid_coronavac_legacy"
)

COVID_CHILD_SUPPORTED_PRODUCTS = frozenset(
    {
        COVID_CHILD_PRODUCT_PFIZER,
        COVID_CHILD_PRODUCT_MODERNA,
        COVID_CHILD_PRODUCT_CORONAVAC,
    }
)

COVID_CHILD_COMPLETE_PRODUCT_SEQUENCES = frozenset(
    {
        (
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_PFIZER,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_MODERNA,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_PFIZER,
        ),
        (
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_CORONAVAC,
            COVID_CHILD_PRODUCT_MODERNA,
        ),
    }
)

COVID_CHILD_AUTHORIZED_PRODUCT_PREFIXES = frozenset(
    sequence[:length]
    for sequence in COVID_CHILD_COMPLETE_PRODUCT_SEQUENCES
    for length in range(
        1,
        len(sequence),
    )
)

COVID_CHILD_INTERVAL_1_TO_2_DAYS = 28
COVID_CHILD_INTERVAL_2_TO_3_DAYS = 56


def _covid_child_plain_mapping(
    value,
    *,
    field_name,
):
    if hasattr(
        value,
        "model_dump",
    ):
        value = value.model_dump()

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"{field_name} must be a mapping or model"
        )

    return dict(
        value
    )


def _covid_child_add_months_clamped(
    value,
    months,
):
    import calendar

    month_index = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + month_index // 12
    )

    month = (
        month_index % 12
        + 1
    )

    day = min(
        value.day,
        calendar.monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def _covid_child_sequence_state(
    sequence,
):
    sequence = tuple(
        sequence
    )

    if not sequence:
        return "documented_zero_exposure"

    if (
        sequence
        in COVID_CHILD_COMPLETE_PRODUCT_SEQUENCES
    ):
        return "source_authorized_complete"

    if (
        sequence
        in COVID_CHILD_AUTHORIZED_PRODUCT_PREFIXES
    ):
        return "source_authorized_incomplete_prefix"

    return "unsupported_sequence"


def normalize_covid_child_history(
    *,
    assessment_date,
    date_of_birth,
    history,
    history_scope,
    registration_role_events=None,
):
    """
    Normalize product-sensitive COVID-19 history for the
    healthy-child under-5 basic-series layer.

    This function preserves product-local registration labels
    separately from chronological clinical exposure ordinals.
    It does not recommend a vaccine or assign current due status.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if history_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "invalid COVID history_scope"
        )

    lifetime = _covid_child_plain_mapping(
        history,
        field_name="history",
    )

    if (
        lifetime.get(
            "vaccine_key"
        )
        != "covid_19"
    ):
        raise ValueError(
            "COVID child history must use vaccine_key covid_19"
        )

    lifetime_history_state = lifetime.get(
        "history_state"
    )

    if lifetime_history_state not in {
        "documented_zero_dose",
        "documented_doses",
        "unknown",
        "partial_record",
    }:
        raise ValueError(
            "invalid COVID lifetime history_state"
        )

    raw_doses = list(
        lifetime.get(
            "doses"
        )
        or []
    )

    reported_undated = int(
        lifetime.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if reported_undated < 0:
        raise ValueError(
            "reported undated COVID dose count cannot be negative"
        )

    if (
        lifetime_history_state
        == "documented_zero_dose"
        and (
            raw_doses
            or reported_undated
        )
    ):
        raise ValueError(
            "documented zero COVID history cannot contain dose evidence"
        )

    if (
        lifetime_history_state
        == "documented_doses"
        and not raw_doses
        and reported_undated == 0
    ):
        raise ValueError(
            "documented COVID doses require dose evidence"
        )

    registration_role_events = list(
        registration_role_events
        or []
    )

    registration_roles_by_date = {}

    for index, raw_role in enumerate(
        registration_role_events
    ):
        item = _covid_child_plain_mapping(
            raw_role,
            field_name=(
                f"registration_role_events[{index}]"
            ),
        )

        event_date = item.get(
            "administration_date"
        )

        source_role = item.get(
            "source_registration_role"
        )

        if not isinstance(
            event_date,
            date,
        ):
            raise ValueError(
                "COVID registration metadata administration_date "
                "must be a date"
            )

        if (
            not isinstance(
                source_role,
                str,
            )
            or not source_role.strip()
        ):
            raise ValueError(
                "COVID source_registration_role must be "
                "a non-empty string"
            )

        if (
            event_date
            in registration_roles_by_date
        ):
            raise ValueError(
                "duplicate COVID registration metadata date"
            )

        registration_roles_by_date[
            event_date
        ] = source_role.strip()

    age_6m = _covid_child_add_months_clamped(
        date_of_birth,
        6,
    )

    age_5y = _covid_child_add_months_clamped(
        date_of_birth,
        60,
    )

    lifetime_events = []
    date_counts = {}
    unsupported_product_keys = set()

    for index, raw_dose in enumerate(
        raw_doses
    ):
        dose = _covid_child_plain_mapping(
            raw_dose,
            field_name=(
                f"history.doses[{index}]"
            ),
        )

        administration_date = dose.get(
            "administration_date"
        )

        if not isinstance(
            administration_date,
            date,
        ):
            raise ValueError(
                "COVID administration_date must be a date"
            )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "COVID administration_date cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "COVID administration_date cannot follow assessment_date"
            )

        product_key = dose.get(
            "product_key"
        )

        if (
            product_key
            not in COVID_CHILD_SUPPORTED_PRODUCTS
        ):
            unsupported_product_keys.add(
                (
                    product_key
                    if isinstance(
                        product_key,
                        str,
                    )
                    else "<missing>"
                )
            )

        if (
            administration_date
            < age_6m
        ):
            age_scope = (
                "before_under5_series_start"
            )

        elif (
            administration_date
            < age_5y
        ):
            age_scope = (
                "under5_series_age"
            )

        else:
            age_scope = (
                "at_or_after_age5"
            )

        lifetime_events.append(
            {
                "administration_date":
                    administration_date,

                "product_key":
                    product_key,

                "documentation_source":
                    dose.get(
                        "documentation_source"
                    ),

                "source_registration_role":
                    registration_roles_by_date.get(
                        administration_date
                    ),

                "age_scope_at_exposure":
                    age_scope,
            }
        )

        date_counts[
            administration_date
        ] = (
            date_counts.get(
                administration_date,
                0,
            )
            + 1
        )

    ambiguous_dates = sorted(
        event_date
        for event_date, count
        in date_counts.items()
        if count > 1
    )

    if ambiguous_dates:
        raise ValueError(
            "same-day COVID lifetime event ambiguity"
        )

    lifetime_dates = {
        event[
            "administration_date"
        ]
        for event in lifetime_events
    }

    unreconciled_registration_dates = sorted(
        event_date
        for event_date
        in registration_roles_by_date
        if event_date not in lifetime_dates
    )

    if unreconciled_registration_dates:
        raise ValueError(
            "COVID registration metadata must reconcile "
            "to a dated lifetime event"
        )

    lifetime_events.sort(
        key=lambda event: event[
            "administration_date"
        ]
    )

    for ordinal, event in enumerate(
        lifetime_events,
        1,
    ):
        event[
            "lifetime_chronology_ordinal"
        ] = ordinal

    under5_events = [
        event
        for event in lifetime_events
        if event[
            "age_scope_at_exposure"
        ]
        == "under5_series_age"
    ]

    for ordinal, event in enumerate(
        under5_events,
        1,
    ):
        event[
            "clinical_exposure_ordinal"
        ] = ordinal

    for event in lifetime_events:
        if (
            "clinical_exposure_ordinal"
            not in event
        ):
            event[
                "clinical_exposure_ordinal"
            ] = None

    clinical_product_sequence = tuple(
        event[
            "product_key"
        ]
        for event in under5_events
    )

    if unsupported_product_keys:
        product_sequence_state = (
            "unsupported_sequence"
        )

    else:
        product_sequence_state = (
            _covid_child_sequence_state(
                clinical_product_sequence
            )
        )

    interval_checks = []

    if len(
        under5_events
    ) >= 2:
        actual_days = (
            under5_events[
                1
            ][
                "administration_date"
            ]
            - under5_events[
                0
            ][
                "administration_date"
            ]
        ).days

        interval_checks.append(
            {
                "from_ordinal":
                    1,

                "to_ordinal":
                    2,

                "actual_days":
                    actual_days,

                "required_minimum_days":
                    COVID_CHILD_INTERVAL_1_TO_2_DAYS,

                "valid":
                    (
                        actual_days
                        >= COVID_CHILD_INTERVAL_1_TO_2_DAYS
                    ),
            }
        )

    if len(
        under5_events
    ) >= 3:
        actual_days = (
            under5_events[
                2
            ][
                "administration_date"
            ]
            - under5_events[
                1
            ][
                "administration_date"
            ]
        ).days

        interval_checks.append(
            {
                "from_ordinal":
                    2,

                "to_ordinal":
                    3,

                "actual_days":
                    actual_days,

                "required_minimum_days":
                    COVID_CHILD_INTERVAL_2_TO_3_DAYS,

                "valid":
                    (
                        actual_days
                        >= COVID_CHILD_INTERVAL_2_TO_3_DAYS
                    ),
            }
        )

    intervals_valid = all(
        check[
            "valid"
        ]
        for check in interval_checks
    )

    before_6m_events = [
        event
        for event in lifetime_events
        if event[
            "age_scope_at_exposure"
        ]
        == "before_under5_series_start"
    ]

    at_or_after_5y_events = [
        event
        for event in lifetime_events
        if event[
            "age_scope_at_exposure"
        ]
        == "at_or_after_age5"
    ]

    source_history_incomplete = (
        history_scope
        != "complete"
        or lifetime_history_state
        in {
            "unknown",
            "partial_record",
        }
        or reported_undated > 0
    )

    chronology_ambiguous = False

    pre_6m_history_present = bool(
        before_6m_events
    )

    unsupported_sequence = (
        product_sequence_state
        == "unsupported_sequence"
    )

    safe_for_under5_series_evaluation = (
        not source_history_incomplete
        and not chronology_ambiguous
        and not unsupported_product_keys
        and not unsupported_sequence
        and intervals_valid
        and not pre_6m_history_present
    )

    return {
        "target_family": (
            "covid_19_healthy_child_under5_basic_series"
        ),

        "history_scope":
            history_scope,

        "lifetime_history_state":
            lifetime_history_state,

        "age_6m_date":
            age_6m,

        "age_5y_date":
            age_5y,

        "events":
            lifetime_events,

        "lifetime_event_count":
            len(
                lifetime_events
            ),

        "clinical_product_sequence":
            list(
                clinical_product_sequence
            ),

        "product_sequence_state":
            product_sequence_state,

        "interval_checks":
            interval_checks,

        "intervals_valid":
            intervals_valid,

        "valid_under5_exposure_count":
            len(
                under5_events
            ),

        "before_6m_event_count":
            len(
                before_6m_events
            ),

        "at_or_after_5y_event_count":
            len(
                at_or_after_5y_events
            ),

        "reported_undated_event_count":
            reported_undated,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "chronology_ambiguous":
            chronology_ambiguous,

        "safe_for_under5_series_evaluation":
            safe_for_under5_series_evaluation,

        "registration_role_metadata_present":
            bool(
                registration_roles_by_date
            ),

        "registration_role_defines_clinical_ordinal":
            False,

        "clinical_ordinal_derived_from_chronology":
            True,

        "current_2026_initiation_product_key":
            COVID_CHILD_PRODUCT_PFIZER,

        "age_out_rule_resolved":
            True,

        "post_age5_under5_completion_allowed":
            False,

        "normalizer_assigns_due_decision":
            False,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }



YELLOW_FEVER_PRODUCT_STANDARD = (
    "yellow_fever_standard"
)

YELLOW_FEVER_PRODUCT_FRACTIONAL_2018 = (
    "yellow_fever_fractional_2018"
)

YELLOW_FEVER_SUPPORTED_PRODUCTS = frozenset(
    {
        YELLOW_FEVER_PRODUCT_STANDARD,
        YELLOW_FEVER_PRODUCT_FRACTIONAL_2018,
    }
)

YELLOW_FEVER_INTERNAL_INTERVAL_DAYS = 30


def _yellow_fever_plain_mapping(
    value,
    *,
    field_name,
):
    if hasattr(
        value,
        "model_dump",
    ):
        value = value.model_dump()

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"{field_name} must be a mapping or model"
        )

    return dict(
        value
    )


def _yellow_fever_add_months_clamped(
    value,
    months,
):
    import calendar
    from datetime import date as _date

    month_index = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + month_index // 12
    )

    month = (
        month_index % 12
        + 1
    )

    day = min(
        value.day,
        calendar.monthrange(
            year,
            month,
        )[1],
    )

    return _date(
        year,
        month,
        day,
    )


def normalize_yellow_fever_history(
    *,
    assessment_date,
    date_of_birth,
    history,
    history_scope,
    registration_role_events=None,
):
    """
    Normalize product- and age-sensitive yellow-fever history.

    This function distinguishes standard-dose evidence, exceptional
    6-8 month dose-zero evidence and documented 2018 fractional-dose
    evidence. It does not assign a current due decision.
    """

    from datetime import date as _date

    if not isinstance(
        assessment_date,
        _date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        _date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if history_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "invalid yellow-fever history_scope"
        )

    lifetime = _yellow_fever_plain_mapping(
        history,
        field_name="history",
    )

    if (
        lifetime.get(
            "vaccine_key"
        )
        != "yellow_fever"
    ):
        raise ValueError(
            "yellow-fever history must use "
            "vaccine_key yellow_fever"
        )

    lifetime_history_state = lifetime.get(
        "history_state"
    )

    if lifetime_history_state not in {
        "documented_zero_dose",
        "documented_doses",
        "unknown",
        "partial_record",
    }:
        raise ValueError(
            "invalid yellow-fever lifetime history_state"
        )

    raw_doses = list(
        lifetime.get(
            "doses"
        )
        or []
    )

    reported_undated = int(
        lifetime.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if reported_undated < 0:
        raise ValueError(
            "reported undated yellow-fever dose count "
            "cannot be negative"
        )

    if (
        lifetime_history_state
        == "documented_zero_dose"
        and (
            raw_doses
            or reported_undated
        )
    ):
        raise ValueError(
            "documented zero yellow-fever history "
            "cannot contain dose evidence"
        )

    if (
        lifetime_history_state
        == "documented_doses"
        and not raw_doses
    ):
        raise ValueError(
            "documented yellow-fever doses require "
            "at least one dated dose"
        )

    age_6m = _yellow_fever_add_months_clamped(
        date_of_birth,
        6,
    )

    age_9m = _yellow_fever_add_months_clamped(
        date_of_birth,
        9,
    )

    age_4y = _yellow_fever_add_months_clamped(
        date_of_birth,
        48,
    )

    age_5y = _yellow_fever_add_months_clamped(
        date_of_birth,
        60,
    )

    age_60y = _yellow_fever_add_months_clamped(
        date_of_birth,
        720,
    )

    registration_role_events = list(
        registration_role_events
        or []
    )

    registration_roles_by_date = {}

    for index, raw_role in enumerate(
        registration_role_events
    ):
        item = _yellow_fever_plain_mapping(
            raw_role,
            field_name=(
                f"registration_role_events[{index}]"
            ),
        )

        event_date = item.get(
            "administration_date"
        )

        source_role = item.get(
            "source_registration_role"
        )

        if not isinstance(
            event_date,
            _date,
        ):
            raise ValueError(
                "yellow-fever registration metadata "
                "administration_date must be a date"
            )

        if (
            not isinstance(
                source_role,
                str,
            )
            or not source_role.strip()
        ):
            raise ValueError(
                "yellow-fever source_registration_role "
                "must be a non-empty string"
            )

        if (
            event_date
            in registration_roles_by_date
        ):
            raise ValueError(
                "duplicate yellow-fever registration metadata date"
            )

        registration_roles_by_date[
            event_date
        ] = source_role.strip()

    lifetime_events = []
    date_counts = {}
    unsupported_product_keys = set()

    for index, raw_dose in enumerate(
        raw_doses
    ):
        dose = _yellow_fever_plain_mapping(
            raw_dose,
            field_name=(
                f"history.doses[{index}]"
            ),
        )

        administration_date = dose.get(
            "administration_date"
        )

        if not isinstance(
            administration_date,
            _date,
        ):
            raise ValueError(
                "yellow-fever administration_date must be a date"
            )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "yellow-fever administration_date "
                "cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "yellow-fever administration_date "
                "cannot follow assessment_date"
            )

        product_key = dose.get(
            "product_key"
        )

        if (
            administration_date
            < age_6m
        ):
            age_scope = (
                "before_vfa_minimum_age"
            )

        elif (
            administration_date
            < age_9m
        ):
            age_scope = (
                "exceptional_dose_zero_age"
            )

        elif (
            administration_date
            < age_5y
        ):
            age_scope = (
                "standard_under5_age"
            )

        elif (
            administration_date
            < age_60y
        ):
            age_scope = (
                "standard_age5_to59"
            )

        else:
            age_scope = (
                "age60plus_exception_layer"
            )

        if (
            product_key
            == YELLOW_FEVER_PRODUCT_STANDARD
        ):
            if (
                administration_date
                < age_6m
            ):
                clinical_role = (
                    "before_vfa_minimum_age"
                )

            elif (
                administration_date
                < age_9m
            ):
                clinical_role = (
                    "exceptional_dose_zero"
                )

            elif (
                administration_date
                < age_5y
            ):
                clinical_role = (
                    "standard_series_dose_before5"
                )

            elif (
                administration_date
                < age_60y
            ):
                clinical_role = (
                    "standard_series_dose_age5_to59"
                )

            else:
                clinical_role = (
                    "standard_dose_age60plus_exception_layer"
                )

        elif (
            product_key
            == YELLOW_FEVER_PRODUCT_FRACTIONAL_2018
        ):
            if (
                administration_date.year
                != 2018
            ):
                raise ValueError(
                    "yellow_fever_fractional_2018 "
                    "must have a 2018 administration date"
                )

            clinical_role = (
                "fractional_2018_nonstandard"
            )

        else:
            unsupported_product_keys.add(
                (
                    product_key
                    if isinstance(
                        product_key,
                        str,
                    )
                    else "<missing>"
                )
            )

            clinical_role = (
                "unsupported_product"
            )

        lifetime_events.append(
            {
                "administration_date":
                    administration_date,

                "product_key":
                    product_key,

                "documentation_source":
                    dose.get(
                        "documentation_source"
                    ),

                "source_registration_role":
                    registration_roles_by_date.get(
                        administration_date
                    ),

                "clinical_role":
                    clinical_role,

                "age_scope_at_exposure":
                    age_scope,

                "standard_series_ordinal":
                    None,

                "fractional_regularization_event":
                    False,
            }
        )

        date_counts[
            administration_date
        ] = (
            date_counts.get(
                administration_date,
                0,
            )
            + 1
        )

    ambiguous_dates = sorted(
        event_date
        for event_date, count
        in date_counts.items()
        if count > 1
    )

    if ambiguous_dates:
        raise ValueError(
            "same-day yellow-fever lifetime event ambiguity"
        )

    lifetime_dates = {
        event[
            "administration_date"
        ]
        for event in lifetime_events
    }

    unreconciled_registration_dates = sorted(
        event_date
        for event_date
        in registration_roles_by_date
        if event_date not in lifetime_dates
    )

    if unreconciled_registration_dates:
        raise ValueError(
            "yellow-fever registration metadata must reconcile "
            "to a dated lifetime event"
        )

    lifetime_events.sort(
        key=lambda event: event[
            "administration_date"
        ]
    )

    for ordinal, event in enumerate(
        lifetime_events,
        1,
    ):
        event[
            "lifetime_chronology_ordinal"
        ] = ordinal

    routine_standard_roles = {
        "standard_series_dose_before5",
        "standard_series_dose_age5_to59",
        "standard_dose_age60plus_exception_layer",
    }

    standard_series_events = [
        event
        for event in lifetime_events
        if event[
            "clinical_role"
        ]
        in routine_standard_roles
    ]

    for ordinal, event in enumerate(
        standard_series_events,
        1,
    ):
        event[
            "standard_series_ordinal"
        ] = ordinal

    dose_zero_events = [
        event
        for event in lifetime_events
        if (
            event[
                "clinical_role"
            ]
            == "exceptional_dose_zero"
        )
    ]

    fractional_events = [
        event
        for event in lifetime_events
        if (
            event[
                "clinical_role"
            ]
            == "fractional_2018_nonstandard"
        )
    ]

    latest_fractional_date = (
        max(
            (
                event[
                    "administration_date"
                ]
                for event in fractional_events
            ),
            default=None,
        )
    )

    standard_before_latest_fractional_events = []
    standards_after_latest_fractional = []

    if (
        latest_fractional_date
        is not None
    ):
        standard_before_latest_fractional_events = [
            event
            for event in standard_series_events
            if (
                event[
                    "administration_date"
                ]
                < latest_fractional_date
            )
        ]

        standards_after_latest_fractional = [
            event
            for event in standard_series_events
            if (
                event[
                    "administration_date"
                ]
                > latest_fractional_date
            )
        ]

        if standards_after_latest_fractional:
            standards_after_latest_fractional[
                0
            ][
                "fractional_regularization_event"
            ] = True

    fractional_regularization_required = (
        bool(
            fractional_events
        )
        and not standards_after_latest_fractional
    )

    interval_checks = []

    previous_interval_event = None

    interval_source_roles = {
        "exceptional_dose_zero",
        "standard_series_dose_before5",
        "standard_series_dose_age5_to59",
        "standard_dose_age60plus_exception_layer",
    }

    interval_target_roles = {
        "standard_series_dose_before5",
        "standard_series_dose_age5_to59",
        "standard_dose_age60plus_exception_layer",
    }

    for event in lifetime_events:
        role = event[
            "clinical_role"
        ]

        if (
            role
            in interval_target_roles
            and previous_interval_event
            is not None
        ):
            actual_days = (
                event[
                    "administration_date"
                ]
                - previous_interval_event[
                    "administration_date"
                ]
            ).days

            from_role = (
                previous_interval_event[
                    "clinical_role"
                ]
            )

            interval_type = (
                "dose_zero_to_standard"
                if (
                    from_role
                    == "exceptional_dose_zero"
                )
                else "standard_to_standard"
            )

            interval_checks.append(
                {
                    "from_event_date":
                        previous_interval_event[
                            "administration_date"
                        ],

                    "to_event_date":
                        event[
                            "administration_date"
                        ],

                    "from_clinical_role":
                        from_role,

                    "to_clinical_role":
                        role,

                    "interval_type":
                        interval_type,

                    "actual_days":
                        actual_days,

                    "required_minimum_days":
                        YELLOW_FEVER_INTERNAL_INTERVAL_DAYS,

                    "valid":
                        (
                            actual_days
                            >= YELLOW_FEVER_INTERNAL_INTERVAL_DAYS
                        ),
                }
            )

        if (
            role
            in interval_source_roles
        ):
            previous_interval_event = event

    intervals_valid = all(
        check[
            "valid"
        ]
        for check in interval_checks
    )

    standard_before5_events = [
        event
        for event in standard_series_events
        if (
            event[
                "clinical_role"
            ]
            == "standard_series_dose_before5"
        )
    ]

    standard_at_or_after5_events = [
        event
        for event in standard_series_events
        if event[
            "clinical_role"
        ]
        in {
            "standard_series_dose_age5_to59",
            "standard_dose_age60plus_exception_layer",
        }
    ]

    age60plus_standard_events = [
        event
        for event in standard_series_events
        if (
            event[
                "clinical_role"
            ]
            == "standard_dose_age60plus_exception_layer"
        )
    ]

    before_6m_events = [
        event
        for event in lifetime_events
        if (
            event[
                "age_scope_at_exposure"
            ]
            == "before_vfa_minimum_age"
        )
    ]

    source_history_incomplete = (
        history_scope
        != "complete"
        or lifetime_history_state
        in {
            "unknown",
            "partial_record",
        }
        or reported_undated > 0
    )

    chronology_ambiguous = False

    fractional_regularization_third_standard_allowed = (
        bool(
            fractional_events
        )
        and len(
            standard_series_events
        )
        == 3
        and len(
            standard_before_latest_fractional_events
        )
        == 2
        and len(
            standards_after_latest_fractional
        )
        == 1
    )

    excessive_standard_dose_evidence = (
        len(
            standard_series_events
        )
        > 2
        and not fractional_regularization_third_standard_allowed
    )

    excessive_dose_zero_evidence = (
        len(
            dose_zero_events
        )
        > 1
    )

    safe_for_routine_evaluation = (
        not source_history_incomplete
        and not chronology_ambiguous
        and not unsupported_product_keys
        and intervals_valid
        and not before_6m_events
        and not excessive_standard_dose_evidence
        and not excessive_dose_zero_evidence
    )

    return {
        "target_family":
            "yellow_fever_routine_history",

        "history_scope":
            history_scope,

        "lifetime_history_state":
            lifetime_history_state,

        "age_6m_date":
            age_6m,

        "age_9m_date":
            age_9m,

        "age_4y_date":
            age_4y,

        "age_5y_date":
            age_5y,

        "age_60y_date":
            age_60y,

        "events":
            lifetime_events,

        "lifetime_event_count":
            len(
                lifetime_events
            ),

        "dose_zero_count":
            len(
                dose_zero_events
            ),

        "standard_dose_count":
            len(
                standard_series_events
            ),

        "standard_dose_before5_count":
            len(
                standard_before5_events
            ),

        "standard_dose_at_or_after5_count":
            len(
                standard_at_or_after5_events
            ),

        "standard_dose_age60plus_count":
            len(
                age60plus_standard_events
            ),

        "fractional_2018_count":
            len(
                fractional_events
            ),

        "latest_fractional_2018_date":
            latest_fractional_date,

        "standard_before_latest_fractional_count":
            len(
                standard_before_latest_fractional_events
            ),

        "standard_after_latest_fractional_count":
            len(
                standards_after_latest_fractional
            ),

        "fractional_regularization_required":
            fractional_regularization_required,

        "fractional_regularization_third_standard_allowed":
            fractional_regularization_third_standard_allowed,

        "internal_interval_checks":
            interval_checks,

        "intervals_valid":
            intervals_valid,

        "before_6m_event_count":
            len(
                before_6m_events
            ),

        "reported_undated_event_count":
            reported_undated,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "chronology_ambiguous":
            chronology_ambiguous,

        "excessive_standard_dose_evidence":
            excessive_standard_dose_evidence,

        "excessive_dose_zero_evidence":
            excessive_dose_zero_evidence,

        "safe_for_routine_evaluation":
            safe_for_routine_evaluation,

        "registration_role_metadata_present":
            bool(
                registration_roles_by_date
            ),

        "registration_role_defines_clinical_role":
            False,

        "clinical_role_derived_from_product_age_chronology":
            True,

        "normalizer_assigns_due_decision":
            False,

        "epidemiologic_context_inferred":
            False,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }
MMR_PRODUCT_SCR = (
    "mmr_scr"
)

MMR_PRODUCT_SCRV = (
    "mmrv_scrv"
)

MMR_SUPPORTED_PRODUCTS = frozenset(
    {
        MMR_PRODUCT_SCR,
        MMR_PRODUCT_SCRV,
    }
)

MMR_GENERAL_ORDINARY_INTERVAL_DAYS = 30
MMR_GENERAL_EXCEPTIONAL_MINIMUM_DAYS = 15
MMR_HEALTH_WORKER_MINIMUM_INTERVAL_DAYS = 30
MMR_D0_TO_ROUTINE_MINIMUM_INTERVAL_DAYS = 30

MMR_GENERAL_INTERVAL_EXCEPTION_AUTHORIZATION_KEY = (
    "source_authorized_general_15_day_exception"
)


def _mmr_plain_mapping(
    value,
    *,
    field_name,
):
    if hasattr(
        value,
        "model_dump",
    ):
        value = value.model_dump()

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"{field_name} must be a mapping or model"
        )

    return dict(
        value
    )


def _mmr_add_months_clamped(
    value,
    months,
):
    import calendar
    from datetime import date as _date

    month_index = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + month_index // 12
    )

    month = (
        month_index % 12
        + 1
    )

    day = min(
        value.day,
        calendar.monthrange(
            year,
            month,
        )[1],
    )

    return _date(
        year,
        month,
        day,
    )


def _mmr_count_valid_series_events(
    events,
    *,
    exception_pairs,
    occupational,
):
    accepted = []

    for event in events:
        if not accepted:
            accepted.append(
                event
            )

            continue

        previous = accepted[
            -1
        ]

        actual_days = (
            event[
                "administration_date"
            ]
            - previous[
                "administration_date"
            ]
        ).days

        if (
            actual_days
            >= MMR_GENERAL_ORDINARY_INTERVAL_DAYS
        ):
            accepted.append(
                event
            )

            continue

        if occupational:
            continue

        pair = (
            previous[
                "administration_date"
            ],
            event[
                "administration_date"
            ],
        )

        if (
            actual_days
            >= MMR_GENERAL_EXCEPTIONAL_MINIMUM_DAYS
            and pair
            in exception_pairs
        ):
            accepted.append(
                event
            )

    return accepted


def normalize_mmr_history(
    *,
    assessment_date,
    date_of_birth,
    history,
    history_scope,
    registration_role_events=None,
    historical_interval_exception_events=None,
):
    """
    Normalize product/component-sensitive SCR/MMR history.

    The normalizer distinguishes D0 from routine MMR-component
    doses, preserves MMRV/SCRV as one physical combination-vaccine
    event, and derives separate general-population versus
    occupational series counts.

    It does not assign a current vaccination decision.
    """

    from datetime import date as _date

    if not isinstance(
        assessment_date,
        _date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        _date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if history_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "invalid MMR history_scope"
        )

    lifetime = _mmr_plain_mapping(
        history,
        field_name="history",
    )

    if (
        lifetime.get(
            "vaccine_key"
        )
        != "mmr"
    ):
        raise ValueError(
            "MMR history must use vaccine_key mmr"
        )

    lifetime_history_state = lifetime.get(
        "history_state"
    )

    if lifetime_history_state not in {
        "documented_zero_dose",
        "documented_doses",
        "unknown",
        "partial_record",
    }:
        raise ValueError(
            "invalid MMR lifetime history_state"
        )

    raw_doses = list(
        lifetime.get(
            "doses"
        )
        or []
    )

    reported_undated = int(
        lifetime.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if reported_undated < 0:
        raise ValueError(
            "reported undated MMR dose count cannot be negative"
        )

    if (
        lifetime_history_state
        == "documented_zero_dose"
        and (
            raw_doses
            or reported_undated
        )
    ):
        raise ValueError(
            "documented zero MMR history cannot contain dose evidence"
        )

    if (
        lifetime_history_state
        == "documented_doses"
        and not raw_doses
    ):
        raise ValueError(
            "documented MMR doses require at least one dated dose"
        )

    age_6m = _mmr_add_months_clamped(
        date_of_birth,
        6,
    )

    age_12m = _mmr_add_months_clamped(
        date_of_birth,
        12,
    )

    age_15m = _mmr_add_months_clamped(
        date_of_birth,
        15,
    )

    age_30y = _mmr_add_months_clamped(
        date_of_birth,
        360,
    )

    age_60y = _mmr_add_months_clamped(
        date_of_birth,
        720,
    )

    registration_role_events = list(
        registration_role_events
        or []
    )

    registration_roles_by_date = {}

    for index, raw_role in enumerate(
        registration_role_events
    ):
        item = _mmr_plain_mapping(
            raw_role,
            field_name=(
                f"registration_role_events[{index}]"
            ),
        )

        event_date = item.get(
            "administration_date"
        )

        source_role = item.get(
            "source_registration_role"
        )

        if not isinstance(
            event_date,
            _date,
        ):
            raise ValueError(
                "MMR registration metadata "
                "administration_date must be a date"
            )

        if (
            not isinstance(
                source_role,
                str,
            )
            or not source_role.strip()
        ):
            raise ValueError(
                "MMR source_registration_role "
                "must be a non-empty string"
            )

        if (
            event_date
            in registration_roles_by_date
        ):
            raise ValueError(
                "duplicate MMR registration metadata date"
            )

        registration_roles_by_date[
            event_date
        ] = source_role.strip()

    exception_events = list(
        historical_interval_exception_events
        or []
    )

    exception_pairs = set()

    for index, raw_exception in enumerate(
        exception_events
    ):
        item = _mmr_plain_mapping(
            raw_exception,
            field_name=(
                "historical_interval_exception_events"
                f"[{index}]"
            ),
        )

        from_date = item.get(
            "from_administration_date"
        )

        to_date = item.get(
            "to_administration_date"
        )

        authorization_key = item.get(
            "authorization_key"
        )

        if (
            not isinstance(
                from_date,
                _date,
            )
            or not isinstance(
                to_date,
                _date,
            )
        ):
            raise ValueError(
                "MMR interval-exception dates must be dates"
            )

        if (
            to_date
            <= from_date
        ):
            raise ValueError(
                "MMR interval-exception dates must be chronological"
            )

        if (
            authorization_key
            != MMR_GENERAL_INTERVAL_EXCEPTION_AUTHORIZATION_KEY
        ):
            raise ValueError(
                "unsupported MMR historical interval "
                "exception authorization_key"
            )

        pair = (
            from_date,
            to_date,
        )

        if pair in exception_pairs:
            raise ValueError(
                "duplicate MMR historical interval exception pair"
            )

        exception_pairs.add(
            pair
        )

    lifetime_events = []
    date_counts = {}
    unsupported_product_keys = set()
    unsupported_age_product_event_count = 0

    for index, raw_dose in enumerate(
        raw_doses
    ):
        dose = _mmr_plain_mapping(
            raw_dose,
            field_name=(
                f"history.doses[{index}]"
            ),
        )

        administration_date = dose.get(
            "administration_date"
        )

        if not isinstance(
            administration_date,
            _date,
        ):
            raise ValueError(
                "MMR administration_date must be a date"
            )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "MMR administration_date cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "MMR administration_date cannot follow assessment_date"
            )

        product_key = dose.get(
            "product_key"
        )

        contains_measles = False
        contains_mumps = False
        contains_rubella = False
        contains_varicella = False

        if (
            product_key
            == MMR_PRODUCT_SCR
        ):
            contains_measles = True
            contains_mumps = True
            contains_rubella = True

        elif (
            product_key
            == MMR_PRODUCT_SCRV
        ):
            contains_measles = True
            contains_mumps = True
            contains_rubella = True
            contains_varicella = True

        else:
            unsupported_product_keys.add(
                (
                    product_key
                    if isinstance(
                        product_key,
                        str,
                    )
                    else "<missing>"
                )
            )

        if (
            administration_date
            < age_6m
        ):
            age_scope = (
                "before_scr_minimum_history_age"
            )

        elif (
            administration_date
            < age_12m
        ):
            age_scope = (
                "dose_zero_age"
            )

        elif (
            administration_date
            < age_30y
        ):
            age_scope = (
                "routine_age_12m_to29"
            )

        elif (
            administration_date
            < age_60y
        ):
            age_scope = (
                "routine_age_30_to59"
            )

        else:
            age_scope = (
                "age60plus"
            )

        if (
            product_key
            not in MMR_SUPPORTED_PRODUCTS
        ):
            clinical_role = (
                "unsupported_product"
            )

        elif (
            administration_date
            < age_6m
        ):
            clinical_role = (
                "before_scr_minimum_history_age"
            )

        elif (
            administration_date
            < age_12m
        ):
            if (
                product_key
                == MMR_PRODUCT_SCR
            ):
                clinical_role = (
                    "dose_zero_history"
                )

            else:
                clinical_role = (
                    "unsupported_pre12_mmrv"
                )

                unsupported_age_product_event_count += 1

        elif (
            administration_date
            < age_30y
        ):
            clinical_role = (
                "routine_component_dose_under30"
            )

        elif (
            administration_date
            < age_60y
        ):
            clinical_role = (
                "routine_component_dose_age30_to59"
            )

        else:
            clinical_role = (
                "age60plus_component_evidence"
            )

        lifetime_events.append(
            {
                "administration_date":
                    administration_date,

                "product_key":
                    product_key,

                "documentation_source":
                    dose.get(
                        "documentation_source"
                    ),

                "source_registration_role":
                    registration_roles_by_date.get(
                        administration_date
                    ),

                "clinical_role":
                    clinical_role,

                "age_scope_at_exposure":
                    age_scope,

                "lifetime_chronology_ordinal":
                    None,

                "routine_component_ordinal":
                    None,

                "contains_measles":
                    contains_measles,

                "contains_mumps":
                    contains_mumps,

                "contains_rubella":
                    contains_rubella,

                "contains_varicella":
                    contains_varicella,

                "general_series_counted":
                    False,

                "occupational_series_counted":
                    False,
            }
        )

        date_counts[
            administration_date
        ] = (
            date_counts.get(
                administration_date,
                0,
            )
            + 1
        )

    ambiguous_dates = sorted(
        event_date
        for event_date, count
        in date_counts.items()
        if count > 1
    )

    if ambiguous_dates:
        raise ValueError(
            "same-day MMR lifetime event ambiguity"
        )

    lifetime_dates = {
        event[
            "administration_date"
        ]
        for event
        in lifetime_events
    }

    unreconciled_registration_dates = sorted(
        event_date
        for event_date
        in registration_roles_by_date
        if event_date not in lifetime_dates
    )

    if unreconciled_registration_dates:
        raise ValueError(
            "MMR registration metadata must reconcile "
            "to a dated lifetime event"
        )

    lifetime_events.sort(
        key=lambda event: event[
            "administration_date"
        ]
    )

    for ordinal, event in enumerate(
        lifetime_events,
        1,
    ):
        event[
            "lifetime_chronology_ordinal"
        ] = ordinal

    routine_roles = {
        "routine_component_dose_under30",
        "routine_component_dose_age30_to59",
        "age60plus_component_evidence",
    }

    routine_events = [
        event
        for event in lifetime_events
        if (
            event[
                "clinical_role"
            ]
            in routine_roles
        )
    ]

    for ordinal, event in enumerate(
        routine_events,
        1,
    ):
        event[
            "routine_component_ordinal"
        ] = ordinal

    routine_event_dates = {
        event[
            "administration_date"
        ]
        for event
        in routine_events
    }

    unreconciled_exception_pairs = sorted(
        pair
        for pair in exception_pairs
        if (
            pair[
                0
            ]
            not in routine_event_dates
            or pair[
                1
            ]
            not in routine_event_dates
        )
    )

    if unreconciled_exception_pairs:
        raise ValueError(
            "MMR historical interval exception pair must reconcile "
            "to dated routine-component events"
        )

    dose_zero_events = [
        event
        for event in lifetime_events
        if (
            event[
                "clinical_role"
            ]
            == "dose_zero_history"
        )
    ]

    before_6m_events = [
        event
        for event in lifetime_events
        if (
            event[
                "clinical_role"
            ]
            == "before_scr_minimum_history_age"
        )
    ]

    interval_checks = []

    for previous, current in zip(
        routine_events,
        routine_events[
            1:
        ],
    ):
        from_date = previous[
            "administration_date"
        ]

        to_date = current[
            "administration_date"
        ]

        actual_days = (
            to_date
            - from_date
        ).days

        pair = (
            from_date,
            to_date,
        )

        exception_documented = (
            pair
            in exception_pairs
        )

        ordinary_valid = (
            actual_days
            >= MMR_GENERAL_ORDINARY_INTERVAL_DAYS
        )

        below_absolute_minimum = (
            actual_days
            < MMR_GENERAL_EXCEPTIONAL_MINIMUM_DAYS
        )

        requires_exception_evidence = (
            MMR_GENERAL_EXCEPTIONAL_MINIMUM_DAYS
            <= actual_days
            < MMR_GENERAL_ORDINARY_INTERVAL_DAYS
            and not exception_documented
        )

        general_series_interval_valid = (
            ordinary_valid
            or (
                MMR_GENERAL_EXCEPTIONAL_MINIMUM_DAYS
                <= actual_days
                < MMR_GENERAL_ORDINARY_INTERVAL_DAYS
                and exception_documented
            )
        )

        health_worker_interval_valid = (
            actual_days
            >= MMR_HEALTH_WORKER_MINIMUM_INTERVAL_DAYS
        )

        interval_checks.append(
            {
                "from_event_date":
                    from_date,

                "to_event_date":
                    to_date,

                "actual_days":
                    actual_days,

                "ordinary_30d_valid":
                    ordinary_valid,

                "general_15d_exception_documented":
                    exception_documented,

                "general_series_interval_valid":
                    general_series_interval_valid,

                "health_worker_interval_valid":
                    health_worker_interval_valid,

                "requires_exception_evidence":
                    requires_exception_evidence,

                "below_absolute_15d_minimum":
                    below_absolute_minimum,
            }
        )

    d0_to_routine_interval_checks = []

    if (
        dose_zero_events
        and routine_events
    ):
        latest_d0 = dose_zero_events[
            -1
        ]

        first_routine = routine_events[
            0
        ]

        actual_days = (
            first_routine[
                "administration_date"
            ]
            - latest_d0[
                "administration_date"
            ]
        ).days

        d0_to_routine_interval_checks.append(
            {
                "from_event_date":
                    latest_d0[
                        "administration_date"
                    ],

                "to_event_date":
                    first_routine[
                        "administration_date"
                    ],

                "actual_days":
                    actual_days,

                "required_minimum_days":
                    MMR_D0_TO_ROUTINE_MINIMUM_INTERVAL_DAYS,

                "valid":
                    (
                        actual_days
                        >= MMR_D0_TO_ROUTINE_MINIMUM_INTERVAL_DAYS
                    ),
            }
        )

    unresolved_short_interval_evidence = any(
        check[
            "requires_exception_evidence"
        ]
        for check
        in interval_checks
    )

    below_absolute_minimum_interval = any(
        check[
            "below_absolute_15d_minimum"
        ]
        for check
        in interval_checks
    )

    d0_to_routine_intervals_valid = all(
        check[
            "valid"
        ]
        for check
        in d0_to_routine_interval_checks
    )

    general_series_events = (
        _mmr_count_valid_series_events(
            routine_events,
            exception_pairs=exception_pairs,
            occupational=False,
        )
    )

    occupational_series_events = (
        _mmr_count_valid_series_events(
            routine_events,
            exception_pairs=exception_pairs,
            occupational=True,
        )
    )

    general_counted_dates = {
        event[
            "administration_date"
        ]
        for event
        in general_series_events
    }

    occupational_counted_dates = {
        event[
            "administration_date"
        ]
        for event
        in occupational_series_events
    }

    for event in routine_events:
        event[
            "general_series_counted"
        ] = (
            event[
                "administration_date"
            ]
            in general_counted_dates
        )

        event[
            "occupational_series_counted"
        ] = (
            event[
                "administration_date"
            ]
            in occupational_counted_dates
        )

    source_history_incomplete = (
        history_scope
        != "complete"
        or lifetime_history_state
        in {
            "unknown",
            "partial_record",
        }
        or reported_undated > 0
    )

    chronology_ambiguous = False

    intervals_safe_for_general_series = (
        not unresolved_short_interval_evidence
        and not below_absolute_minimum_interval
        and d0_to_routine_intervals_valid
    )

    # "safe" means the occupational count is deterministically
    # interpretable. A source-authorized 15-29d general interval
    # remains occupationally non-counting, but does not make the
    # history itself ambiguous because the 30d occupational
    # subsequence is still derived explicitly.
    intervals_safe_for_health_worker_series = (
        not unresolved_short_interval_evidence
        and not below_absolute_minimum_interval
        and d0_to_routine_intervals_valid
    )

    safe_for_routine_evaluation = (
        not source_history_incomplete
        and not chronology_ambiguous
        and not unsupported_product_keys
        and unsupported_age_product_event_count == 0
        and not before_6m_events
        and intervals_safe_for_general_series
        and intervals_safe_for_health_worker_series
    )

    return {
        "target_family":
            "mmr_routine_history",

        "history_scope":
            history_scope,

        "lifetime_history_state":
            lifetime_history_state,

        "age_6m_date":
            age_6m,

        "age_12m_date":
            age_12m,

        "age_15m_date":
            age_15m,

        "age_30y_date":
            age_30y,

        "age_60y_date":
            age_60y,

        "events":
            lifetime_events,

        "lifetime_event_count":
            len(
                lifetime_events
            ),

        "dose_zero_count":
            len(
                dose_zero_events
            ),

        "routine_component_event_count":
            len(
                routine_events
            ),

        "mmr_scr_routine_event_count":
            sum(
                1
                for event
                in routine_events
                if (
                    event[
                        "product_key"
                    ]
                    == MMR_PRODUCT_SCR
                )
            ),

        "mmrv_scrv_routine_event_count":
            sum(
                1
                for event
                in routine_events
                if (
                    event[
                        "product_key"
                    ]
                    == MMR_PRODUCT_SCRV
                )
            ),

        "general_valid_component_dose_count":
            len(
                general_series_events
            ),

        "occupational_valid_component_dose_count":
            len(
                occupational_series_events
            ),

        "interval_checks":
            interval_checks,

        "d0_to_routine_interval_checks":
            d0_to_routine_interval_checks,

        "historical_interval_exception_pair_count":
            len(
                exception_pairs
            ),

        "unresolved_short_interval_evidence":
            unresolved_short_interval_evidence,

        "below_absolute_minimum_interval":
            below_absolute_minimum_interval,

        "intervals_safe_for_general_series":
            intervals_safe_for_general_series,

        "intervals_safe_for_health_worker_series":
            intervals_safe_for_health_worker_series,

        "before_6m_event_count":
            len(
                before_6m_events
            ),

        "unsupported_age_product_event_count":
            unsupported_age_product_event_count,

        "reported_undated_event_count":
            reported_undated,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "chronology_ambiguous":
            chronology_ambiguous,

        "safe_for_routine_evaluation":
            safe_for_routine_evaluation,

        "registration_role_metadata_present":
            bool(
                registration_roles_by_date
            ),

        "registration_role_defines_clinical_role":
            False,

        "clinical_role_derived_from_product_age_chronology":
            True,

        "normalizer_assigns_due_decision":
            False,

        "occupation_inferred":
            False,

        "pregnancy_inferred":
            False,

        "epidemiologic_context_inferred":
            False,

        "special_condition_inferred":
            False,

        "synthetic_score_applied":
            False,
    }
DTP_HISTORY_MODEL_ID = (
    "PNI26-DTP-CHILD-HISTORY-001"
)

DTP_HISTORY_PENTAVALENT_KEY = (
    "pentavalent"
)

DTP_HISTORY_DTP_KEY = (
    "dtp"
)


def _dtp_add_months_clamped(
    value,
    months,
):
    from calendar import monthrange

    zero_based = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + zero_based // 12
    )

    month = (
        zero_based % 12
        + 1
    )

    day = min(
        value.day,
        monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def _dtp_age_boundary(
    date_of_birth,
    *,
    months,
    days=0,
):
    from datetime import timedelta

    return (
        _dtp_add_months_clamped(
            date_of_birth,
            months,
        )
        + timedelta(
            days=days,
        )
    )


def _dtp_history_payload(
    value,
    *,
    expected_vaccine_key,
    assessment_date,
    date_of_birth,
):
    if value is None:
        raise ValueError(
            f"{expected_vaccine_key} history is required"
        )

    if hasattr(
        value,
        "model_dump",
    ):
        payload = value.model_dump(
            mode="python"
        )

    elif isinstance(
        value,
        dict,
    ):
        payload = dict(
            value
        )

    else:
        raise ValueError(
            f"{expected_vaccine_key} history must be "
            "PniVaccineHistory-compatible"
        )

    if (
        payload.get(
            "vaccine_key"
        )
        != expected_vaccine_key
    ):
        raise ValueError(
            "expected vaccine_key "
            f"{expected_vaccine_key}"
        )

    state = payload.get(
        "history_state"
    )

    undated = int(
        payload.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if undated < 0:
        raise ValueError(
            "reported_prior_doses_without_exact_dates "
            "cannot be negative"
        )

    events = []

    for raw_dose in (
        payload.get(
            "doses"
        )
        or []
    ):
        if hasattr(
            raw_dose,
            "model_dump",
        ):
            dose = raw_dose.model_dump(
                mode="python"
            )

        elif isinstance(
            raw_dose,
            dict,
        ):
            dose = dict(
                raw_dose
            )

        else:
            raise ValueError(
                "dose must be PniDoseRecord-compatible"
            )

        administration_date = dose.get(
            "administration_date"
        )

        if isinstance(
            administration_date,
            str,
        ):
            administration_date = date.fromisoformat(
                administration_date
            )

        if not isinstance(
            administration_date,
            date,
        ):
            raise ValueError(
                "administration_date must be a date"
            )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                f"{expected_vaccine_key} administration_date "
                "cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                f"{expected_vaccine_key} administration_date "
                "cannot follow assessment_date"
            )

        events.append({
            "vaccine_key":
                expected_vaccine_key,

            "product_key":
                dose.get(
                    "product_key"
                ),

            "administration_date":
                administration_date,

            "documentation_source":
                dose.get(
                    "documentation_source"
                ),

            "clinical_role":
                "unclassified",
        })

    events.sort(
        key=lambda item:
            item[
                "administration_date"
            ]
    )

    return {
        "state":
            state,

        "undated":
            undated,

        "events":
            events,
    }


def normalize_dtp_child_history(
    *,
    assessment_date,
    date_of_birth,
    pentavalent_history,
    dtp_history,
    history_scope,
):
    """
    Normalize routine childhood DTP booster history.

    Ordinary DTP completion is deliberately product/role specific:
    a qualifying 3-dose pentavalent primary series precedes DTP R1/R2.
    Aggregate diphtheria/tetanus/pertussis antigen counts are not used
    as a substitute for this chronology.
    """

    if not isinstance(
        assessment_date,
        date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if history_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "history_scope must be complete, partial, or unknown"
        )

    penta = _dtp_history_payload(
        pentavalent_history,
        expected_vaccine_key=(
            DTP_HISTORY_PENTAVALENT_KEY
        ),
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
    )

    dtp = _dtp_history_payload(
        dtp_history,
        expected_vaccine_key=(
            DTP_HISTORY_DTP_KEY
        ),
        assessment_date=assessment_date,
        date_of_birth=date_of_birth,
    )

    age_1m15d = _dtp_age_boundary(
        date_of_birth,
        months=1,
        days=15,
    )

    age_2m = _dtp_age_boundary(
        date_of_birth,
        months=2,
    )

    age_6m = _dtp_age_boundary(
        date_of_birth,
        months=6,
    )

    age_15m = _dtp_age_boundary(
        date_of_birth,
        months=15,
    )

    age_4y = _dtp_age_boundary(
        date_of_birth,
        months=48,
    )

    age_7y = _dtp_age_boundary(
        date_of_birth,
        months=84,
    )

    invalid_reasons = []
    unsupported_product_keys = set()

    source_history_incomplete = (
        history_scope
        != "complete"
        or penta[
            "state"
        ]
        not in {
            "documented_zero_dose",
            "documented_doses",
        }
        or dtp[
            "state"
        ]
        not in {
            "documented_zero_dose",
            "documented_doses",
        }
        or penta[
            "undated"
        ]
        > 0
        or dtp[
            "undated"
        ]
        > 0
    )

    if source_history_incomplete:
        invalid_reasons.append(
            "source_history_incomplete"
        )

    all_events = (
        penta[
            "events"
        ]
        + dtp[
            "events"
        ]
    )

    all_dates = [
        event[
            "administration_date"
        ]
        for event in all_events
    ]

    chronology_ambiguous = (
        len(
            all_dates
        )
        != len(
            set(
                all_dates
            )
        )
    )

    if chronology_ambiguous:
        invalid_reasons.append(
            "same_day_duplicate_or_conflicting_evidence"
        )

    supported_penta_events = []

    for event in penta[
        "events"
    ]:
        if (
            event[
                "product_key"
            ]
            != DTP_HISTORY_PENTAVALENT_KEY
        ):
            unsupported_product_keys.add(
                event[
                    "product_key"
                ]
                or "<missing>"
            )

            event[
                "clinical_role"
            ] = (
                "unsupported_pentavalent_product_evidence"
            )

            continue

        supported_penta_events.append(
            event
        )

    supported_dtp_events = []

    for event in dtp[
        "events"
    ]:
        if (
            event[
                "product_key"
            ]
            != DTP_HISTORY_DTP_KEY
        ):
            unsupported_product_keys.add(
                event[
                    "product_key"
                ]
                or "<missing>"
            )

            event[
                "clinical_role"
            ] = (
                "unsupported_dtp_product_evidence"
            )

            continue

        supported_dtp_events.append(
            event
        )

    if unsupported_product_keys:
        invalid_reasons.append(
            "unsupported_product_identity"
        )

    excessive_pentavalent_evidence = (
        len(
            supported_penta_events
        )
        > 3
    )

    excessive_dtp_evidence = (
        len(
            supported_dtp_events
        )
        > 2
    )

    if excessive_pentavalent_evidence:
        invalid_reasons.append(
            "more_than_three_pentavalent_events"
        )

    if excessive_dtp_evidence:
        invalid_reasons.append(
            "more_than_two_dtp_events"
        )

    penta_dates = [
        event[
            "administration_date"
        ]
        for event in supported_penta_events
    ]

    pentavalent_interval_checks = []

    unresolved_pentavalent_exception_evidence = False
    pentavalent_history_invalid = False

    if penta_dates:
        first = penta_dates[
            0
        ]

        if first < age_1m15d:
            pentavalent_history_invalid = True

            invalid_reasons.append(
                "pentavalent_d1_before_1m15d"
            )

        elif first < age_2m:
            unresolved_pentavalent_exception_evidence = True

            invalid_reasons.append(
                "pentavalent_early_d1_requires_"
                "historical_exception_evidence"
            )

    for index in range(
        1,
        len(
            penta_dates
        ),
    ):
        previous = penta_dates[
            index
            - 1
        ]

        current = penta_dates[
            index
        ]

        actual_days = (
            current
            - previous
        ).days

        check = {
            "from_administration_date":
                previous,

            "to_administration_date":
                current,

            "actual_days":
                actual_days,

            "routine_recommended_days":
                60,

            "absolute_minimum_days":
                30,

            "historical_exception_evidence_present":
                False,
        }

        if actual_days < 30:
            check[
                "status"
            ] = "below_absolute_minimum"

            pentavalent_history_invalid = True

            invalid_reasons.append(
                "pentavalent_interval_under_30_days"
            )

        elif actual_days < 60:
            check[
                "status"
            ] = (
                "requires_historical_exception_evidence"
            )

            unresolved_pentavalent_exception_evidence = True

            invalid_reasons.append(
                "pentavalent_30_to_59_day_interval_"
                "without_exception_evidence"
            )

        else:
            check[
                "status"
            ] = "routine_interval_valid"

        pentavalent_interval_checks.append(
            check
        )

    if len(
        penta_dates
    ) >= 3:
        d1 = penta_dates[
            0
        ]

        d3 = penta_dates[
            2
        ]

        if (
            d3
            < _dtp_add_months_clamped(
                d1,
                4,
            )
        ):
            pentavalent_history_invalid = True

            invalid_reasons.append(
                "pentavalent_d1_to_d3_under_"
                "4_calendar_months"
            )

        if d3 < age_6m:
            pentavalent_history_invalid = True

            invalid_reasons.append(
                "pentavalent_d3_before_exact_6_months"
            )

    pentavalent_basic_series_complete = (
        len(
            penta_dates
        )
        == 3
        and not excessive_pentavalent_evidence
        and not pentavalent_history_invalid
        and not unresolved_pentavalent_exception_evidence
    )

    qualifying_pentavalent_d3_date = (
        penta_dates[
            2
        ]
        if pentavalent_basic_series_complete
        else None
    )

    for index, event in enumerate(
        supported_penta_events,
        start=1,
    ):
        if index <= 3:
            event[
                "clinical_role"
            ] = (
                "pentavalent_basic_series_candidate_"
                f"d{index}"
            )

        else:
            event[
                "clinical_role"
            ] = (
                "excess_pentavalent_evidence"
            )

    valid_r1 = None
    valid_r2 = None

    dtp_interval_checks = []

    for event in supported_dtp_events:
        event_date = event[
            "administration_date"
        ]

        if event_date >= age_7y:
            event[
                "clinical_role"
            ] = "dtp_age7plus_invalid"

            invalid_reasons.append(
                "dtp_at_or_after_exact_7_years"
            )

            continue

        if not pentavalent_basic_series_complete:
            event[
                "clinical_role"
            ] = (
                "dtp_without_qualifying_penta_series"
            )

            invalid_reasons.append(
                "dtp_before_qualifying_primary_series"
            )

            continue

        if valid_r1 is None:
            minimum_r1 = _dtp_add_months_clamped(
                qualifying_pentavalent_d3_date,
                6,
            )

            check = {
                "interval_type":
                    "pentavalent_d3_to_dtp_r1",

                "from_administration_date":
                    qualifying_pentavalent_d3_date,

                "to_administration_date":
                    event_date,

                "minimum_date":
                    minimum_r1,

                "minimum_calendar_months":
                    6,
            }

            if event_date < age_15m:
                event[
                    "clinical_role"
                ] = "dtp_r1_before_exact_15m"

                check[
                    "valid"
                ] = False

                check[
                    "reason"
                ] = "before_exact_15m"

                invalid_reasons.append(
                    "dtp_r1_before_exact_15_months"
                )

            elif event_date < minimum_r1:
                event[
                    "clinical_role"
                ] = "dtp_r1_interval_too_short"

                check[
                    "valid"
                ] = False

                check[
                    "reason"
                ] = "d3_to_r1_under_6_calendar_months"

                invalid_reasons.append(
                    "d3_to_r1_under_6_calendar_months"
                )

            else:
                valid_r1 = event_date

                event[
                    "clinical_role"
                ] = "dtp_r1"

                check[
                    "valid"
                ] = True

                check[
                    "reason"
                ] = "valid_r1"

            dtp_interval_checks.append(
                check
            )

            continue

        if valid_r2 is None:
            minimum_r2 = _dtp_add_months_clamped(
                valid_r1,
                6,
            )

            check = {
                "interval_type":
                    "dtp_r1_to_dtp_r2",

                "from_administration_date":
                    valid_r1,

                "to_administration_date":
                    event_date,

                "minimum_date":
                    minimum_r2,

                "minimum_calendar_months":
                    6,
            }

            if event_date < age_4y:
                event[
                    "clinical_role"
                ] = "dtp_r2_before_exact_4y"

                check[
                    "valid"
                ] = False

                check[
                    "reason"
                ] = "before_exact_4y"

                invalid_reasons.append(
                    "dtp_r2_before_exact_4_years"
                )

            elif event_date < minimum_r2:
                event[
                    "clinical_role"
                ] = "dtp_r2_interval_too_short"

                check[
                    "valid"
                ] = False

                check[
                    "reason"
                ] = "r1_to_r2_under_6_calendar_months"

                invalid_reasons.append(
                    "r1_to_r2_under_6_calendar_months"
                )

            else:
                valid_r2 = event_date

                event[
                    "clinical_role"
                ] = "dtp_r2"

                check[
                    "valid"
                ] = True

                check[
                    "reason"
                ] = "valid_r2"

            dtp_interval_checks.append(
                check
            )

            continue

        event[
            "clinical_role"
        ] = "excess_dtp_evidence"

    r2_earliest_date = (
        max(
            age_4y,
            _dtp_add_months_clamped(
                valid_r1,
                6,
            ),
        )
        if valid_r1 is not None
        else None
    )

    late_r1_closes_r2_before_age7 = (
        valid_r1 is not None
        and valid_r2 is None
        and r2_earliest_date is not None
        and r2_earliest_date >= age_7y
    )

    dtp_r1_history_valid = (
        valid_r1 is not None
    )

    dtp_r2_history_valid = (
        valid_r2 is not None
    )

    safe_for_routine_evaluation = (
        not source_history_incomplete
        and not chronology_ambiguous
        and not unsupported_product_keys
        and not excessive_pentavalent_evidence
        and not excessive_dtp_evidence
        and not pentavalent_history_invalid
        and not unresolved_pentavalent_exception_evidence
        and not invalid_reasons
    )

    return {
        "model_id":
            DTP_HISTORY_MODEL_ID,

        "target_family":
            "dtp_child_booster_history",

        "history_scope":
            history_scope,

        "age_1m15d_date":
            age_1m15d,

        "age_2m_date":
            age_2m,

        "age_6m_date":
            age_6m,

        "age_15m_date":
            age_15m,

        "age_4y_date":
            age_4y,

        "age_7y_date":
            age_7y,

        "pentavalent_history_state":
            penta[
                "state"
            ],

        "dtp_history_state":
            dtp[
                "state"
            ],

        "events":
            sorted(
                all_events,
                key=lambda item:
                    item[
                        "administration_date"
                    ],
            ),

        "pentavalent_events":
            penta[
                "events"
            ],

        "dtp_events":
            dtp[
                "events"
            ],

        "pentavalent_event_count":
            len(
                supported_penta_events
            ),

        "dtp_event_count":
            len(
                supported_dtp_events
            ),

        "qualifying_pentavalent_primary_dates":
            penta_dates[
                :3
            ],

        "pentavalent_basic_series_complete":
            pentavalent_basic_series_complete,

        "qualifying_pentavalent_d3_date":
            qualifying_pentavalent_d3_date,

        "dtp_r1_event_date":
            valid_r1,

        "dtp_r2_event_date":
            valid_r2,

        "dtp_r1_history_valid":
            dtp_r1_history_valid,

        "dtp_r2_history_valid":
            dtp_r2_history_valid,

        "pentavalent_interval_checks":
            pentavalent_interval_checks,

        "dtp_interval_checks":
            dtp_interval_checks,

        "r2_earliest_date":
            r2_earliest_date,

        "late_r1_closes_r2_before_age7":
            late_r1_closes_r2_before_age7,

        "unresolved_pentavalent_exception_evidence":
            unresolved_pentavalent_exception_evidence,

        "excessive_pentavalent_evidence":
            excessive_pentavalent_evidence,

        "excessive_dtp_evidence":
            excessive_dtp_evidence,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "source_history_incomplete":
            source_history_incomplete,

        "chronology_ambiguous":
            chronology_ambiguous,

        "invalid_history_reasons":
            sorted(
                set(
                    invalid_reasons
                )
            ),

        "safe_for_routine_evaluation":
            safe_for_routine_evaluation,

        "aggregate_toxoid_history_defines_dtp_completion":
            False,

        "normalizer_assigns_due_decision":
            False,

        "special_condition_inferred":
            False,

        "crie_eligibility_inferred":
            False,

        "outbreak_contact_context_inferred":
            False,

        "pentavalent_booster_substitution_inferred":
            False,

        "future_dt_schedule_inferred":
            False,

        "synthetic_score_applied":
            False,
    }
VARICELLA_HISTORY_MODEL_ID = (
    "PNI26-VARICELLA-CHILD-HISTORY-001"
)

VARICELLA_MONOVALENT_PRODUCT_KEY = (
    "varicella"
)

VARICELLA_SCRV_PRODUCT_KEY = (
    "mmrv_scrv"
)


def _varicella_add_months_clamped(
    value,
    months,
):
    from calendar import monthrange
    from datetime import date as _date

    zero_based = (
        value.month
        - 1
        + months
    )

    year = (
        value.year
        + zero_based // 12
    )

    month = (
        zero_based % 12
        + 1
    )

    day = min(
        value.day,
        monthrange(
            year,
            month,
        )[1],
    )

    return _date(
        year,
        month,
        day,
    )


def _varicella_plain_mapping(
    value,
    *,
    field_name,
):
    if hasattr(
        value,
        "model_dump",
    ):
        value = value.model_dump(
            mode="python"
        )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"{field_name} must be a mapping or model"
        )

    return dict(
        value
    )


def normalize_varicella_child_history(
    *,
    assessment_date,
    date_of_birth,
    varicella_history,
    varicella_history_scope,
    mmr_history,
):
    """
    Normalize general-child varicella-component history.

    Physical evidence is unified from:
      • monovalent varicella history; and
      • varicella components preserved by the locked MMR normalizer.

    The same SCRV/MMRV administration remains one physical event.

    MMR-series validity does not define VZ-series validity.
    """

    from datetime import date as _date

    if not isinstance(
        assessment_date,
        _date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        _date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if varicella_history_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "invalid varicella_history_scope"
        )

    age_9m = _varicella_add_months_clamped(
        date_of_birth,
        9,
    )

    age_12m = _varicella_add_months_clamped(
        date_of_birth,
        12,
    )

    age_15m = _varicella_add_months_clamped(
        date_of_birth,
        15,
    )

    age_4y = _varicella_add_months_clamped(
        date_of_birth,
        48,
    )

    age_7y = _varicella_add_months_clamped(
        date_of_birth,
        84,
    )

    monovalent = _varicella_plain_mapping(
        varicella_history,
        field_name="varicella_history",
    )

    if (
        monovalent.get(
            "vaccine_key"
        )
        != "varicella"
    ):
        raise ValueError(
            "varicella_history requires vaccine_key varicella"
        )

    monovalent_state = monovalent.get(
        "history_state"
    )

    monovalent_undated = int(
        monovalent.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if monovalent_undated < 0:
        raise ValueError(
            "reported_prior_doses_without_exact_dates "
            "cannot be negative"
        )

    if not isinstance(
        mmr_history,
        dict,
    ):
        raise ValueError(
            "mmr_history must be LOCKED normalized MMR history"
        )

    if (
        mmr_history.get(
            "target_family"
        )
        != "mmr_routine_history"
    ):
        raise ValueError(
            "mmr_history target_family must be mmr_routine_history"
        )

    mmr_scope = mmr_history.get(
        "history_scope"
    )

    if mmr_scope not in {
        "complete",
        "partial",
        "unknown",
    }:
        raise ValueError(
            "mmr_history has invalid history_scope"
        )

    mmr_age_15m = mmr_history.get(
        "age_15m_date"
    )

    if (
        mmr_age_15m
        != age_15m
    ):
        raise ValueError(
            "mmr_history does not match date_of_birth"
        )

    invalid_reasons = []
    unsupported_product_keys = set()

    source_history_incomplete = (
        varicella_history_scope
        != "complete"
        or monovalent_state
        not in {
            "documented_zero_dose",
            "documented_doses",
        }
        or monovalent_undated
        > 0
        or mmr_scope
        != "complete"
        or bool(
            mmr_history.get(
                "source_history_incomplete"
            )
        )
        or int(
            mmr_history.get(
                "reported_undated_event_count"
            )
            or 0
        )
        > 0
    )

    if source_history_incomplete:
        invalid_reasons.append(
            "source_history_incomplete"
        )

    monovalent_events = []

    for raw_dose in (
        monovalent.get(
            "doses"
        )
        or []
    ):
        dose = _varicella_plain_mapping(
            raw_dose,
            field_name="varicella dose",
        )

        administration_date = dose.get(
            "administration_date"
        )

        if isinstance(
            administration_date,
            str,
        ):
            administration_date = _date.fromisoformat(
                administration_date
            )

        if not isinstance(
            administration_date,
            _date,
        ):
            raise ValueError(
                "varicella administration_date must be a date"
            )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "varicella administration_date "
                "cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "varicella administration_date "
                "cannot follow assessment_date"
            )

        product_key = dose.get(
            "product_key"
        )

        supported = (
            product_key
            == VARICELLA_MONOVALENT_PRODUCT_KEY
        )

        if not supported:
            unsupported_product_keys.add(
                (
                    product_key
                    if isinstance(
                        product_key,
                        str,
                    )
                    else "<missing>"
                )
            )

        monovalent_events.append({
            "administration_date":
                administration_date,

            "source_family":
                "varicella",

            "product_key":
                product_key,

            "documentation_source":
                dose.get(
                    "documentation_source"
                ),

            "physical_event_kind": (
                "monovalent_varicella"
                if supported
                else "unsupported_varicella_family_product"
            ),

            "contains_varicella":
                supported,

            "source_mmr_clinical_role":
                None,

            "source_mmr_general_series_counted":
                None,

            "source_mmr_occupational_series_counted":
                None,

            "vz_age_scope":
                None,

            "lifetime_component_ordinal":
                None,

            "routine_component_ordinal":
                None,

            "vz_series_counted":
                False,

            "vz_series_role":
                None,
        })

    mmr_unsupported = list(
        mmr_history.get(
            "unsupported_product_keys"
        )
        or []
    )

    if mmr_unsupported:
        invalid_reasons.append(
            "mmr_history_contains_unsupported_product_evidence"
        )

        for product_key in mmr_unsupported:
            unsupported_product_keys.add(
                f"mmr:{product_key}"
            )

    scrv_component_events = []
    inconsistent_scrv_component_provenance = False

    mmr_events = mmr_history.get(
        "events"
    )

    if not isinstance(
        mmr_events,
        list,
    ):
        raise ValueError(
            "mmr_history events must be a list"
        )

    for raw_event in mmr_events:
        event = _varicella_plain_mapping(
            raw_event,
            field_name="normalized MMR event",
        )

        administration_date = event.get(
            "administration_date"
        )

        if isinstance(
            administration_date,
            str,
        ):
            administration_date = _date.fromisoformat(
                administration_date
            )

        if not isinstance(
            administration_date,
            _date,
        ):
            raise ValueError(
                "normalized MMR administration_date must be a date"
            )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "MMR administration_date cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "MMR administration_date cannot follow assessment_date"
            )

        product_key = event.get(
            "product_key"
        )

        contains_varicella = event.get(
            "contains_varicella"
        )

        if (
            product_key
            == VARICELLA_SCRV_PRODUCT_KEY
        ):
            if contains_varicella is not True:
                inconsistent_scrv_component_provenance = True
                continue

            scrv_component_events.append({
                "administration_date":
                    administration_date,

                "source_family":
                    "mmr",

                "product_key":
                    product_key,

                "documentation_source":
                    event.get(
                        "documentation_source"
                    ),

                "physical_event_kind":
                    "scrv_varicella_component",

                "contains_varicella":
                    True,

                "source_mmr_clinical_role":
                    event.get(
                        "clinical_role"
                    ),

                "source_mmr_general_series_counted":
                    event.get(
                        "general_series_counted"
                    ),

                "source_mmr_occupational_series_counted":
                    event.get(
                        "occupational_series_counted"
                    ),

                "vz_age_scope":
                    None,

                "lifetime_component_ordinal":
                    None,

                "routine_component_ordinal":
                    None,

                "vz_series_counted":
                    False,

                "vz_series_role":
                    None,
            })

            continue

        if contains_varicella is True:
            inconsistent_scrv_component_provenance = True

    if inconsistent_scrv_component_provenance:
        invalid_reasons.append(
            "inconsistent_scrv_component_provenance"
        )

    events = sorted(
        (
            monovalent_events
            + scrv_component_events
        ),
        key=lambda item:
            (
                item[
                    "administration_date"
                ],
                item[
                    "source_family"
                ],
                str(
                    item[
                        "product_key"
                    ]
                ),
            ),
    )

    for ordinal, event in enumerate(
        events,
        start=1,
    ):
        event[
            "lifetime_component_ordinal"
        ] = ordinal

        administration_date = event[
            "administration_date"
        ]

        if administration_date < age_9m:
            age_scope = (
                "before_postexposure_vaccination_age"
            )

        elif administration_date < age_12m:
            age_scope = (
                "postexposure_d0_age_evidence"
            )

        elif administration_date < age_15m:
            age_scope = (
                "anticipated_or_nonroutine_pre15_evidence"
            )

        elif administration_date < age_7y:
            age_scope = (
                "routine_child_age"
            )

        else:
            age_scope = (
                "age7plus_component_evidence"
            )

        event[
            "vz_age_scope"
        ] = age_scope

    vz_component_events = [
        event
        for event in events
        if (
            event[
                "contains_varicella"
            ]
            is True
        )
    ]

    date_counts = {}

    for event in vz_component_events:
        event_date = event[
            "administration_date"
        ]

        date_counts[
            event_date
        ] = (
            date_counts.get(
                event_date,
                0,
            )
            + 1
        )

    ambiguous_dates = sorted(
        event_date
        for event_date, count
        in date_counts.items()
        if count > 1
    )

    chronology_ambiguous = bool(
        ambiguous_dates
    )

    if chronology_ambiguous:
        invalid_reasons.append(
            "same_day_multiple_vz_containing_physical_events"
        )

    pre15_component_events = [
        event
        for event in vz_component_events
        if (
            event[
                "administration_date"
            ]
            < age_15m
        )
    ]

    pre15_component_evidence_present = bool(
        pre15_component_events
    )

    if pre15_component_evidence_present:
        invalid_reasons.append(
            "pre15_vz_component_requires_explicit_pathway_context"
        )

    routine_component_events = [
        event
        for event in vz_component_events
        if (
            age_15m
            <= event[
                "administration_date"
            ]
            < age_7y
        )
    ]

    for ordinal, event in enumerate(
        routine_component_events,
        start=1,
    ):
        event[
            "routine_component_ordinal"
        ] = ordinal

    valid_series_events = []
    interval_checks = []
    short_interval_event_count = 0

    for event in routine_component_events:
        event_date = event[
            "administration_date"
        ]

        if not valid_series_events:
            valid_series_events.append(
                event
            )

            event[
                "vz_series_counted"
            ] = True

            event[
                "vz_series_role"
            ] = "D1"

            continue

        if len(
            valid_series_events
        ) >= 2:
            event[
                "vz_series_role"
            ] = "extra_after_complete_series"

            continue

        previous = valid_series_events[
            -1
        ]

        threshold = _varicella_add_months_clamped(
            previous[
                "administration_date"
            ],
            3,
        )

        check = {
            "from_administration_date":
                previous[
                    "administration_date"
                ],

            "to_administration_date":
                event_date,

            "minimum_date":
                threshold,

            "minimum_calendar_months":
                3,

            "fixed_day_conversion_used":
                False,

            "valid":
                event_date
                >= threshold,
        }

        interval_checks.append(
            check
        )

        if event_date >= threshold:
            valid_series_events.append(
                event
            )

            event[
                "vz_series_counted"
            ] = True

            event[
                "vz_series_role"
            ] = "D2"

        else:
            short_interval_event_count += 1

            event[
                "vz_series_role"
            ] = "short_interval_extra_not_counted"

    valid_child_series_dates = [
        event[
            "administration_date"
        ]
        for event in valid_series_events
    ]

    child_series_complete = (
        len(
            valid_series_events
        )
        >= 2
    )

    unsupported_product_evidence_present = bool(
        unsupported_product_keys
    )

    if unsupported_product_evidence_present:
        invalid_reasons.append(
            "unsupported_product_identity"
        )

    safe_for_routine_evaluation = (
        not source_history_incomplete
        and not unsupported_product_evidence_present
        and not inconsistent_scrv_component_provenance
        and not chronology_ambiguous
        and not pre15_component_evidence_present
    )

    return {
        "model_id":
            VARICELLA_HISTORY_MODEL_ID,

        "target_family":
            "varicella_child_routine_history",

        "varicella_history_scope":
            varicella_history_scope,

        "mmr_history_scope":
            mmr_scope,

        "age_9m_date":
            age_9m,

        "age_12m_date":
            age_12m,

        "age_15m_date":
            age_15m,

        "age_4y_date":
            age_4y,

        "age_7y_date":
            age_7y,

        "events":
            events,

        "monovalent_events":
            monovalent_events,

        "scrv_component_events":
            scrv_component_events,

        "lifetime_varicella_component_event_count":
            len(
                vz_component_events
            ),

        "routine_age_component_event_count":
            len(
                routine_component_events
            ),

        "valid_child_component_dose_count":
            len(
                valid_series_events
            ),

        "valid_child_series_dates":
            valid_child_series_dates,

        "first_valid_component_date": (
            valid_child_series_dates[
                0
            ]
            if valid_child_series_dates
            else None
        ),

        "second_valid_component_date": (
            valid_child_series_dates[
                1
            ]
            if len(
                valid_child_series_dates
            )
            >= 2
            else None
        ),

        "child_series_complete":
            child_series_complete,

        "interval_checks":
            interval_checks,

        "short_interval_event_count":
            short_interval_event_count,

        "pre15_component_evidence_present":
            pre15_component_evidence_present,

        "pre15_component_event_count":
            len(
                pre15_component_events
            ),

        "same_day_ambiguous_dates":
            ambiguous_dates,

        "source_history_incomplete":
            source_history_incomplete,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "inconsistent_scrv_component_provenance":
            inconsistent_scrv_component_provenance,

        "chronology_ambiguous":
            chronology_ambiguous,

        "invalid_history_reasons":
            sorted(
                set(
                    invalid_reasons
                )
            ),

        "safe_for_routine_evaluation":
            safe_for_routine_evaluation,

        "mmr_validity_defines_vz_validity":
            False,

        "physical_event_cloning_applied":
            False,

        "disease_history_inferred":
            False,

        "epidemiologic_context_inferred":
            False,

        "pregnancy_inferred":
            False,

        "special_condition_inferred":
            False,

        "normalizer_assigns_due_decision":
            False,

        "synthetic_score_applied":
            False,
    }
DENGUE_TAKEDA_HISTORY_MODEL_ID = (
    "PNI26-DNG4-TAKEDA-HISTORY-001"
)

DENGUE_PRODUCT_TAKEDA = (
    "dengue_takeda"
)

DENGUE_PRODUCT_BUTANTAN = (
    "dengue_butantan"
)

DENGUE_PRODUCT_SANOFI_LEGACY = (
    "dengue_sanofi_legacy"
)

DENGUE_SUPPORTED_PRODUCTS = frozenset({
    DENGUE_PRODUCT_TAKEDA,
    DENGUE_PRODUCT_BUTANTAN,
    DENGUE_PRODUCT_SANOFI_LEGACY,
})


def _dengue_add_years_clamped(
    value,
    years,
):
    from calendar import monthrange
    from datetime import date as _date

    year = (
        value.year
        + years
    )

    month = value.month

    day = min(
        value.day,
        monthrange(
            year,
            month,
        )[1],
    )

    return _date(
        year,
        month,
        day,
    )


def normalize_dengue_takeda_history(
    *,
    assessment_date,
    date_of_birth,
    history,
    history_scope,
):
    """
    Normalize product-sensitive dengue vaccine history.

    The normalizer derives Takeda series chronology and the narrow
    2026 Takeda-D1 -> accidental-Butantan error-management outcome.

    Disease timing and current clinical eligibility remain outside
    this history layer.
    """

    from datetime import date as _date
    from datetime import timedelta

    if not isinstance(
        assessment_date,
        _date,
    ):
        raise ValueError(
            "assessment_date must be a date"
        )

    if not isinstance(
        date_of_birth,
        _date,
    ):
        raise ValueError(
            "date_of_birth must be a date"
        )

    if (
        assessment_date
        < date_of_birth
    ):
        raise ValueError(
            "assessment_date cannot precede date_of_birth"
        )

    if (
        history_scope
        not in ALLOWED_HISTORY_SCOPES
    ):
        raise ValueError(
            "invalid dengue history_scope"
        )

    raw_history = _as_plain_dict(
        history
    )

    if (
        raw_history.get(
            "vaccine_key"
        )
        != "dengue"
    ):
        raise ValueError(
            "dengue history requires vaccine_key=dengue"
        )

    history_state = raw_history.get(
        "history_state"
    )

    if (
        history_state
        not in ALLOWED_HISTORY_STATES
    ):
        raise ValueError(
            "invalid dengue history_state"
        )

    reported_undated = int(
        raw_history.get(
            "reported_prior_doses_without_exact_dates"
        )
        or 0
    )

    if reported_undated < 0:
        raise ValueError(
            "reported_prior_doses_without_exact_dates "
            "cannot be negative"
        )

    source_history_incomplete = (
        history_scope
        != "complete"
        or history_state
        in {
            "partial_record",
            "unknown",
        }
        or reported_undated
        > 0
    )

    invalid_history_reasons = []

    if source_history_incomplete:
        invalid_history_reasons.append(
            "source_history_incomplete"
        )

    age_4y = _dengue_add_years_clamped(
        date_of_birth,
        4,
    )

    age_10y = _dengue_add_years_clamped(
        date_of_birth,
        10,
    )

    age_12y = _dengue_add_years_clamped(
        date_of_birth,
        12,
    )

    age_15y = _dengue_add_years_clamped(
        date_of_birth,
        15,
    )

    age_60y = _dengue_add_years_clamped(
        date_of_birth,
        60,
    )

    events = []
    unsupported_product_keys = set()

    for raw_dose in (
        raw_history.get(
            "doses"
        )
        or []
    ):
        dose = _as_plain_dict(
            raw_dose
        )

        administration_date = _as_date(
            dose.get(
                "administration_date"
            )
        )

        if (
            administration_date
            < date_of_birth
        ):
            raise ValueError(
                "dengue administration_date "
                "cannot precede date_of_birth"
            )

        if (
            administration_date
            > assessment_date
        ):
            raise ValueError(
                "dengue administration_date "
                "cannot follow assessment_date"
            )

        product_key = dose.get(
            "product_key"
        )

        if (
            product_key
            not in DENGUE_SUPPORTED_PRODUCTS
        ):
            unsupported_product_keys.add(
                (
                    product_key
                    if isinstance(
                        product_key,
                        str,
                    )
                    else "<missing>"
                )
            )

            manufacturer_role = (
                "unsupported"
            )

        elif (
            product_key
            == DENGUE_PRODUCT_TAKEDA
        ):
            manufacturer_role = (
                "takeda"
            )

        elif (
            product_key
            == DENGUE_PRODUCT_BUTANTAN
        ):
            manufacturer_role = (
                "butantan"
            )

        else:
            manufacturer_role = (
                "sanofi_legacy"
            )

        if (
            administration_date
            < age_4y
        ):
            age_scope = (
                "before_takeda_label_age"
            )

        elif (
            administration_date
            < age_10y
        ):
            age_scope = (
                "takeda_label_age_before_pni_target"
            )

        elif (
            administration_date
            < age_12y
        ):
            age_scope = (
                "pni_takeda_age_below_butantan_label"
            )

        elif (
            administration_date
            < age_15y
        ):
            age_scope = (
                "pni_takeda_initiation_age"
            )

        elif (
            administration_date
            < age_60y
        ):
            age_scope = (
                "age15_to_before60"
            )

        else:
            age_scope = (
                "age60plus"
            )

        if (
            manufacturer_role
            == "takeda"
        ):
            product_label_age_valid = (
                age_4y
                <= administration_date
                < age_60y
            )

            pni_takeda_initiation_age_event = (
                age_10y
                <= administration_date
                < age_15y
            )

        elif (
            manufacturer_role
            == "butantan"
        ):
            product_label_age_valid = (
                age_12y
                <= administration_date
                < age_60y
            )

            pni_takeda_initiation_age_event = False

        else:
            product_label_age_valid = None
            pni_takeda_initiation_age_event = False

        events.append({
            "administration_date":
                administration_date,

            "product_key":
                product_key,

            "documentation_source":
                dose.get(
                    "documentation_source"
                ),

            "manufacturer_role":
                manufacturer_role,

            "age_scope":
                age_scope,

            "product_label_age_valid":
                product_label_age_valid,

            "pni_takeda_initiation_age_event":
                pni_takeda_initiation_age_event,

            "physical_event_ordinal":
                None,

            "product_series_role":
                None,

            "takeda_series_counted":
                False,

            "takeda_series_role":
                None,
        })

    events.sort(
        key=lambda event: (
            event[
                "administration_date"
            ],
            str(
                event[
                    "product_key"
                ]
            ),
        )
    )

    for ordinal, event in enumerate(
        events,
        start=1,
    ):
        event[
            "physical_event_ordinal"
        ] = ordinal

    if unsupported_product_keys:
        invalid_history_reasons.append(
            "unsupported_product_identity"
        )

    date_counts = {}

    for event in events:
        event_date = event[
            "administration_date"
        ]

        date_counts[
            event_date
        ] = (
            date_counts.get(
                event_date,
                0,
            )
            + 1
        )

    same_day_ambiguous_dates = sorted(
        event_date
        for event_date, count
        in date_counts.items()
        if count > 1
    )

    same_day_product_conflict = bool(
        same_day_ambiguous_dates
    )

    if same_day_product_conflict:
        invalid_history_reasons.append(
            "same_day_multiple_dengue_physical_events"
        )

    takeda_events = [
        event
        for event in events
        if (
            event[
                "manufacturer_role"
            ]
            == "takeda"
        )
    ]

    butantan_events = [
        event
        for event in events
        if (
            event[
                "manufacturer_role"
            ]
            == "butantan"
        )
    ]

    sanofi_legacy_events = [
        event
        for event in events
        if (
            event[
                "manufacturer_role"
            ]
            == "sanofi_legacy"
        )
    ]

    invalid_takeda_label_age_events = [
        event
        for event in takeda_events
        if (
            event[
                "product_label_age_valid"
            ]
            is not True
        )
    ]

    if invalid_takeda_label_age_events:
        invalid_history_reasons.append(
            "takeda_event_outside_supported_label_age"
        )

    invalid_butantan_label_age_events = [
        event
        for event in butantan_events
        if (
            event[
                "product_label_age_valid"
            ]
            is not True
        )
    ]

    if invalid_butantan_label_age_events:
        invalid_history_reasons.append(
            "butantan_event_outside_supported_label_age"
        )

    sanofi_history_present = bool(
        sanofi_legacy_events
    )

    if sanofi_history_present:
        invalid_history_reasons.append(
            "sanofi_legacy_history_requires_nonroutine_review"
        )

    valid_takeda_d1_event = None

    for event in takeda_events:
        event_date = event[
            "administration_date"
        ]

        if (
            event[
                "product_label_age_valid"
            ]
            is not True
        ):
            event[
                "product_series_role"
            ] = "takeda_out_of_label_event"

            continue

        if event_date >= age_15y:
            if valid_takeda_d1_event is None:
                event[
                    "product_series_role"
                ] = (
                    "takeda_first_event_after_pni_initiation_ceiling"
                )

                invalid_history_reasons.append(
                    "first_takeda_event_at_or_after_exact15y"
                )

            continue

        valid_takeda_d1_event = event

        event[
            "product_series_role"
        ] = "takeda_candidate_D1"

        event[
            "takeda_series_counted"
        ] = True

        event[
            "takeda_series_role"
        ] = "D1"

        break

    valid_takeda_d1_date = (
        valid_takeda_d1_event[
            "administration_date"
        ]
        if valid_takeda_d1_event is not None
        else None
    )

    valid_takeda_d2_event = None
    early_takeda_d2_events = []
    next_corrective_takeda_date = None

    cross_product_error_completion = False
    cross_product_completion_date = None
    cross_product_ambiguous = False

    butantan_seen_before_valid_takeda_d1 = False

    if valid_takeda_d1_event is not None:
        base_takeda_threshold = (
            valid_takeda_d1_date
            + timedelta(
                days=90,
            )
        )

        corrective_threshold = (
            base_takeda_threshold
        )

        for event in events:
            if (
                event[
                    "physical_event_ordinal"
                ]
                <= valid_takeda_d1_event[
                    "physical_event_ordinal"
                ]
            ):
                if (
                    event[
                        "manufacturer_role"
                    ]
                    == "butantan"
                ):
                    butantan_seen_before_valid_takeda_d1 = True

                continue

            manufacturer = event[
                "manufacturer_role"
            ]

            event_date = event[
                "administration_date"
            ]

            if (
                manufacturer
                == "sanofi_legacy"
            ):
                continue

            if (
                manufacturer
                == "unsupported"
            ):
                continue

            if (
                manufacturer
                == "butantan"
            ):
                if (
                    event[
                        "product_label_age_valid"
                    ]
                    is not True
                ):
                    event[
                        "product_series_role"
                    ] = (
                        "butantan_out_of_label_event"
                    )

                    cross_product_ambiguous = True

                    continue

                if (
                    valid_takeda_d2_event
                    is not None
                    or cross_product_error_completion
                ):
                    event[
                        "product_series_role"
                    ] = (
                        "butantan_after_completed_takeda_history"
                    )

                    continue

                if early_takeda_d2_events:
                    event[
                        "product_series_role"
                    ] = (
                        "butantan_after_complex_early_takeda_history"
                    )

                    cross_product_ambiguous = True

                    continue

                cross_product_days = (
                    event_date
                    - valid_takeda_d1_date
                ).days

                if cross_product_days >= 30:
                    event[
                        "product_series_role"
                    ] = (
                        "cross_product_error_completion"
                    )

                    cross_product_error_completion = True
                    cross_product_completion_date = event_date

                else:
                    event[
                        "product_series_role"
                    ] = (
                        "cross_product_error_too_early"
                    )

                    cross_product_ambiguous = True

                continue

            if (
                manufacturer
                != "takeda"
            ):
                continue

            if (
                event
                is valid_takeda_d1_event
            ):
                continue

            if (
                event[
                    "product_label_age_valid"
                ]
                is not True
            ):
                event[
                    "product_series_role"
                ] = "takeda_out_of_label_event"

                continue

            if cross_product_error_completion:
                event[
                    "product_series_role"
                ] = "takeda_after_error_managed_completion"

                continue

            if (
                valid_takeda_d2_event
                is not None
            ):
                event[
                    "product_series_role"
                ] = "extra_after_complete_takeda_series"

                continue

            if event_date >= corrective_threshold:
                valid_takeda_d2_event = event

                event[
                    "product_series_role"
                ] = "takeda_candidate_D2"

                event[
                    "takeda_series_counted"
                ] = True

                event[
                    "takeda_series_role"
                ] = "D2"

                continue

            event[
                "product_series_role"
            ] = "takeda_short_interval_extra"

            event[
                "takeda_series_role"
            ] = "early_D2_not_counted"

            early_takeda_d2_events.append(
                event
            )

            corrective_threshold = max(
                base_takeda_threshold,
                event_date
                + timedelta(
                    days=30,
                ),
            )

        if (
            valid_takeda_d2_event is None
            and not cross_product_error_completion
        ):
            next_corrective_takeda_date = (
                corrective_threshold
            )

    else:
        if butantan_events:
            cross_product_ambiguous = True

            invalid_history_reasons.append(
                "butantan_without_prior_valid_takeda_D1"
            )

            for event in butantan_events:
                if (
                    event[
                        "product_series_role"
                    ]
                    is None
                ):
                    event[
                        "product_series_role"
                    ] = (
                        "butantan_without_prior_valid_takeda_D1"
                    )

    if butantan_seen_before_valid_takeda_d1:
        cross_product_ambiguous = True

        invalid_history_reasons.append(
            "butantan_before_valid_takeda_D1"
        )

    if cross_product_ambiguous:
        invalid_history_reasons.append(
            "cross_product_history_requires_review"
        )

    valid_takeda_d2_date = (
        valid_takeda_d2_event[
            "administration_date"
        ]
        if valid_takeda_d2_event is not None
        else None
    )

    valid_takeda_dose_count = (
        int(
            valid_takeda_d1_event
            is not None
        )
        + int(
            valid_takeda_d2_event
            is not None
        )
    )

    takeda_series_complete = (
        valid_takeda_dose_count
        >= 2
    )

    error_managed_series_complete = (
        cross_product_error_completion
    )

    position20_series_complete = (
        takeda_series_complete
        or error_managed_series_complete
    )

    if (
        valid_takeda_d1_event
        is not None
        and (
            valid_takeda_d1_date
            < age_10y
        )
    ):
        valid_takeda_d1_event[
            "product_series_role"
        ] = (
            "takeda_valid_D1_before_pni_target_age"
        )

    if unsupported_product_keys:
        safe_for_routine_evaluation = False

    else:
        safe_for_routine_evaluation = (
            not source_history_incomplete
            and not same_day_product_conflict
            and not invalid_takeda_label_age_events
            and not invalid_butantan_label_age_events
            and not sanofi_history_present
            and not cross_product_ambiguous
            and (
                "first_takeda_event_at_or_after_exact15y"
                not in invalid_history_reasons
            )
        )

    return {
        "model_id":
            DENGUE_TAKEDA_HISTORY_MODEL_ID,

        "target_family":
            "dengue_takeda_routine_history",

        "history_scope":
            history_scope,

        "lifetime_history_state":
            history_state,

        "reported_undated_event_count":
            reported_undated,

        "age_4y_date":
            age_4y,

        "age_10y_date":
            age_10y,

        "age_12y_date":
            age_12y,

        "age_15y_date":
            age_15y,

        "age_60y_date":
            age_60y,

        "events":
            events,

        "takeda_events":
            takeda_events,

        "butantan_events":
            butantan_events,

        "sanofi_legacy_events":
            sanofi_legacy_events,

        "lifetime_dengue_vaccine_event_count":
            len(
                events
            ),

        "valid_takeda_d1_date":
            valid_takeda_d1_date,

        "valid_takeda_d2_date":
            valid_takeda_d2_date,

        "valid_takeda_dose_count":
            valid_takeda_dose_count,

        "takeda_series_complete":
            takeda_series_complete,

        "early_takeda_d2_events":
            early_takeda_d2_events,

        "early_takeda_d2_event_count":
            len(
                early_takeda_d2_events
            ),

        "next_corrective_takeda_date":
            next_corrective_takeda_date,

        "cross_product_error_completion":
            cross_product_error_completion,

        "cross_product_completion_date":
            cross_product_completion_date,

        "cross_product_ambiguous":
            cross_product_ambiguous,

        "error_managed_series_complete":
            error_managed_series_complete,

        "position20_series_complete":
            position20_series_complete,

        "sanofi_history_present":
            sanofi_history_present,

        "source_history_incomplete":
            source_history_incomplete,

        "unsupported_product_keys":
            sorted(
                unsupported_product_keys
            ),

        "same_day_ambiguous_dates":
            same_day_ambiguous_dates,

        "same_day_product_conflict":
            same_day_product_conflict,

        "invalid_history_reasons":
            sorted(
                set(
                    invalid_history_reasons
                )
            ),

        "safe_for_routine_evaluation":
            safe_for_routine_evaluation,

        "d1_d2_interval_days":
            90,

        "early_dose_corrective_interval_days":
            30,

        "cross_product_error_minimum_days":
            30,

        "calendar_month_interval_used":
            False,

        "generic_cross_manufacturer_counting_applied":
            False,

        "dengue_disease_history_inferred":
            False,

        "pregnancy_inferred":
            False,

        "breastfeeding_inferred":
            False,

        "immune_status_inferred":
            False,

        "geographic_eligibility_inferred":
            False,

        "normalizer_assigns_due_decision":
            False,

        "synthetic_score_applied":
            False,
    }
