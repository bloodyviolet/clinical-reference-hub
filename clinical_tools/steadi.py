"""Complementary CDC STEADI assessment engines.

These tools are deliberately separate from the Brazil-primary
Caderneta Brasileira da Pessoa Idosa 2026 and IVCF-20 instruments.

Implemented complementary assessments:

1. Timed Up and Go (TUG)
2. 30-Second Chair Stand
3. 4-Stage Balance
4. Orthostatic blood pressure

No synthetic score is calculated across STEADI assessments or across
STEADI, Caderneta, and IVCF-20.

CDC STEADI thresholds are complementary international guidance and
must not be represented as generic national SUS thresholds.
"""

from __future__ import annotations

from datetime import date
import math


STEADI_CLINICAL_RESOURCES_URL = (
    "https://www.cdc.gov/steadi/hcp/"
    "clinical-resources/index.html"
)

STEADI_TUG_URL = (
    "https://www.cdc.gov/steadi/media/pdfs/"
    "STEADI-Assessment-TUG-508.pdf"
)

STEADI_CHAIR_STAND_URL = (
    "https://www.cdc.gov/steadi/media/pdfs/"
    "STEADI-Assessment-30Sec-508.pdf"
)

STEADI_FOUR_STAGE_URL = (
    "https://www.cdc.gov/steadi/media/pdfs/"
    "STEADI-Assessment-4Stage-508.pdf"
)

STEADI_ORTHOSTATIC_BP_URL = (
    "https://www.cdc.gov/steadi/media/pdfs/"
    "STEADI-Assessment-MeasuringBP-508.pdf"
)


CHAIR_STAND_THRESHOLDS = {
    "60-64": {
        "minimum_age": 60,
        "maximum_age": 64,
        "male": 14,
        "female": 12,
    },
    "65-69": {
        "minimum_age": 65,
        "maximum_age": 69,
        "male": 12,
        "female": 11,
    },
    "70-74": {
        "minimum_age": 70,
        "maximum_age": 74,
        "male": 12,
        "female": 10,
    },
    "75-79": {
        "minimum_age": 75,
        "maximum_age": 79,
        "male": 11,
        "female": 10,
    },
    "80-84": {
        "minimum_age": 80,
        "maximum_age": 84,
        "male": 10,
        "female": 9,
    },
    "85-89": {
        "minimum_age": 85,
        "maximum_age": 89,
        "male": 8,
        "female": 8,
    },
    "90-94": {
        "minimum_age": 90,
        "maximum_age": 94,
        "male": 7,
        "female": 4,
    },
}


def _require_bool(
    name: str,
    value: bool,
) -> None:
    if not isinstance(
        value,
        bool,
    ):
        raise ValueError(
            f"{name} must be boolean."
        )


def _require_integer(
    name: str,
    value: int,
    *,
    minimum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
    ):
        raise ValueError(
            f"{name} must be an integer "
            f"greater than or equal to {minimum}."
        )

    return value


def _require_number(
    name: str,
    value: int | float,
    *,
    minimum: float,
    minimum_inclusive: bool = True,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(
            value,
            (int, float),
        )
        or not math.isfinite(value)
    ):
        raise ValueError(
            f"{name} must be a finite number."
        )

    number = float(value)

    invalid = (
        number < minimum
        if minimum_inclusive
        else number <= minimum
    )

    if invalid:
        comparator = (
            "greater than or equal to"
            if minimum_inclusive
            else "greater than"
        )

        raise ValueError(
            f"{name} must be {comparator} "
            f"to {minimum}."
        )

    return number


def _require_balance_seconds(
    name: str,
    value: int | float,
) -> float:
    seconds = _require_number(
        name,
        value,
        minimum=0,
    )

    if seconds > 10:
        raise ValueError(
            f"{name} cannot exceed the "
            "10-second STEADI stage interval."
        )

    return seconds


def _chair_reference(
    age_years: int,
    sex: str,
) -> tuple[str | None, int | None]:
    for (
        band,
        values,
    ) in CHAIR_STAND_THRESHOLDS.items():
        if (
            values["minimum_age"]
            <= age_years
            <= values["maximum_age"]
        ):
            return (
                band,
                values[sex],
            )

    return (
        None,
        None,
    )


def calculate_steadi_tug(
    *,
    time_seconds: int | float,
    walking_aid_used: bool,
    standard_3m_protocol_confirmed: bool,
) -> dict:
    """Interpret the complementary CDC STEADI Timed Up and Go."""

    seconds = _require_number(
        "time_seconds",
        time_seconds,
        minimum=0,
        minimum_inclusive=False,
    )

    _require_bool(
        "walking_aid_used",
        walking_aid_used,
    )

    _require_bool(
        "standard_3m_protocol_confirmed",
        standard_3m_protocol_confirmed,
    )

    if not standard_3m_protocol_confirmed:
        raise ValueError(
            "The standard STEADI 3-m / 10-ft "
            "TUG protocol must be confirmed."
        )

    increased_fall_risk = (
        seconds >= 12
    )

    return {
        "tool":
            "steadi_timed_up_and_go",

        "source_role":
            "complementary_international_guidance",

        "time_seconds":
            seconds,

        "course_distance_m":
            3,

        "course_distance_ft":
            10,

        "walking_aid_allowed":
            True,

        "walking_aid_used":
            walking_aid_used,

        "threshold_seconds":
            12,

        "threshold_comparison":
            ">=",

        "increased_fall_risk":
            increased_fall_risk,

        "ivcf_four_meter_gait_inferred":
            False,

        "national_sus_threshold_applied":
            False,

        "automatic_cross_instrument_inference_applied":
            False,

        "synthetic_cross_instrument_score_applied":
            False,

        "interpretation_pt": (
            (
                "TUG STEADI em 12 segundos ou mais: "
                "o instrumento indica risco aumentado "
                "de queda."
            )
            if increased_fall_risk
            else (
                "TUG STEADI abaixo de 12 segundos: "
                "o ponto de corte STEADI de risco aumentado "
                "não foi atingido."
            )
        ),

        "interpretation_en": (
            (
                "STEADI TUG at 12 seconds or longer: "
                "the instrument indicates increased fall risk."
            )
            if increased_fall_risk
            else (
                "STEADI TUG below 12 seconds: "
                "the STEADI increased-risk threshold "
                "was not reached."
            )
        ),
    }


def calculate_steadi_chair_stand_30s(
    *,
    age_years: int,
    sex: str,
    repetitions: int,
    arms_required_to_stand: bool,
    standard_30_second_protocol_confirmed: bool,
) -> dict:
    """Interpret the complementary CDC 30-Second Chair Stand."""

    age = _require_integer(
        "age_years",
        age_years,
        minimum=60,
    )

    if sex not in {
        "male",
        "female",
    }:
        raise ValueError(
            "sex must be 'male' or 'female' "
            "for the STEADI reference table."
        )

    repetitions_value = _require_integer(
        "repetitions",
        repetitions,
        minimum=0,
    )

    _require_bool(
        "arms_required_to_stand",
        arms_required_to_stand,
    )

    _require_bool(
        "standard_30_second_protocol_confirmed",
        standard_30_second_protocol_confirmed,
    )

    if not standard_30_second_protocol_confirmed:
        raise ValueError(
            "The standard STEADI 30-second "
            "Chair Stand protocol must be confirmed."
        )

    recorded_repetitions = (
        0
        if arms_required_to_stand
        else repetitions_value
    )

    (
        reference_age_band,
        below_average_threshold,
    ) = _chair_reference(
        age,
        sex,
    )

    classification_available = (
        below_average_threshold
        is not None
    )

    if classification_available:
        below_average = (
            recorded_repetitions
            < below_average_threshold
        )

        increased_fall_risk = (
            below_average
        )
    else:
        below_average = None
        increased_fall_risk = None

    return {
        "tool":
            "steadi_30_second_chair_stand",

        "source_role":
            "complementary_international_guidance",

        "age_years":
            age,

        "reference_sex":
            sex,

        "observed_repetitions_input":
            repetitions_value,

        "arms_required_to_stand":
            arms_required_to_stand,

        "test_stopped_due_to_arm_use":
            arms_required_to_stand,

        "recorded_repetitions":
            recorded_repetitions,

        "reference_age_band":
            reference_age_band,

        "below_average_threshold":
            below_average_threshold,

        "threshold_comparison":
            "<",

        "reference_classification_available":
            classification_available,

        "below_average":
            below_average,

        "increased_fall_risk":
            increased_fall_risk,

        "reference_table_maximum_age_years":
            94,

        "cutoff_extrapolated":
            False,

        "national_sus_threshold_applied":
            False,

        "automatic_cross_instrument_inference_applied":
            False,

        "synthetic_cross_instrument_score_applied":
            False,

        "interpretation_pt": (
            (
                "A tabela STEADI publicada não fornece "
                "ponto de corte etário/sexo para esta idade; "
                "o número bruto de repetições é preservado "
                "sem classificação extrapolada."
            )
            if not classification_available
            else (
                (
                    "Resultado abaixo da média de referência "
                    "STEADI para idade e sexo de referência."
                )
                if below_average
                else (
                    "Resultado não está abaixo da média "
                    "de referência STEADI para idade e sexo "
                    "de referência."
                )
            )
        ),

        "interpretation_en": (
            (
                "The published STEADI table provides no "
                "age/sex cutoff for this age; the raw count "
                "is preserved without an extrapolated "
                "classification."
            )
            if not classification_available
            else (
                (
                    "Result is below the STEADI reference "
                    "average for the reference age and sex."
                )
                if below_average
                else (
                    "Result is not below the STEADI reference "
                    "average for the reference age and sex."
                )
            )
        ),
    }


def calculate_steadi_four_stage_balance(
    *,
    side_by_side_seconds: int | float,
    semi_tandem_seconds: int | float | None,
    tandem_seconds: int | float | None,
    one_leg_seconds: int | float | None,
    assistive_device_used: bool,
    standard_four_stage_protocol_confirmed: bool,
) -> dict:
    """Interpret the complementary CDC 4-Stage Balance Test."""

    _require_bool(
        "assistive_device_used",
        assistive_device_used,
    )

    _require_bool(
        "standard_four_stage_protocol_confirmed",
        standard_four_stage_protocol_confirmed,
    )

    if not standard_four_stage_protocol_confirmed:
        raise ValueError(
            "The standard STEADI 4-Stage Balance "
            "protocol must be confirmed."
        )

    if assistive_device_used:
        raise ValueError(
            "STEADI 4-Stage Balance does not permit "
            "an assistive device during the test."
        )

    side = _require_balance_seconds(
        "side_by_side_seconds",
        side_by_side_seconds,
    )

    semi = (
        None
        if semi_tandem_seconds is None
        else _require_balance_seconds(
            "semi_tandem_seconds",
            semi_tandem_seconds,
        )
    )

    tandem = (
        None
        if tandem_seconds is None
        else _require_balance_seconds(
            "tandem_seconds",
            tandem_seconds,
        )
    )

    one_leg = (
        None
        if one_leg_seconds is None
        else _require_balance_seconds(
            "one_leg_seconds",
            one_leg_seconds,
        )
    )

    if side < 10:
        if any(
            value is not None
            for value in (
                semi,
                tandem,
                one_leg,
            )
        ):
            raise ValueError(
                "Later 4-Stage Balance positions "
                "must not be recorded after failure "
                "to hold side-by-side for 10 seconds."
            )

        last_stage_attempted = (
            "side_by_side"
        )

        tandem_held_10_seconds = (
            False
        )

    else:
        if semi is None:
            raise ValueError(
                "semi_tandem_seconds is required "
                "after side-by-side is held for 10 seconds."
            )

        if semi < 10:
            if (
                tandem is not None
                or one_leg is not None
            ):
                raise ValueError(
                    "Later 4-Stage Balance positions "
                    "must not be recorded after failure "
                    "to hold semi-tandem for 10 seconds."
                )

            last_stage_attempted = (
                "semi_tandem"
            )

            tandem_held_10_seconds = (
                False
            )

        else:
            if tandem is None:
                raise ValueError(
                    "tandem_seconds is required after "
                    "semi-tandem is held for 10 seconds."
                )

            if tandem < 10:
                if one_leg is not None:
                    raise ValueError(
                        "One-leg time must not be recorded "
                        "after failure to hold tandem "
                        "for 10 seconds."
                    )

                last_stage_attempted = (
                    "tandem"
                )

                tandem_held_10_seconds = (
                    False
                )

            else:
                if one_leg is None:
                    raise ValueError(
                        "one_leg_seconds is required after "
                        "tandem is held for 10 seconds."
                    )

                last_stage_attempted = (
                    "one_leg"
                )

                tandem_held_10_seconds = (
                    True
                )

    increased_fall_risk = (
        not tandem_held_10_seconds
    )

    return {
        "tool":
            "steadi_four_stage_balance",

        "source_role":
            "complementary_international_guidance",

        "side_by_side_seconds":
            side,

        "semi_tandem_seconds":
            semi,

        "tandem_seconds":
            tandem,

        "one_leg_seconds":
            one_leg,

        "target_seconds_per_stage":
            10,

        "last_stage_attempted":
            last_stage_attempted,

        "tandem_held_10_seconds":
            tandem_held_10_seconds,

        "increased_fall_risk":
            increased_fall_risk,

        "assistive_device_allowed":
            False,

        "assistive_device_used":
            False,

        "eyes_open_required":
            True,

        "national_sus_threshold_applied":
            False,

        "automatic_cross_instrument_inference_applied":
            False,

        "synthetic_cross_instrument_score_applied":
            False,

        "interpretation_pt": (
            (
                "No 4-Stage Balance STEADI, não foi "
                "demonstrada manutenção da posição tandem "
                "por pelo menos 10 segundos; o instrumento "
                "indica risco aumentado de queda."
            )
            if increased_fall_risk
            else (
                "A posição tandem foi mantida por pelo menos "
                "10 segundos; o critério específico STEADI "
                "de risco aumentado pelo tandem não foi atingido."
            )
        ),

        "interpretation_en": (
            (
                "In the STEADI 4-Stage Balance Test, tandem "
                "stance was not demonstrated for at least "
                "10 seconds; the instrument indicates "
                "increased fall risk."
            )
            if increased_fall_risk
            else (
                "Tandem stance was maintained for at least "
                "10 seconds; the STEADI tandem-specific "
                "increased-risk criterion was not met."
            )
        ),
    }


def calculate_steadi_orthostatic_bp(
    *,
    supine_sbp_mm_hg: int | float,
    supine_dbp_mm_hg: int | float,
    supine_pulse_bpm: int | float,
    standing_1m_sbp_mm_hg: int | float,
    standing_1m_dbp_mm_hg: int | float,
    standing_1m_pulse_bpm: int | float,
    standing_3m_sbp_mm_hg: int | float,
    standing_3m_dbp_mm_hg: int | float,
    standing_3m_pulse_bpm: int | float,
    lightheaded_or_dizzy: bool,
    standard_5_1_3_protocol_confirmed: bool,
) -> dict:
    """Interpret the complementary CDC STEADI orthostatic BP test."""

    _require_bool(
        "lightheaded_or_dizzy",
        lightheaded_or_dizzy,
    )

    _require_bool(
        "standard_5_1_3_protocol_confirmed",
        standard_5_1_3_protocol_confirmed,
    )

    if not standard_5_1_3_protocol_confirmed:
        raise ValueError(
            "The STEADI 5-minute supine / "
            "1-minute standing / 3-minute standing "
            "orthostatic protocol must be confirmed."
        )

    readings = {
        "supine_sbp_mm_hg":
            _require_number(
                "supine_sbp_mm_hg",
                supine_sbp_mm_hg,
                minimum=0,
                minimum_inclusive=False,
            ),

        "supine_dbp_mm_hg":
            _require_number(
                "supine_dbp_mm_hg",
                supine_dbp_mm_hg,
                minimum=0,
                minimum_inclusive=False,
            ),

        "supine_pulse_bpm":
            _require_number(
                "supine_pulse_bpm",
                supine_pulse_bpm,
                minimum=0,
                minimum_inclusive=False,
            ),

        "standing_1m_sbp_mm_hg":
            _require_number(
                "standing_1m_sbp_mm_hg",
                standing_1m_sbp_mm_hg,
                minimum=0,
                minimum_inclusive=False,
            ),

        "standing_1m_dbp_mm_hg":
            _require_number(
                "standing_1m_dbp_mm_hg",
                standing_1m_dbp_mm_hg,
                minimum=0,
                minimum_inclusive=False,
            ),

        "standing_1m_pulse_bpm":
            _require_number(
                "standing_1m_pulse_bpm",
                standing_1m_pulse_bpm,
                minimum=0,
                minimum_inclusive=False,
            ),

        "standing_3m_sbp_mm_hg":
            _require_number(
                "standing_3m_sbp_mm_hg",
                standing_3m_sbp_mm_hg,
                minimum=0,
                minimum_inclusive=False,
            ),

        "standing_3m_dbp_mm_hg":
            _require_number(
                "standing_3m_dbp_mm_hg",
                standing_3m_dbp_mm_hg,
                minimum=0,
                minimum_inclusive=False,
            ),

        "standing_3m_pulse_bpm":
            _require_number(
                "standing_3m_pulse_bpm",
                standing_3m_pulse_bpm,
                minimum=0,
                minimum_inclusive=False,
            ),
    }

    for prefix in (
        "supine",
        "standing_1m",
        "standing_3m",
    ):
        if (
            readings[
                f"{prefix}_sbp_mm_hg"
            ]
            < readings[
                f"{prefix}_dbp_mm_hg"
            ]
        ):
            raise ValueError(
                f"{prefix} systolic blood pressure "
                "cannot be lower than diastolic "
                "blood pressure."
            )

    systolic_drop_1m = (
        readings["supine_sbp_mm_hg"]
        - readings["standing_1m_sbp_mm_hg"]
    )

    systolic_drop_3m = (
        readings["supine_sbp_mm_hg"]
        - readings["standing_3m_sbp_mm_hg"]
    )

    diastolic_drop_1m = (
        readings["supine_dbp_mm_hg"]
        - readings["standing_1m_dbp_mm_hg"]
    )

    diastolic_drop_3m = (
        readings["supine_dbp_mm_hg"]
        - readings["standing_3m_dbp_mm_hg"]
    )

    maximum_systolic_drop = max(
        systolic_drop_1m,
        systolic_drop_3m,
    )

    maximum_diastolic_drop = max(
        diastolic_drop_1m,
        diastolic_drop_3m,
    )

    systolic_threshold_met = (
        maximum_systolic_drop >= 20
    )

    diastolic_threshold_met = (
        maximum_diastolic_drop >= 10
    )

    abnormal = any(
        (
            systolic_threshold_met,
            diastolic_threshold_met,
            lightheaded_or_dizzy,
        )
    )

    return {
        "tool":
            "steadi_orthostatic_blood_pressure",

        "source_role":
            "complementary_international_guidance",

        **readings,

        "supine_rest_minutes":
            5,

        "standing_measurement_minutes":
            [
                1,
                3,
            ],

        "systolic_drop_1m_mm_hg":
            systolic_drop_1m,

        "systolic_drop_3m_mm_hg":
            systolic_drop_3m,

        "diastolic_drop_1m_mm_hg":
            diastolic_drop_1m,

        "diastolic_drop_3m_mm_hg":
            diastolic_drop_3m,

        "maximum_systolic_drop_mm_hg":
            maximum_systolic_drop,

        "maximum_diastolic_drop_mm_hg":
            maximum_diastolic_drop,

        "systolic_drop_threshold_mm_hg":
            20,

        "diastolic_drop_threshold_mm_hg":
            10,

        "systolic_threshold_met":
            systolic_threshold_met,

        "diastolic_threshold_met":
            diastolic_threshold_met,

        "lightheaded_or_dizzy":
            lightheaded_or_dizzy,

        "abnormal_steadi_orthostatic_assessment":
            abnormal,

        "fall_risk_classification_applied":
            False,

        "national_sus_threshold_applied":
            False,

        "automatic_cross_instrument_inference_applied":
            False,

        "synthetic_cross_instrument_score_applied":
            False,

        "interpretation_pt": (
            (
                "Avaliação ortostática STEADI anormal por "
                "queda pressórica e/ou tontura."
            )
            if abnormal
            else (
                "Os critérios STEADI de anormalidade "
                "ortostática não foram atingidos."
            )
        ),

        "interpretation_en": (
            (
                "STEADI orthostatic assessment is abnormal "
                "because of blood-pressure drop and/or "
                "lightheadedness or dizziness."
            )
            if abnormal
            else (
                "STEADI orthostatic abnormality criteria "
                "were not met."
            )
        ),
    }



def _steadi_metadata(
    *,
    tool_id: str,
    name_pt: str,
    name_en: str,
    description_pt: str,
    description_en: str,
    aliases_pt: list[str],
    aliases_en: list[str],
    source_title: str,
    source_url: str,
    population_pt: str,
    population_en: str,
    limitations_pt: list[str],
    limitations_en: list[str],
) -> dict:
    """Build the shared complementary STEADI metadata contract."""

    return {
        "id":
            tool_id,

        "name_pt":
            name_pt,

        "name_en":
            name_en,

        "description_pt":
            description_pt,

        "description_en":
            description_en,

        "aliases_pt":
            aliases_pt,

        "aliases_en":
            aliases_en,

        "publisher":
            (
                "US Centers for Disease Control "
                "and Prevention / STEADI"
            ),

        "source_title":
            source_title,

        "source_version":
            (
                "CDC STEADI clinical resource "
                "reviewed 2026-09-11"
            ),

        "source_url":
            source_url,

        "source_language":
            "en-US",

        "canonical_language":
            "en-US",

        "translation_status_pt":
            "local_translation",

        "translation_status_en":
            "official_original",

        "translation_disclaimer_required":
            False,

        "translation_disclaimer_source_url":
            None,

        "translation_note_pt": (
            "O texto PT-BR é tradução local informativa. "
            "Os critérios numéricos permanecem os da "
            "fonte CDC STEADI."
        ),

        "translation_note_en": (
            "English terminology follows the CDC STEADI "
            "source; PT-BR is an informative local translation."
        ),

        "population_pt":
            population_pt,

        "population_en":
            population_en,

        "limitations_pt":
            limitations_pt,

        "limitations_en":
            limitations_en,

        "licensing_note_pt": (
            "Implementação lógica própria baseada em "
            "material público do CDC STEADI."
        ),

        "licensing_note_en": (
            "Locally implemented logic based on public "
            "CDC STEADI clinical resources."
        ),

        "clinical_review_date":
            date(2026, 9, 11),

        "offline_capable":
            True,

        "brazil_applicability_status":
            "no_national_variant_identified",

        "brazil_review_date":
            date(2026, 9, 11),

        "brazil_authority":
            "Brazil clinical harmonization review",

        "brazil_source_title":
            (
                "Falls/function Brazil source review — "
                "Caderneta 2026 + IVCF-20"
            ),

        "brazil_source_url":
            None,

        "brazil_document_or_portaria":
            None,

        "brazil_scope_pt": (
            "Avaliação internacional complementar; "
            "não identificada como ponto de corte "
            "nacional genérico do SUS."
        ),

        "brazil_scope_en": (
            "Complementary international assessment; "
            "not identified as a generic national SUS cutoff."
        ),

        "brazil_differs_from_international":
            False,

        "brazil_difference_notes_pt": (
            "A camada nacional brasileira permanece "
            "Caderneta 2026 + IVCF-20. O STEADI deve "
            "permanecer separado e identificado como "
            "orientação internacional complementar."
        ),

        "brazil_difference_notes_en": (
            "The Brazilian national layer remains "
            "Caderneta 2026 + IVCF-20. STEADI must remain "
            "separate and labelled as complementary "
            "international guidance."
        ),

        "final_brazil_review_status":
            "pass",
    }


STEADI_TUG_METADATA = _steadi_metadata(
    tool_id=
        "steadi_timed_up_and_go",

    name_pt=
        "STEADI · Timed Up and Go",

    name_en=
        "STEADI · Timed Up and Go",

    description_pt=(
        "Avaliação complementar de mobilidade STEADI "
        "em percurso de 3 m / 10 ft."
    ),

    description_en=(
        "Complementary STEADI mobility assessment "
        "using a 3-m / 10-ft course."
    ),

    aliases_pt=[
        "TUG",
        "Timed Up and Go",
        "STEADI TUG",
    ],

    aliases_en=[
        "TUG",
        "Timed Up and Go",
        "STEADI TUG",
    ],

    source_title=
        "STEADI Assessment — Timed Up and Go",

    source_url=
        STEADI_TUG_URL,

    population_pt=
        "Pessoa idosa avaliada com o protocolo STEADI TUG.",

    population_en=
        "Older person assessed with the STEADI TUG protocol.",

    limitations_pt=[
        (
            "O limiar >=12 s pertence ao STEADI e "
            "não é um ponto de corte nacional genérico do SUS."
        ),
        (
            "TUG não é equivalente ao item de marcha "
            "de 4 metros do IVCF-20."
        ),
        (
            "Não combinar automaticamente o resultado "
            "com Caderneta, IVCF-20 ou outros testes STEADI."
        ),
    ],

    limitations_en=[
        (
            "The >=12-second threshold belongs to STEADI "
            "and is not a generic national SUS cutoff."
        ),
        (
            "TUG is not equivalent to the IVCF-20 "
            "4-metre gait item."
        ),
        (
            "Do not automatically combine the result with "
            "Caderneta, IVCF-20 or other STEADI tests."
        ),
    ],
)


STEADI_CHAIR_STAND_METADATA = _steadi_metadata(
    tool_id=
        "steadi_30_second_chair_stand",

    name_pt=
        "STEADI · Teste de sentar e levantar em 30 segundos",

    name_en=
        "STEADI · 30-Second Chair Stand",

    description_pt=(
        "Avaliação complementar STEADI de força e "
        "resistência dos membros inferiores."
    ),

    description_en=(
        "Complementary STEADI assessment of lower-limb "
        "strength and endurance."
    ),

    aliases_pt=[
        "30-Second Chair Stand",
        "Chair Stand",
        "STEADI Chair Stand",
    ],

    aliases_en=[
        "30-Second Chair Stand",
        "Chair Stand",
        "STEADI Chair Stand",
    ],

    source_title=
        "STEADI Assessment — 30-Second Chair Stand",

    source_url=
        STEADI_CHAIR_STAND_URL,

    population_pt=(
        "Tabela de referência STEADI publicada para "
        "idades de 60 a 94 anos."
    ),

    population_en=(
        "Published STEADI reference table for ages "
        "60 through 94 years."
    ),

    limitations_pt=[
        (
            "Não extrapolar pontos de corte etários/sexo "
            "além de 94 anos."
        ),
        (
            "Valor exatamente igual ao limiar não é "
            "classificado como abaixo da média."
        ),
        (
            "Se os braços forem necessários para levantar, "
            "o teste é interrompido e registra-se zero."
        ),
        (
            "Não combinar automaticamente com outros "
            "instrumentos de quedas."
        ),
    ],

    limitations_en=[
        (
            "Do not extrapolate age/sex cutoffs "
            "beyond age 94."
        ),
        (
            "A value exactly equal to the threshold "
            "is not classified as below average."
        ),
        (
            "If the arms are required to stand, stop "
            "the test and record zero."
        ),
        (
            "Do not automatically combine with other "
            "falls instruments."
        ),
    ],
)


STEADI_FOUR_STAGE_METADATA = _steadi_metadata(
    tool_id=
        "steadi_four_stage_balance",

    name_pt=
        "STEADI · Teste de equilíbrio em 4 estágios",

    name_en=
        "STEADI · 4-Stage Balance Test",

    description_pt=(
        "Avaliação complementar STEADI de equilíbrio "
        "estático em quatro posições progressivas."
    ),

    description_en=(
        "Complementary STEADI static-balance assessment "
        "using four progressive positions."
    ),

    aliases_pt=[
        "4-Stage Balance",
        "teste de equilíbrio em 4 estágios",
        "STEADI Balance",
    ],

    aliases_en=[
        "4-Stage Balance",
        "4-Stage Balance Test",
        "STEADI Balance",
    ],

    source_title=
        "STEADI Assessment — 4-Stage Balance Test",

    source_url=
        STEADI_FOUR_STAGE_URL,

    population_pt=
        "Pessoa idosa submetida ao protocolo STEADI de equilíbrio.",

    population_en=
        "Older person assessed with the STEADI balance protocol.",

    limitations_pt=[
        (
            "O teste progride apenas após manter a posição "
            "atual por 10 segundos."
        ),
        (
            "Não utilizar dispositivo de auxílio durante "
            "o teste de equilíbrio em 4 estágios."
        ),
        (
            "Tandem <10 s é critério STEADI, não ponto "
            "de corte nacional genérico do SUS."
        ),
        (
            "Não importar a regra de bengala/andador do TUG."
        ),
    ],

    limitations_en=[
        (
            "Progress only after the current position "
            "is held for 10 seconds."
        ),
        (
            "Do not use an assistive device during "
            "the 4-Stage Balance Test."
        ),
        (
            "Tandem <10 seconds is a STEADI criterion, "
            "not a generic national SUS cutoff."
        ),
        (
            "Do not import the TUG walking-aid rule."
        ),
    ],
)


STEADI_ORTHOSTATIC_BP_METADATA = _steadi_metadata(
    tool_id=
        "steadi_orthostatic_blood_pressure",

    name_pt=
        "STEADI · Pressão arterial ortostática",

    name_en=
        "STEADI · Measuring Orthostatic Blood Pressure",

    description_pt=(
        "Avaliação complementar STEADI com 5 minutos "
        "em decúbito e medidas em pé aos 1 e 3 minutos."
    ),

    description_en=(
        "Complementary STEADI assessment using 5 minutes "
        "supine and standing measurements at 1 and 3 minutes."
    ),

    aliases_pt=[
        "pressão ortostática",
        "hipotensão ortostática",
        "STEADI orthostatic BP",
    ],

    aliases_en=[
        "orthostatic blood pressure",
        "orthostatic hypotension",
        "STEADI orthostatic BP",
    ],

    source_title=
        "STEADI Assessment — Measuring Orthostatic Blood Pressure",

    source_url=
        STEADI_ORTHOSTATIC_BP_URL,

    population_pt=(
        "Pessoa idosa submetida ao protocolo ortostático STEADI."
    ),

    population_en=(
        "Older person assessed with the STEADI orthostatic protocol."
    ),

    limitations_pt=[
        (
            "A interpretação 20/10 mmHg ou sintomas exige "
            "confirmação do protocolo STEADI 5/1/3 minutos."
        ),
        (
            "A Caderneta 2026 registra posições pressóricas, "
            "mas não define este protocolo numérico completo."
        ),
        (
            "Nenhum limiar de pulso é inventado pelo aplicativo."
        ),
        (
            "O resultado ortostático não é convertido "
            "automaticamente em escore de risco de quedas."
        ),
    ],

    limitations_en=[
        (
            "The 20/10-mmHg-or-symptom interpretation requires "
            "confirmation of the STEADI 5/1/3-minute protocol."
        ),
        (
            "The 2026 Brazilian Caderneta records BP positions "
            "but does not define this complete numeric protocol."
        ),
        (
            "The application does not invent a pulse threshold."
        ),
        (
            "The orthostatic result is not automatically "
            "converted into a falls-risk score."
        ),
    ],
)
