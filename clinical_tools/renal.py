"""Adult renal calculation and classification tools.

Implemented sources:

- CKD-EPI 2021 race-free creatinine equation.
- KDIGO 2024 CKD GFR/albuminuria classification.
- KDIGO 2012 AKI definition and staging.

The 2026 KDIGO AKI/AKD public-review draft is intentionally not
used as production criteria.
"""

from __future__ import annotations

from datetime import date
import math
from typing import Literal


Sex = Literal[
    "female",
    "male",
]

CreatinineUnit = Literal[
    "mg/dL",
    "umol/L",
]

ACRUnit = Literal[
    "mg/g",
    "mg/mmol",
]


NKF_EGFR_URL = (
    "https://www.kidney.org/"
    "ckd-epi-creatinine-equation-2021"
)

KDIGO_CKD_URL = (
    "https://kdigo.org/guidelines/"
    "ckd-evaluation-and-management/"
)

KDIGO_AKI_URL = (
    "https://kdigo.org/wp-content/uploads/"
    "2016/10/KDIGO-2012-AKI-Guideline-English.pdf"
)



# Clinical cut-points must not change because of binary floating-point
# representation (for example, 1.2 - 0.9 is slightly below 0.3 in
# IEEE-754 arithmetic). The tolerance is deliberately tiny: it corrects
# machine precision only and does not clinically round measurements.
_FLOAT_ABS_TOL = 1e-9


def _at_least(
    value: float,
    threshold: float,
) -> bool:
    return (
        value > threshold
        or math.isclose(
            value,
            threshold,
            rel_tol=0.0,
            abs_tol=_FLOAT_ABS_TOL,
        )
    )


def _strictly_below(
    value: float,
    threshold: float,
) -> bool:
    return (
        value < threshold
        and not math.isclose(
            value,
            threshold,
            rel_tol=0.0,
            abs_tol=_FLOAT_ABS_TOL,
        )
    )


def _creatinine_mg_dl(
    value: float,
    unit: CreatinineUnit,
) -> float:
    if value <= 0:
        raise ValueError(
            "Creatinine must be greater than zero."
        )

    if unit == "mg/dL":
        return value

    if unit == "umol/L":
        return value / 88.4

    raise ValueError(
        "Unsupported creatinine unit."
    )


def gfr_category(
    egfr: float,
) -> tuple[str, str, str]:
    if egfr < 0:
        raise ValueError(
            "eGFR cannot be negative."
        )

    if egfr >= 90:
        return (
            "G1",
            "Normal ou elevada",
            "Normal or high",
        )

    if egfr >= 60:
        return (
            "G2",
            "Levemente reduzida",
            "Mildly decreased",
        )

    if egfr >= 45:
        return (
            "G3a",
            "Leve a moderadamente reduzida",
            "Mildly to moderately decreased",
        )

    if egfr >= 30:
        return (
            "G3b",
            "Moderada a gravemente reduzida",
            "Moderately to severely decreased",
        )

    if egfr >= 15:
        return (
            "G4",
            "Gravemente reduzida",
            "Severely decreased",
        )

    return (
        "G5",
        "Falência renal",
        "Kidney failure",
    )


def albuminuria_category(
    acr: float,
    unit: ACRUnit,
) -> tuple[str, str, str]:
    if acr < 0:
        raise ValueError(
            "ACR cannot be negative."
        )

    if unit == "mg/g":
        if acr < 30:
            category = "A1"
        elif acr <= 300:
            category = "A2"
        else:
            category = "A3"

    elif unit == "mg/mmol":
        if acr < 3:
            category = "A1"
        elif acr <= 30:
            category = "A2"
        else:
            category = "A3"

    else:
        raise ValueError(
            "Unsupported ACR unit."
        )

    labels = {
        "A1": (
            "Normal a levemente aumentada",
            "Normal to mildly increased",
        ),
        "A2": (
            "Moderadamente aumentada",
            "Moderately increased",
        ),
        "A3": (
            "Gravemente aumentada",
            "Severely increased",
        ),
    }

    pt, en = labels[category]

    return category, pt, en


def calculate_egfr_ckd_epi_2021(
    *,
    age_years: int,
    sex: Sex,
    serum_creatinine: float,
    creatinine_unit: CreatinineUnit,
) -> dict:
    """Calculate adult race-free CKD-EPI 2021 eGFRcr."""

    if not 18 <= age_years <= 120:
        raise ValueError(
            "CKD-EPI 2021 adult calculation requires "
            "age between 18 and 120 years."
        )

    if sex not in {
        "female",
        "male",
    }:
        raise ValueError(
            "sex must be female or male for this equation."
        )

    scr = _creatinine_mg_dl(
        serum_creatinine,
        creatinine_unit,
    )

    if sex == "female":
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0

    ratio = scr / kappa

    egfr = (
        142
        * min(ratio, 1.0) ** alpha
        * max(ratio, 1.0) ** -1.200
        * 0.9938 ** age_years
        * sex_factor
    )

    category, category_pt, category_en = (
        gfr_category(egfr)
    )

    return {
        "tool": "egfr_ckd_epi_2021",
        "equation": "CKD-EPI creatinine 2021",
        "race_coefficient_used": False,
        "age_years": age_years,
        "sex": sex,
        "creatinine_mg_dl": round(scr, 4),
        "egfr_ml_min_1_73m2": round(egfr, 1),
        "gfr_category": category,
        "gfr_category_label_pt": category_pt,
        "gfr_category_label_en": category_en,
        "interpretation_pt": (
            "TFG estimada indexada para 1,73 m². "
            "Não é equivalente ao clearance de creatinina "
            "de Cockcroft-Gault nem a uma TFG não indexada."
        ),
        "interpretation_en": (
            "Estimated GFR indexed to 1.73 m². "
            "It is not equivalent to Cockcroft-Gault "
            "creatinine clearance or an unindexed GFR."
        ),
    }


def classify_ckd(
    *,
    egfr_ml_min_1_73m2: float,
    acr: float | None = None,
    acr_unit: ACRUnit = "mg/g",
    chronicity_at_least_3_months: bool = False,
    other_kidney_damage_marker: bool = False,
) -> dict:
    """Classify G/A and assess CKD definition from supplied data."""

    if egfr_ml_min_1_73m2 < 0:
        raise ValueError(
            "eGFR cannot be negative."
        )

    g_category_code, g_pt, g_en = (
        gfr_category(
            egfr_ml_min_1_73m2
        )
    )

    if acr is None:
        a_category_code = None
        a_pt = None
        a_en = None
    else:
        (
            a_category_code,
            a_pt,
            a_en,
        ) = albuminuria_category(
            acr,
            acr_unit,
        )

    reduced_gfr_marker = (
        egfr_ml_min_1_73m2 < 60
    )

    albuminuria_marker = (
        a_category_code
        in {"A2", "A3"}
    )

    abnormality_present = (
        reduced_gfr_marker
        or albuminuria_marker
        or other_kidney_damage_marker
    )

    if (
        abnormality_present
        and chronicity_at_least_3_months
    ):
        status_code = "criteria_met"

        status_pt = (
            "Os dados fornecidos atendem à definição "
            "de DRC quanto à cronicidade e aos marcadores "
            "informados."
        )

        status_en = (
            "The supplied data meet the CKD definition "
            "with respect to the reported chronicity and "
            "kidney abnormality markers."
        )

    elif abnormality_present:
        status_code = (
            "chronicity_not_established"
        )

        status_pt = (
            "Há marcador compatível com doença renal, "
            "mas a cronicidade mínima de 3 meses não foi "
            "confirmada; DRC não deve ser inferida deste "
            "resultado isolado."
        )

        status_en = (
            "A kidney abnormality marker is present, "
            "but the minimum 3-month chronicity has not "
            "been confirmed; CKD must not be inferred "
            "from this isolated result."
        )

    else:
        status_code = (
            "criteria_not_met_by_supplied_data"
        )

        status_pt = (
            "Os dados fornecidos não atendem, por si só, "
            "à definição de DRC."
        )

        status_en = (
            "The supplied data do not, by themselves, "
            "meet the definition of CKD."
        )

    ga_classification = (
        f"{g_category_code}/{a_category_code}"
        if a_category_code
        else g_category_code
    )

    return {
        "tool": "ckd_classification",
        "gfr_category": g_category_code,
        "gfr_category_label_pt": g_pt,
        "gfr_category_label_en": g_en,
        "albuminuria_category":
            a_category_code,
        "albuminuria_category_label_pt":
            a_pt,
        "albuminuria_category_label_en":
            a_en,
        "ga_classification":
            ga_classification,
        "chronicity_at_least_3_months":
            chronicity_at_least_3_months,
        "other_kidney_damage_marker":
            other_kidney_damage_marker,
        "ckd_status_code":
            status_code,
        "ckd_status_pt":
            status_pt,
        "ckd_status_en":
            status_en,
        "classification_note_pt": (
            "A classificação completa KDIGO é CGA "
            "(causa, categoria G e categoria A). "
            "Este módulo determina G/A; a causa não é "
            "inferida automaticamente."
        ),
        "classification_note_en": (
            "Complete KDIGO classification is CGA "
            "(cause, G category and A category). "
            "This module determines G/A; cause is not "
            "inferred automatically."
        ),
    }


_AKI_CRITERIA_PT = {
    "creatinine_delta_0_3_within_48h":
        "Aumento de creatinina ≥0,3 mg/dL em até 48 horas.",

    "creatinine_ratio_1_5_within_7d":
        "Creatinina ≥1,5 vez o basal em até 7 dias.",

    "creatinine_ratio_2_0_to_2_9":
        "Creatinina entre 2,0 e 2,9 vezes o basal.",

    "creatinine_ratio_3_0":
        "Creatinina ≥3,0 vezes o basal.",

    "creatinine_to_4_0":
        "Aumento agudo da creatinina para ≥4,0 mg/dL.",

    "urine_output_below_0_5_6h":
        "Diurese <0,5 mL/kg/h por pelo menos 6 horas.",

    "urine_output_below_0_5_12h":
        "Diurese <0,5 mL/kg/h por pelo menos 12 horas.",

    "urine_output_below_0_3_24h":
        "Diurese <0,3 mL/kg/h por pelo menos 24 horas.",

    "anuria_6h":
        "Anúria por pelo menos 6 horas.",

    "anuria_12h":
        "Anúria por pelo menos 12 horas.",

    "renal_replacement_therapy":
        "Terapia renal substitutiva iniciada.",
}


_AKI_CRITERIA_EN = {
    "creatinine_delta_0_3_within_48h":
        "Serum creatinine increased by ≥0.3 mg/dL within 48 hours.",

    "creatinine_ratio_1_5_within_7d":
        "Serum creatinine is ≥1.5 times baseline within 7 days.",

    "creatinine_ratio_2_0_to_2_9":
        "Serum creatinine is 2.0–2.9 times baseline.",

    "creatinine_ratio_3_0":
        "Serum creatinine is ≥3.0 times baseline.",

    "creatinine_to_4_0":
        "Acute serum creatinine increase to ≥4.0 mg/dL.",

    "urine_output_below_0_5_6h":
        "Urine output <0.5 mL/kg/h for at least 6 hours.",

    "urine_output_below_0_5_12h":
        "Urine output <0.5 mL/kg/h for at least 12 hours.",

    "urine_output_below_0_3_24h":
        "Urine output <0.3 mL/kg/h for at least 24 hours.",

    "anuria_6h":
        "Anuria for at least 6 hours.",

    "anuria_12h":
        "Anuria for at least 12 hours.",

    "renal_replacement_therapy":
        "Kidney replacement therapy initiated.",
}


def calculate_kdigo_aki(
    *,
    current_creatinine: float | None = None,
    current_creatinine_unit: CreatinineUnit = "mg/dL",
    baseline_creatinine: float | None = None,
    baseline_creatinine_unit: CreatinineUnit | None = None,
    baseline_interval_hours: float | None = None,
    weight_kg: float | None = None,
    urine_output_ml: float | None = None,
    urine_output_duration_hours: float | None = None,
    anuria_duration_hours: float | None = None,
    renal_replacement_therapy: bool = False,
) -> dict:
    """Stage adult AKI using supplied KDIGO 2012 criteria."""

    current = (
        _creatinine_mg_dl(
            current_creatinine,
            current_creatinine_unit,
        )
        if current_creatinine is not None
        else None
    )

    criteria_codes: list[str] = []

    creatinine_stage: int | None = None
    urine_output_stage: int | None = None
    rrt_stage: int | None = None

    creatinine_ratio = None
    creatinine_delta = None
    urine_rate = None

    if baseline_creatinine is not None:
        if current is None:
            raise ValueError(
                "current_creatinine is required when "
                "baseline_creatinine is supplied."
            )

        if baseline_interval_hours is None:
            raise ValueError(
                "baseline_interval_hours is required "
                "when baseline_creatinine is supplied."
            )

        if baseline_interval_hours < 0:
            raise ValueError(
                "baseline_interval_hours cannot be negative."
            )

        baseline = _creatinine_mg_dl(
            baseline_creatinine,
            (
                baseline_creatinine_unit
                or current_creatinine_unit
            ),
        )

        creatinine_ratio = current / baseline
        creatinine_delta = current - baseline

        if baseline_interval_hours <= 168:
            acute_by_ratio = (
                _at_least(creatinine_ratio, 1.5)
            )

            acute_by_delta = (
                baseline_interval_hours <= 48
                and _at_least(creatinine_delta, 0.3)
            )

            acute_creatinine_criterion = (
                acute_by_ratio
                or acute_by_delta
            )

            if acute_by_delta:
                criteria_codes.append(
                    "creatinine_delta_0_3_within_48h"
                )

            if acute_by_ratio:
                criteria_codes.append(
                    "creatinine_ratio_1_5_within_7d"
                )

            if acute_creatinine_criterion:
                if (
                    _at_least(creatinine_ratio, 3.0)
                    or _at_least(current, 4.0)
                ):
                    creatinine_stage = 3

                    if _at_least(creatinine_ratio, 3.0):
                        criteria_codes.append(
                            "creatinine_ratio_3_0"
                        )

                    if _at_least(current, 4.0):
                        criteria_codes.append(
                            "creatinine_to_4_0"
                        )

                elif _at_least(creatinine_ratio, 2.0):
                    creatinine_stage = 2

                    criteria_codes.append(
                        "creatinine_ratio_2_0_to_2_9"
                    )

                else:
                    creatinine_stage = 1

            else:
                creatinine_stage = 0

    urine_group = (
        weight_kg,
        urine_output_ml,
        urine_output_duration_hours,
    )

    supplied_urine_fields = sum(
        value is not None
        for value in urine_group
    )

    if supplied_urine_fields not in {0, 3}:
        raise ValueError(
            "weight_kg, urine_output_ml and "
            "urine_output_duration_hours must be "
            "supplied together."
        )

    if supplied_urine_fields == 3:
        assert weight_kg is not None
        assert urine_output_ml is not None
        assert urine_output_duration_hours is not None

        if weight_kg <= 0:
            raise ValueError(
                "weight_kg must be greater than zero."
            )

        if urine_output_ml < 0:
            raise ValueError(
                "urine_output_ml cannot be negative."
            )

        if urine_output_duration_hours <= 0:
            raise ValueError(
                "urine_output_duration_hours must be "
                "greater than zero."
            )

        urine_rate = (
            urine_output_ml
            / weight_kg
            / urine_output_duration_hours
        )

        if (
            urine_output_duration_hours >= 24
            and _strictly_below(urine_rate, 0.3)
        ):
            urine_output_stage = 3

            criteria_codes.append(
                "urine_output_below_0_3_24h"
            )

        elif (
            urine_output_duration_hours >= 12
            and _strictly_below(urine_rate, 0.5)
        ):
            urine_output_stage = 2

            criteria_codes.append(
                "urine_output_below_0_5_12h"
            )

        elif (
            urine_output_duration_hours >= 6
            and _strictly_below(urine_rate, 0.5)
        ):
            urine_output_stage = 1

            criteria_codes.append(
                "urine_output_below_0_5_6h"
            )

        else:
            urine_output_stage = 0

    if anuria_duration_hours is not None:
        if anuria_duration_hours < 0:
            raise ValueError(
                "anuria_duration_hours cannot be negative."
            )

        anuria_stage = 0

        if anuria_duration_hours >= 12:
            anuria_stage = 3

            criteria_codes.append(
                "anuria_12h"
            )

        elif anuria_duration_hours >= 6:
            anuria_stage = 1

            criteria_codes.append(
                "anuria_6h"
            )

        urine_output_stage = max(
            urine_output_stage or 0,
            anuria_stage,
        )

    if renal_replacement_therapy:
        rrt_stage = 3

        criteria_codes.append(
            "renal_replacement_therapy"
        )

    evaluable_stages = [
        stage
        for stage in (
            creatinine_stage,
            urine_output_stage,
            rrt_stage,
        )
        if stage is not None
    ]

    if not evaluable_stages:
        stage = None
        evaluable = False
        aki_criteria_met = None

        interpretation_pt = (
            "Dados insuficientes para determinar estágio "
            "KDIGO de LRA. É necessário um critério temporal "
            "de creatinina, diurese mensurável ou informação "
            "sobre terapia renal substitutiva."
        )

        interpretation_en = (
            "Insufficient data to determine KDIGO AKI stage. "
            "A time-qualified creatinine comparison, measured "
            "urine output or kidney replacement therapy "
            "information is required."
        )

    else:
        stage = max(evaluable_stages)
        evaluable = True
        aki_criteria_met = stage > 0

        if stage == 0:
            interpretation_pt = (
                "Nenhum critério KDIGO de LRA foi atendido "
                "pelos dados temporais fornecidos."
            )

            interpretation_en = (
                "No KDIGO AKI criterion was met by the "
                "time-qualified data supplied."
            )

        else:
            interpretation_pt = (
                f"LRA KDIGO estágio {stage} pelos critérios "
                "fornecidos. O estágio final corresponde ao "
                "critério de maior gravidade."
            )

            interpretation_en = (
                f"KDIGO AKI stage {stage} by the supplied "
                "criteria. The final stage is determined by "
                "the most severe qualifying criterion."
            )

    unique_codes = list(
        dict.fromkeys(criteria_codes)
    )

    return {
        "tool": "kdigo_aki",
        "evaluable": evaluable,
        "aki_criteria_met": aki_criteria_met,
        "stage": stage,
        "creatinine_stage": creatinine_stage,
        "urine_output_stage": urine_output_stage,
        "rrt_stage": rrt_stage,
        "current_creatinine_mg_dl":
            (
                round(current, 4)
                if current is not None
                else None
            ),
        "creatinine_ratio":
            (
                round(creatinine_ratio, 4)
                if creatinine_ratio is not None
                else None
            ),
        "creatinine_delta_mg_dl":
            (
                round(creatinine_delta, 4)
                if creatinine_delta is not None
                else None
            ),
        "urine_output_ml_kg_h":
            (
                round(urine_rate, 4)
                if urine_rate is not None
                else None
            ),
        "criteria_codes":
            unique_codes,
        "criteria_pt": [
            _AKI_CRITERIA_PT[code]
            for code in unique_codes
        ],
        "criteria_en": [
            _AKI_CRITERIA_EN[code]
            for code in unique_codes
        ],
        "interpretation_pt":
            interpretation_pt,
        "interpretation_en":
            interpretation_en,
    }


EGFR_METADATA = {
    "id": "egfr-ckd-epi-2021",
    "name_pt": "TFG estimada — CKD-EPI creatinina 2021",
    "name_en": "Estimated GFR — CKD-EPI creatinine 2021",
    "description_pt": (
        "Estimativa da TFG em adultos pela equação CKD-EPI "
        "2021 baseada em creatinina e sem coeficiente de raça."
    ),
    "description_en": (
        "Adult GFR estimate using the 2021 CKD-EPI "
        "creatinine equation without a race coefficient."
    ),
    "aliases_pt": [
        "TFG",
        "TFGe",
        "eGFR",
        "CKD-EPI 2021",
        "função renal",
    ],
    "aliases_en": [
        "eGFR",
        "estimated GFR",
        "CKD-EPI 2021",
        "kidney function",
    ],
    "publisher": "National Kidney Foundation",
    "source_title": "CKD-EPI Creatinine Equation (2021)",
    "source_version": "2021 race-free creatinine equation",
    "source_url": NKF_EGFR_URL,
    "source_language": "en-US",
    "canonical_language": "en-US",
    "translation_status_pt": "local_translation",
    "translation_status_en": "informative_translation",
    "translation_disclaimer_required": False,
    "translation_disclaimer_source_url": None,
    "translation_note_pt": (
        "Explicações PT-BR são redação clínica local; "
        "a fórmula matemática permanece inalterada."
    ),
    "translation_note_en": (
        "EN-GB explanatory text is locally authored; "
        "the mathematical equation is unchanged."
    ),
    "population_pt": "Adultos com 18 anos ou mais.",
    "population_en": "Adults aged 18 years or older.",
    "limitations_pt": [
        (
            "Utilizar creatinina padronizada/rastreável a IDMS."
        ),
        (
            "A TFGe é uma estimativa e pode ser menos confiável "
            "quando a creatinina é influenciada por fatores não "
            "relacionados à TFG."
        ),
        (
            "O resultado é indexado para 1,73 m² e não é "
            "equivalente ao clearance de Cockcroft-Gault."
        ),
    ],
    "limitations_en": [
        "Use IDMS-standardised/traceable creatinine.",
        (
            "eGFR is an estimate and may be less reliable when "
            "serum creatinine is affected by non-GFR factors."
        ),
        (
            "The result is indexed to 1.73 m² and is not "
            "equivalent to Cockcroft-Gault clearance."
        ),
    ],
    "licensing_note_pt": (
        "Implementação matemática e explicações próprias com "
        "referência à equação publicada."
    ),
    "licensing_note_en": (
        "Mathematical implementation and locally authored "
        "explanations referencing the published equation."
    ),
    "clinical_review_date": date(2026, 9, 10),
    "offline_capable": True,
}


CKD_METADATA = {
    "id": "ckd-classification-kdigo-2024",
    "name_pt": "Classificação de DRC — KDIGO 2024",
    "name_en": "CKD classification — KDIGO 2024",
    "description_pt": (
        "Classificação renal pelas categorias G de TFG e A de "
        "albuminúria, com verificação explícita de cronicidade."
    ),
    "description_en": (
        "Kidney classification using GFR G and albuminuria A "
        "categories with explicit assessment of chronicity."
    ),
    "aliases_pt": [
        "DRC",
        "doença renal crônica",
        "KDIGO",
        "G1 G2 G3a G3b G4 G5",
        "A1 A2 A3",
    ],
    "aliases_en": [
        "CKD",
        "chronic kidney disease",
        "KDIGO",
        "GFR category",
        "albuminuria category",
    ],
    "publisher": "KDIGO",
    "source_title": (
        "KDIGO 2024 Clinical Practice Guideline for the "
        "Evaluation and Management of Chronic Kidney Disease"
    ),
    "source_version": "KDIGO CKD 2024",
    "source_url": KDIGO_CKD_URL,
    "source_language": "en",
    "canonical_language": "en",
    "translation_status_pt": "local_translation",
    "translation_status_en": "informative_translation",
    "translation_disclaimer_required": False,
    "translation_disclaimer_source_url": None,
    "translation_note_pt": (
        "Descrições PT-BR são redação local baseada nas "
        "categorias KDIGO."
    ),
    "translation_note_en": (
        "EN-GB descriptions are locally authored from the "
        "KDIGO categories."
    ),
    "population_pt": (
        "Pessoas em avaliação de doença renal crônica."
    ),
    "population_en": (
        "People undergoing assessment for chronic kidney disease."
    ),
    "limitations_pt": [
        (
            "DRC exige anormalidade renal presente por no mínimo "
            "3 meses."
        ),
        (
            "G1 ou G2 isoladamente não estabelecem DRC na "
            "ausência de outro marcador de dano renal."
        ),
        (
            "O módulo determina G/A; a causa da DRC não é "
            "inferida automaticamente."
        ),
    ],
    "limitations_en": [
        (
            "CKD requires a kidney abnormality present for a "
            "minimum of 3 months."
        ),
        (
            "G1 or G2 alone do not establish CKD without "
            "another marker of kidney damage."
        ),
        (
            "The module determines G/A; cause of CKD is not "
            "automatically inferred."
        ),
    ],
    "licensing_note_pt": (
        "Categorias implementadas como lógica estruturada com "
        "explicações próprias; consultar a diretriz completa."
    ),
    "licensing_note_en": (
        "Categories implemented as structured logic with "
        "locally authored explanations; consult the full guideline."
    ),
    "clinical_review_date": date(2026, 9, 10),
    "offline_capable": True,
}


AKI_METADATA = {
    "id": "kdigo-aki-2012",
    "name_pt": "Estadiamento de LRA — KDIGO",
    "name_en": "AKI staging — KDIGO",
    "description_pt": (
        "Definição e estadiamento de lesão renal aguda em adultos "
        "pelos critérios de creatinina, diurese e terapia renal "
        "substitutiva."
    ),
    "description_en": (
        "Adult acute kidney injury definition and staging using "
        "creatinine, urine-output and kidney replacement therapy "
        "criteria."
    ),
    "aliases_pt": [
        "LRA",
        "lesão renal aguda",
        "KDIGO AKI",
        "diurese",
    ],
    "aliases_en": [
        "AKI",
        "acute kidney injury",
        "KDIGO AKI",
        "urine output",
    ],
    "publisher": "KDIGO",
    "source_title": (
        "KDIGO Clinical Practice Guideline for Acute Kidney Injury"
    ),
    "source_version": (
        "KDIGO AKI 2012 — current published staging basis; "
        "2026 public-review draft excluded"
    ),
    "source_url": KDIGO_AKI_URL,
    "source_language": "en",
    "canonical_language": "en",
    "translation_status_pt": "local_translation",
    "translation_status_en": "informative_translation",
    "translation_disclaimer_required": False,
    "translation_disclaimer_source_url": None,
    "translation_note_pt": (
        "Descrições PT-BR são redação clínica local baseada "
        "nos critérios KDIGO publicados."
    ),
    "translation_note_en": (
        "EN-GB descriptions are locally authored from the "
        "published KDIGO criteria."
    ),
    "population_pt": (
        "Adultos em avaliação de lesão renal aguda."
    ),
    "population_en": (
        "Adults undergoing assessment for acute kidney injury."
    ),
    "limitations_pt": [
        (
            "Este módulo é adulto e não implementa o critério "
            "pediátrico de TFGe <35 mL/min/1,73 m² do estágio 3."
        ),
        (
            "A avaliação por creatinina exige informação temporal "
            "compatível com as janelas KDIGO."
        ),
        (
            "A causa da LRA deve ser investigada clinicamente e "
            "não é determinada pelo escore."
        ),
    ],
    "limitations_en": [
        (
            "This implementation is adult-only and does not "
            "implement the paediatric stage-3 eGFR <35 criterion."
        ),
        (
            "Creatinine assessment requires time information "
            "compatible with KDIGO windows."
        ),
        (
            "The cause of AKI requires clinical evaluation and "
            "is not determined by the stage."
        ),
    ],
    "licensing_note_pt": (
        "Critérios implementados como lógica estruturada com "
        "explicações próprias; consultar a diretriz completa."
    ),
    "licensing_note_en": (
        "Criteria implemented as structured logic with locally "
        "authored explanations; consult the full guideline."
    ),
    "clinical_review_date": date(2026, 9, 10),
    "offline_capable": True,
}
