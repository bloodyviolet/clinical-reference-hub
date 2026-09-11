"""WHO paediatric growth z-scores with Brazilian SISVAN interpretation.

Numerical references
--------------------
WHO Child Growth Standards 2006:
- weight-for-age
- length/height-for-age
- BMI-for-age
- head circumference-for-age
- weight-for-length
- weight-for-height

WHO Reference 2007:
- weight-for-age
- height-for-age
- BMI-for-age

Brazilian clinical labels are loaded separately from the Ministry of
Health / SISVAN policy file and never alter the WHO LMS calculations.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Literal


DAYS_PER_MONTH = 30.4375

REF_DIR = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "reference"
    / "who-growth"
)

Sex = Literal[
    "male",
    "female",
]

AgeUnit = Literal[
    "days",
    "months",
]

AgeBasis = Literal[
    "chronological",
    "corrected",
]

MeasurementPosition = Literal[
    "length",
    "height",
]


WHO2006_COMMIT = (
    "b776d8a12b1c97369c748b561159fd2ec4f4db58"
)

WHO2007_COMMIT = (
    "7cfcdb39026e9a55de55732bc3cf14c82261bcf7"
)


@lru_cache(maxsize=None)
def _load_json(
    filename: str,
):
    return json.loads(
        (
            REF_DIR
            / filename
        ).read_text(
            encoding="utf-8"
        )
    )


@lru_cache(maxsize=None)
def _age_index(
    filename: str,
):
    return {
        (
            int(row["sex"]),
            int(row["age"]),
        ):
            row

        for row in _load_json(
            filename
        )
    }


@lru_cache(maxsize=None)
def _size_index(
    filename: str,
    field: str,
):
    return {
        (
            int(row["sex"]),
            round(
                float(row[field]),
                1,
            ),
        ):
            row

        for row in _load_json(
            filename
        )
    }


def _sex_code(
    sex: Sex | str,
) -> int:
    value = str(sex).strip().lower()

    if value in {
        "male",
        "m",
        "1",
    }:
        return 1

    if value in {
        "female",
        "f",
        "2",
    }:
        return 2

    raise ValueError(
        "sex must be male or female."
    )


def _round_half_up(
    value: float,
) -> int:
    if value < 0:
        raise ValueError(
            "age cannot be negative."
        )

    base = math.floor(value)

    if (
        value - base
        >= 0.5
    ):
        return base + 1

    return base


def _prepare_age(
    *,
    age_value: float,
    age_unit: AgeUnit,
) -> tuple[
    int,
    float,
]:
    if age_value < 0:
        raise ValueError(
            "age_value cannot be negative."
        )

    if age_unit == "days":
        age_days = _round_half_up(
            age_value
        )

        age_months = (
            age_value
            / DAYS_PER_MONTH
        )

    elif age_unit == "months":
        age_months = age_value

        age_days = _round_half_up(
            age_value
            * DAYS_PER_MONTH
        )

    else:
        raise ValueError(
            "age_unit must be days or months."
        )

    return (
        age_days,
        age_months,
    )


def _basic_lms_z(
    *,
    value: float,
    l: float,
    m: float,
    s: float,
) -> float:
    if value <= 0:
        raise ValueError(
            "growth measurements must be "
            "greater than zero."
        )

    if math.isclose(
        l,
        0.0,
        abs_tol=1e-12,
    ):
        return (
            math.log(
                value / m
            )
            / s
        )

    return (
        (
            (value / m) ** l
            - 1.0
        )
        / (
            s * l
        )
    )


def _sd_value(
    *,
    sd: float,
    l: float,
    m: float,
    s: float,
) -> float:
    if math.isclose(
        l,
        0.0,
        abs_tol=1e-12,
    ):
        return (
            m
            * math.exp(
                s * sd
            )
        )

    return (
        m
        * (
            1.0
            + l * s * sd
        )
        ** (
            1.0 / l
        )
    )


def _adjusted_lms_z(
    *,
    value: float,
    l: float,
    m: float,
    s: float,
) -> float:
    z = _basic_lms_z(
        value=value,
        l=l,
        m=m,
        s=s,
    )

    if z > 3.0:
        sd3 = _sd_value(
            sd=3.0,
            l=l,
            m=m,
            s=s,
        )

        sd2 = _sd_value(
            sd=2.0,
            l=l,
            m=m,
            s=s,
        )

        return (
            3.0
            + (
                value - sd3
            )
            / (
                sd3 - sd2
            )
        )

    if z < -3.0:
        sd_neg3 = _sd_value(
            sd=-3.0,
            l=l,
            m=m,
            s=s,
        )

        sd_neg2 = _sd_value(
            sd=-2.0,
            l=l,
            m=m,
            s=s,
        )

        return (
            -3.0
            + (
                value - sd_neg3
            )
            / (
                sd_neg2 - sd_neg3
            )
        )

    return z


def _percentile(
    raw_z: float,
) -> float | None:
    # WHO Anthro convention:
    # do not display percentile beyond +/-3 SD.
    if (
        raw_z < -3.0
        or raw_z > 3.0
    ):
        return None

    result = (
        0.5
        * (
            1.0
            + math.erf(
                raw_z
                / math.sqrt(2.0)
            )
        )
        * 100.0
    )

    return round(
        result,
        2,
    )


def _row_lms(
    row: dict,
) -> tuple[
    float,
    float,
    float,
]:
    return (
        float(row["l"]),
        float(row["m"]),
        float(row["s"]),
    )


def _who2006_age_lms(
    *,
    filename: str,
    sex_code: int,
    age_days: int,
) -> tuple[
    float,
    float,
    float,
] | None:
    row = _age_index(
        filename
    ).get(
        (
            sex_code,
            age_days,
        )
    )

    if row is None:
        return None

    return _row_lms(row)


def _who2007_interpolated_lms(
    *,
    filename: str,
    sex_code: int,
    age_months: float,
    upper_age_exclusive: float,
) -> tuple[
    float,
    float,
    float,
] | None:
    if not (
        60.0
        <= age_months
        < upper_age_exclusive
    ):
        return None

    low_age = math.trunc(
        age_months
    )

    upper_age = math.trunc(
        age_months + 1.0
    )

    diff = (
        age_months
        - low_age
    )

    index = _age_index(
        filename
    )

    low = index.get(
        (
            sex_code,
            low_age,
        )
    )

    upper = index.get(
        (
            sex_code,
            upper_age,
        )
    )

    if low is None:
        return None

    if diff <= 0:
        return _row_lms(low)

    if upper is None:
        return None

    result = []

    for field in (
        "l",
        "m",
        "s",
    ):
        low_value = float(
            low[field]
        )

        upper_value = float(
            upper[field]
        )

        result.append(
            low_value
            + diff
            * (
                upper_value
                - low_value
            )
        )

    return tuple(result)


def _who2006_size_lms(
    *,
    filename: str,
    field: str,
    sex_code: int,
    size_cm: float,
) -> tuple[
    float,
    float,
    float,
] | None:
    low_size = (
        math.trunc(
            size_cm * 10.0
        )
        / 10.0
    )

    upper_size = (
        math.trunc(
            size_cm * 10.0
            + 1.0
        )
        / 10.0
    )

    diff = (
        size_cm - low_size
    ) / 0.1

    index = _size_index(
        filename,
        field,
    )

    low = index.get(
        (
            sex_code,
            round(
                low_size,
                1,
            ),
        )
    )

    if low is None:
        return None

    if diff <= 1e-12:
        return _row_lms(low)

    upper = index.get(
        (
            sex_code,
            round(
                upper_size,
                1,
            ),
        )
    )

    if upper is None:
        return None

    result = []

    for name in (
        "l",
        "m",
        "s",
    ):
        result.append(
            float(low[name])
            + diff
            * (
                float(upper[name])
                - float(low[name])
            )
        )

    return tuple(result)


def _classify_from_bands(
    *,
    z_score: float,
    bands: list[dict],
) -> dict | None:
    for band in bands:
        valid = True

        if "z_min" in band:
            minimum = float(
                band["z_min"]
            )

            if band.get(
                "z_min_inclusive",
                False,
            ):
                valid &= (
                    z_score >= minimum
                )
            else:
                valid &= (
                    z_score > minimum
                )

        if "z_max" in band:
            maximum = float(
                band["z_max"]
            )

            if band.get(
                "z_max_inclusive",
                False,
            ):
                valid &= (
                    z_score <= maximum
                )
            else:
                valid &= (
                    z_score < maximum
                )

        if valid:
            return {
                "code":
                    band["code"],

                "label_pt":
                    band["label_pt"],

                "label_en":
                    band["label_en"],
            }

    return None


def _brazil_bands(
    *,
    indicator: str,
    age_months: float,
) -> list[dict] | None:
    policy = _load_json(
        "BRAZIL_SISVAN.json"
    )

    classifications = policy[
        "classifications"
    ]

    if indicator == (
        "head_circumference_for_age"
    ):
        return policy[
            "head_circumference"
        ][
            "classification"
        ]

    if age_months < 60.0:
        group = classifications[
            "under_5"
        ]

        if indicator == (
            "weight_for_age"
        ):
            return group[
                "weight_for_age"
            ]

        if indicator in {
            "weight_for_length_height",
            "bmi_for_age",
        }:
            return group[
                "weight_for_length_height"
            ]

        if indicator == (
            "length_height_for_age"
        ):
            return group[
                "length_height_for_age"
            ]

        return None

    if age_months < 120.0:
        group = classifications[
            "age_5_to_under_10"
        ]

        if indicator == (
            "weight_for_age"
        ):
            return classifications[
                "under_5"
            ][
                "weight_for_age"
            ]

        if indicator == (
            "bmi_for_age"
        ):
            return group[
                "bmi_for_age"
            ]

        if indicator == (
            "length_height_for_age"
        ):
            return classifications[
                "under_5"
            ][
                "length_height_for_age"
            ]

        return None

    group = classifications[
        "age_10_to_under_20"
    ]

    if indicator == (
        "bmi_for_age"
    ):
        return classifications[
            "age_5_to_under_10"
        ][
            "bmi_for_age"
        ]

    if indicator == (
        "length_height_for_age"
    ):
        return classifications[
            "under_5"
        ][
            "length_height_for_age"
        ]

    return None


def _brazil_classification(
    *,
    indicator: str,
    age_months: float,
    z_score: float,
) -> dict | None:
    bands = _brazil_bands(
        indicator=indicator,
        age_months=age_months,
    )

    if bands is None:
        return None

    return _classify_from_bands(
        z_score=z_score,
        bands=bands,
    )



def _who_label(
    code: str,
    label_pt: str,
    label_en: str,
) -> dict:
    return {
        "code":
            code,
        "label_pt":
            label_pt,
        "label_en":
            label_en,
    }


def _who_classification(
    *,
    indicator: str,
    age_months: float,
    z_score: float,
) -> dict | None:
    """WHO named anthropometric interpretation bands.

    This is deliberately separate from SISVAN. Threshold comparisons
    use the WHO-package z-score rounded to two decimals, matching the
    displayed/flagging convention already used by this engine.
    """

    if indicator == (
        "head_circumference_for_age"
    ):
        return None

    if indicator == (
        "length_height_for_age"
    ):
        if z_score < -3.0:
            return _who_label(
                "severely_stunted",
                "Déficit grave de estatura",
                "Severely stunted",
            )

        if z_score < -2.0:
            return _who_label(
                "stunted",
                "Déficit de estatura",
                "Stunted",
            )

        return None

    if indicator == (
        "weight_for_age"
    ):
        if z_score < -3.0:
            return _who_label(
                "severely_underweight",
                "Peso muito baixo para a idade",
                "Severely underweight",
            )

        if z_score < -2.0:
            return _who_label(
                "underweight",
                "Baixo peso para a idade",
                "Underweight",
            )

        return None

    if (
        age_months < 60.0
        and indicator in {
            "weight_for_length_height",
            "bmi_for_age",
        }
    ):
        if z_score < -3.0:
            return _who_label(
                "severely_wasted",
                "Magreza grave",
                "Severely wasted",
            )

        if z_score < -2.0:
            return _who_label(
                "wasted",
                "Magreza",
                "Wasted",
            )

        if z_score > 3.0:
            return _who_label(
                "obesity",
                "Obesidade",
                "Obesity",
            )

        if z_score > 2.0:
            return _who_label(
                "overweight",
                "Sobrepeso",
                "Overweight",
            )

        if z_score > 1.0:
            return _who_label(
                "possible_risk_overweight",
                "Possível risco de sobrepeso",
                "Possible risk of overweight",
            )

        return None

    if (
        age_months >= 60.0
        and indicator == "bmi_for_age"
    ):
        if z_score < -3.0:
            return _who_label(
                "severe_thinness",
                "Magreza acentuada",
                "Severe thinness",
            )

        if z_score < -2.0:
            return _who_label(
                "thinness",
                "Magreza",
                "Thinness",
            )

        if z_score > 2.0:
            return _who_label(
                "obesity",
                "Obesidade",
                "Obesity",
            )

        if z_score > 1.0:
            return _who_label(
                "overweight",
                "Sobrepeso",
                "Overweight",
            )

        return None

    return None


def _plausibility(
    *,
    indicator: str,
    z_score: float,
) -> tuple[
    bool,
    str,
]:
    if indicator == (
        "weight_for_age"
    ):
        flagged = (
            z_score < -6.0
            or z_score > 5.0
        )

        return (
            flagged,
            "-6 <= z <= +5",
        )

    if indicator == (
        "length_height_for_age"
    ):
        return (
            abs(z_score) > 6.0,
            "-6 <= z <= +6",
        )

    return (
        abs(z_score) > 5.0,
        "-5 <= z <= +5",
    )


def _result(
    *,
    indicator: str,
    raw_z: float,
    reference_standard: str,
    reference_table: str,
    age_months: float,
) -> dict:
    # WHO packages expose z-scores rounded to 2 decimals;
    # flags are applied to the rounded z-score.
    z_score = round(
        raw_z,
        2,
    )

    flag, range_text = (
        _plausibility(
            indicator=indicator,
            z_score=z_score,
        )
    )

    return {
        "indicator":
            indicator,

        "z_score":
            z_score,

        "percentile":
            _percentile(
                raw_z
            ),

        "percentile_available":
            (
                -3.0
                <= raw_z
                <= 3.0
            ),

        "reference_standard":
            reference_standard,

        "reference_table":
            reference_table,

        "classification_who":
            _who_classification(
                indicator=indicator,
                age_months=age_months,
                z_score=z_score,
            ),

        "classification_br":
            _brazil_classification(
                indicator=indicator,
                age_months=age_months,
                z_score=z_score,
            ),

        "classification_z_basis":
            (
                "WHO z-score rounded "
                "to 2 decimals"
            ),

        "plausibility_flag":
            flag,

        "who_plausibility_range":
            range_text,
    }


def calculate_who_growth(
    *,
    sex: Sex | str,
    age_value: float,
    age_unit: AgeUnit,
    age_basis: AgeBasis = "chronological",
    weight_kg: float | None = None,
    length_height_cm: float | None = None,
    measurement_position: MeasurementPosition | None = None,
    head_circumference_cm: float | None = None,
    oedema: bool = False,
) -> dict:
    """Calculate all supported WHO growth indicators."""

    sex_code = _sex_code(
        sex
    )

    age_days, age_months = (
        _prepare_age(
            age_value=age_value,
            age_unit=age_unit,
        )
    )

    if age_basis not in {
        "chronological",
        "corrected",
    }:
        raise ValueError(
            "age_basis must be chronological "
            "or corrected."
        )

    if (
        weight_kg is None
        and length_height_cm is None
        and head_circumference_cm is None
    ):
        raise ValueError(
            "At least one anthropometric measurement "
            "must be supplied."
        )

    if (
        weight_kg is not None
        and weight_kg <= 0
    ):
        raise ValueError(
            "weight_kg must be greater "
            "than zero."
        )

    if (
        length_height_cm is not None
        and length_height_cm <= 0
    ):
        raise ValueError(
            "length_height_cm must be "
            "greater than zero."
        )

    if (
        head_circumference_cm is not None
        and head_circumference_cm <= 0
    ):
        raise ValueError(
            "head_circumference_cm must "
            "be greater than zero."
        )

    if (
        length_height_cm is not None
        and measurement_position
        is None
    ):
        raise ValueError(
            "measurement_position is required "
            "when length_height_cm is supplied."
        )

    if (
        measurement_position
        not in {
            None,
            "length",
            "height",
        }
    ):
        raise ValueError(
            "measurement_position must be "
            "length or height."
        )

    if (
        age_months >= 60.0
        and length_height_cm is not None
        and measurement_position != "height"
    ):
        raise ValueError(
            "WHO 2007 requires standing height "
            "for children aged 5 years and older."
        )

    effective_lenhei = (
        length_height_cm
    )

    measurement_adjustment = 0.0

    measurement_warning = None

    effective_position = (
        measurement_position
    )

    if (
        age_months < 60.0
        and length_height_cm
        is not None
    ):
        if (
            age_months < 9.0
            and measurement_position
            == "height"
        ):
            # WHO anthro v1.1.0 marks this as an
            # incorrect measurement position and
            # does not apply the 0.7-cm conversion.
            measurement_warning = (
                "height_under_9_months"
            )

        elif (
            age_days < 731
            and measurement_position
            == "height"
        ):
            effective_lenhei = (
                length_height_cm
                + 0.7
            )

            measurement_adjustment = 0.7

            effective_position = "length"

        elif (
            age_days >= 731
            and measurement_position
            == "length"
        ):
            effective_lenhei = (
                length_height_cm
                - 0.7
            )

            measurement_adjustment = -0.7

            effective_position = "height"

    bmi = None

    if (
        weight_kg is not None
        and effective_lenhei
        is not None
    ):
        bmi = (
            weight_kg
            / (
                effective_lenhei
                / 100.0
            )
            ** 2
        )

    indicators: dict[
        str,
        dict | None,
    ] = {
        "weight_for_age":
            None,

        "length_height_for_age":
            None,

        "weight_for_length_height":
            None,

        "bmi_for_age":
            None,

        "head_circumference_for_age":
            None,
    }

    warnings_pt: list[str] = []
    warnings_en: list[str] = []

    if age_basis == "corrected":
        warnings_pt.append(
            "Foi utilizada idade corrigida. "
            "A idade cronológica deve permanecer "
            "registrada separadamente."
        )

        warnings_en.append(
            "Corrected age was used. "
            "Chronological age should remain "
            "recorded separately."
        )

    if measurement_warning == (
        "height_under_9_months"
    ):
        warnings_pt.append(
            "Altura em pé informada para criança "
            "com menos de 9 meses: posição de "
            "mensuração inadequada segundo o "
            "controle de qualidade do WHO Anthro."
        )

        warnings_en.append(
            "Standing height was supplied for a "
            "child younger than 9 months: this is "
            "an incorrect measurement position "
            "under WHO Anthro quality control."
        )

    if oedema:
        warnings_pt.append(
            "Edema informado: indicadores "
            "dependentes de peso não foram "
            "calculados."
        )

        warnings_en.append(
            "Oedema was reported: weight-related "
            "indicators were not calculated."
        )

    if age_months < 60.0:
        reference = (
            "WHO Child Growth Standards 2006"
        )

        if (
            weight_kg is not None
            and not oedema
        ):
            lms = _who2006_age_lms(
                filename=(
                    "who2006_weight_for_age.json"
                ),
                sex_code=sex_code,
                age_days=age_days,
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "weight_for_age"
                ] = _result(
                    indicator=(
                        "weight_for_age"
                    ),
                    raw_z=_adjusted_lms_z(
                        value=weight_kg,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2006_weight_for_age.json"
                    ),
                    age_months=age_months,
                )

        if effective_lenhei is not None:
            lms = _who2006_age_lms(
                filename=(
                    "who2006_length_height_for_age.json"
                ),
                sex_code=sex_code,
                age_days=age_days,
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "length_height_for_age"
                ] = _result(
                    indicator=(
                        "length_height_for_age"
                    ),
                    raw_z=_basic_lms_z(
                        value=effective_lenhei,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2006_length_height_for_age.json"
                    ),
                    age_months=age_months,
                )

        if (
            bmi is not None
            and not oedema
        ):
            lms = _who2006_age_lms(
                filename=(
                    "who2006_bmi_for_age.json"
                ),
                sex_code=sex_code,
                age_days=age_days,
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "bmi_for_age"
                ] = _result(
                    indicator="bmi_for_age",
                    raw_z=_adjusted_lms_z(
                        value=bmi,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2006_bmi_for_age.json"
                    ),
                    age_months=age_months,
                )

        if (
            effective_lenhei is not None
            and weight_kg is not None
            and not oedema
        ):
            if age_days < 731:
                filename = (
                    "who2006_weight_for_length.json"
                )

                size_field = "length"

                in_domain = (
                    45.0
                    <= effective_lenhei
                    <= 110.0
                )

            else:
                filename = (
                    "who2006_weight_for_height.json"
                )

                size_field = "height"

                in_domain = (
                    65.0
                    <= effective_lenhei
                    <= 120.0
                )

            if in_domain:
                lms = (
                    _who2006_size_lms(
                        filename=filename,
                        field=size_field,
                        sex_code=sex_code,
                        size_cm=effective_lenhei,
                    )
                )

                if lms is not None:
                    l, m, s = lms

                    indicators[
                        "weight_for_length_height"
                    ] = _result(
                        indicator=(
                            "weight_for_length_height"
                        ),
                        raw_z=_adjusted_lms_z(
                            value=weight_kg,
                            l=l,
                            m=m,
                            s=s,
                        ),
                        reference_standard=reference,
                        reference_table=filename,
                        age_months=age_months,
                    )

        if (
            head_circumference_cm
            is not None
        ):
            lms = _who2006_age_lms(
                filename=(
                    "who2006_head_circumference_for_age.json"
                ),
                sex_code=sex_code,
                age_days=age_days,
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "head_circumference_for_age"
                ] = _result(
                    indicator=(
                        "head_circumference_for_age"
                    ),
                    raw_z=_basic_lms_z(
                        value=head_circumference_cm,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2006_head_circumference_for_age.json"
                    ),
                    age_months=age_months,
                )

    elif age_months < 229.0:
        reference = (
            "WHO Growth Reference 2007"
        )

        if (
            weight_kg is not None
            and not oedema
            and age_months < 121.0
        ):
            lms = (
                _who2007_interpolated_lms(
                    filename=(
                        "who2007_weight_for_age.json"
                    ),
                    sex_code=sex_code,
                    age_months=age_months,
                    upper_age_exclusive=121.0,
                )
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "weight_for_age"
                ] = _result(
                    indicator=(
                        "weight_for_age"
                    ),
                    raw_z=_adjusted_lms_z(
                        value=weight_kg,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2007_weight_for_age.json"
                    ),
                    age_months=age_months,
                )

        if effective_lenhei is not None:
            lms = (
                _who2007_interpolated_lms(
                    filename=(
                        "who2007_height_for_age.json"
                    ),
                    sex_code=sex_code,
                    age_months=age_months,
                    upper_age_exclusive=229.0,
                )
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "length_height_for_age"
                ] = _result(
                    indicator=(
                        "length_height_for_age"
                    ),
                    raw_z=_basic_lms_z(
                        value=effective_lenhei,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2007_height_for_age.json"
                    ),
                    age_months=age_months,
                )

        if (
            bmi is not None
            and not oedema
        ):
            lms = (
                _who2007_interpolated_lms(
                    filename=(
                        "who2007_bmi_for_age.json"
                    ),
                    sex_code=sex_code,
                    age_months=age_months,
                    upper_age_exclusive=229.0,
                )
            )

            if lms is not None:
                l, m, s = lms

                indicators[
                    "bmi_for_age"
                ] = _result(
                    indicator="bmi_for_age",
                    raw_z=_adjusted_lms_z(
                        value=bmi,
                        l=l,
                        m=m,
                        s=s,
                    ),
                    reference_standard=reference,
                    reference_table=(
                        "who2007_bmi_for_age.json"
                    ),
                    age_months=age_months,
                )

        if age_months >= 120.0:
            warnings_pt.append(
                "Peso-para-idade não deve ser usado "
                "para classificação SISVAN a partir "
                "dos 10 anos."
            )

            warnings_en.append(
                "Weight-for-age should not be used "
                "for SISVAN classification from age "
                "10 years onward."
            )

    else:
        warnings_pt.append(
            "Idade fora do domínio nativo da "
            "referência WHO 2007 (<229 meses); "
            "nenhum LMS foi extrapolado."
        )

        warnings_en.append(
            "Age is outside the native WHO 2007 "
            "reference domain (<229 months); no "
            "LMS value was extrapolated."
        )

    head_result = indicators[
        "head_circumference_for_age"
    ]

    if head_result is not None:
        head_result[
            "brazil_routine_monitoring_applicable"
        ] = (
            age_months <= 24.0
        )

        if age_months > 24.0:
            warnings_pt.append(
                "A referência WHO para perímetro "
                "cefálico continua disponível, mas "
                "o acompanhamento rotineiro brasileiro "
                "é priorizado nos primeiros 24 meses."
            )

            warnings_en.append(
                "The WHO head-circumference reference "
                "remains available, but Brazilian "
                "routine monitoring is prioritised in "
                "the first 24 months."
            )

    return {
        "tool":
            "who_pediatric_growth",

        "sex":
            (
                "male"
                if sex_code == 1
                else "female"
            ),

        "age_input_value":
            age_value,

        "age_input_unit":
            age_unit,

        "age_basis":
            age_basis,

        "who_age_days":
            age_days,

        "who_age_months":
            round(
                age_months,
                4,
            ),

        "oedema":
            bool(oedema),

        "measurement_position_input":
            measurement_position,

        "measurement_position_effective":
            effective_position,

        "measurement_adjustment_cm":
            round(
                measurement_adjustment,
                1,
            ),

        "length_height_input_cm":
            (
                round(
                    length_height_cm,
                    2,
                )
                if length_height_cm
                is not None
                else None
            ),

        "length_height_effective_cm":
            (
                round(
                    effective_lenhei,
                    2,
                )
                if effective_lenhei
                is not None
                else None
            ),

        "bmi_kg_m2":
            (
                round(
                    bmi,
                    4,
                )
                if bmi is not None
                else None
            ),

        "indicators":
            indicators,

        "warnings_pt":
            warnings_pt,

        "warnings_en":
            warnings_en,

        "provenance": {
            "who2006_commit":
                WHO2006_COMMIT,

            "who2007_commit":
                WHO2007_COMMIT,

            "brazil_policy":
                (
                    "Ministério da Saúde / SISVAN"
                ),
        },
    }



GROWTH_METADATA = {
    "id":
        "who-pediatric-growth",

    "name_pt":
        "Crescimento pediátrico WHO / SISVAN",

    "name_en":
        "WHO / SISVAN paediatric growth",

    "description_pt": (
        "Escores-z e percentis WHO para peso-idade, "
        "comprimento/estatura-idade, peso-comprimento/"
        "estatura, IMC-idade e perímetro cefálico-idade, "
        "com classificação brasileira SISVAN separada."
    ),

    "description_en": (
        "WHO z-scores and percentiles for weight-for-age, "
        "length/height-for-age, weight-for-length/height, "
        "BMI-for-age and head-circumference-for-age, with "
        "a separate Brazilian SISVAN classification layer."
    ),

    "aliases_pt": [
        "curva de crescimento",
        "WHO",
        "OMS",
        "SISVAN",
        "escore-z",
        "percentil",
        "peso por idade",
        "estatura por idade",
        "IMC por idade",
        "perímetro cefálico",
    ],

    "aliases_en": [
        "growth chart",
        "WHO growth",
        "z-score",
        "percentile",
        "weight for age",
        "height for age",
        "BMI for age",
        "head circumference",
    ],

    "publisher": (
        "World Health Organization; "
        "Ministério da Saúde do Brasil / SISVAN"
    ),

    "source_title": (
        "WHO Child Growth Standards 2006 and "
        "WHO Growth Reference 2007"
    ),

    "source_version": (
        "WHO anthro 1.1.0 / "
        "anthroplus 1.1.0; "
        "upstream heads verified 2026-09-11"
    ),

    "source_url":
        "https://www.who.int/tools/child-growth-standards",

    "source_language":
        "en",

    "canonical_language":
        "mixed: WHO numerical reference + pt-BR SISVAN",

    "translation_status_pt":
        "local_translation",

    "translation_status_en":
        "informative_translation",

    "translation_disclaimer_required":
        False,

    "translation_disclaimer_source_url":
        None,

    "translation_note_pt": (
        "Os cálculos LMS WHO são independentes de idioma. "
        "Os rótulos SISVAN em PT-BR são mantidos como "
        "camada brasileira separada."
    ),

    "translation_note_en": (
        "WHO LMS calculations are language-neutral. "
        "Brazilian SISVAN labels are retained as a "
        "separate national interpretation layer."
    ),

    "population_pt": (
        "Crianças e adolescentes dentro dos domínios "
        "etários definidos pelas referências WHO 2006/2007."
    ),

    "population_en": (
        "Children and adolescents within the age domains "
        "defined by the WHO 2006/2007 references."
    ),

    "limitations_pt": [
        (
            "Não extrapola parâmetros LMS WHO 2007 "
            "além de 229 meses."
        ),
        (
            "Peso-para-idade WHO 2007 é limitado "
            "a idade inferior a 121 meses."
        ),
        (
            "Idade corrigida de prematuridade deve ser "
            "explicitamente identificada; não é inferida."
        ),
        (
            "Edema suprime indicadores dependentes de peso."
        ),
        (
            "Posição de comprimento/estatura e correção "
            "de 0,7 cm seguem regras do WHO Anthro."
        ),
        (
            "Classificação WHO e classificação brasileira "
            "SISVAN são apresentadas separadamente."
        ),
    ],

    "limitations_en": [
        (
            "WHO 2007 LMS parameters are not extrapolated "
            "beyond 229 months."
        ),
        (
            "WHO 2007 weight-for-age is limited to "
            "age below 121 months."
        ),
        (
            "Corrected age for prematurity must be explicitly "
            "identified and is not inferred."
        ),
        (
            "Oedema suppresses weight-related indicators."
        ),
        (
            "Length/height position and the 0.7 cm adjustment "
            "follow WHO Anthro rules."
        ),
        (
            "WHO and Brazilian SISVAN classifications are "
            "reported separately."
        ),
    ],

    "licensing_note_pt": (
        "As tabelas normalizadas derivam das fontes mantidas "
        "pela WHO anthro/anthroplus. Atribuição, commits, "
        "licenças declaradas e termos revisados estão documentados "
        "em assets/reference/who-growth/NOTICE.txt e "
        "docs/WHO_GROWTH_ATTRIBUTION.md."
    ),

    "licensing_note_en": (
        "Normalised tables derive from WHO-maintained "
        "anthro/anthroplus sources. Attribution, pinned commits, "
        "declared licences and reviewed terms are documented in "
        "assets/reference/who-growth/NOTICE.txt and "
        "docs/WHO_GROWTH_ATTRIBUTION.md."
    ),

    "clinical_review_date":
        date(2026, 9, 11),

    "offline_capable":
        True,
}
