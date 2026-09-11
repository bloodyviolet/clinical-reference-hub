"""Brazilian national falls/function assessment core.

This module intentionally keeps two independent national instruments
separate:

1. Caderneta Brasileira da Pessoa Idosa 2026 falls check-up.
   - 12 yes/no items.
   - Any positive answer indicates assessment.
   - No weighted score is reconstructed or imported.

2. IVCF-20.
   - Brazilian older-person clinical-functional vulnerability index.
   - Official 0-40 scoring.
   - Not a falls-risk score.
   - The 4-m gait item is not Timed Up and Go.

No synthetic score is calculated across these instruments.
"""

from __future__ import annotations

from datetime import date


CADERNETA_2026_URL = (
    "https://www.gov.br/saude/pt-br/"
    "composicao/saps/publicacoes/"
    "cadernetas-e-cartoes/"
    "caderneta-brasileira-da-pessoa-idosa/"
)

IVCF_2026_NOTE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "centrais-de-conteudo/publicacoes/"
    "estudos-e-notas-informativas/2026/"
    "nota-informativa-no-1-2026-"
    "copid-dgci-saps-ms.pdf/view"
)


CADERNETA_FALLS_ITEM_KEYS = (
    "fall_previous_year",
    "cane_or_walker_recommended",
    "unsteady_while_walking",
    "uses_furniture_for_support",
    "concern_about_falling",
    "needs_hands_to_rise_from_chair",
    "difficulty_stepping_onto_curb",
    "toilet_urgency",
    "reduced_foot_sensation",
    "medication_dizziness_or_fatigue",
    "sleep_or_mood_medication",
    "sadness_or_depressed_mood",
)


def _validate_older_person_age(
    age_years: int,
) -> None:
    if isinstance(age_years, bool):
        raise ValueError(
            "age_years must be an integer age."
        )

    if (
        not isinstance(age_years, int)
        or age_years < 60
    ):
        raise ValueError(
            "age_years must be 60 or greater."
        )


def calculate_caderneta_falls_checkup(
    *,
    age_years: int,
    fall_previous_year: bool,
    cane_or_walker_recommended: bool,
    unsteady_while_walking: bool,
    uses_furniture_for_support: bool,
    concern_about_falling: bool,
    needs_hands_to_rise_from_chair: bool,
    difficulty_stepping_onto_curb: bool,
    toilet_urgency: bool,
    reduced_foot_sensation: bool,
    medication_dizziness_or_fatigue: bool,
    sleep_or_mood_medication: bool,
    sadness_or_depressed_mood: bool,
) -> dict:
    """Apply the unweighted 2026 Caderneta falls check-up."""

    _validate_older_person_age(age_years)

    responses = {
        "fall_previous_year":
            fall_previous_year,
        "cane_or_walker_recommended":
            cane_or_walker_recommended,
        "unsteady_while_walking":
            unsteady_while_walking,
        "uses_furniture_for_support":
            uses_furniture_for_support,
        "concern_about_falling":
            concern_about_falling,
        "needs_hands_to_rise_from_chair":
            needs_hands_to_rise_from_chair,
        "difficulty_stepping_onto_curb":
            difficulty_stepping_onto_curb,
        "toilet_urgency":
            toilet_urgency,
        "reduced_foot_sensation":
            reduced_foot_sensation,
        "medication_dizziness_or_fatigue":
            medication_dizziness_or_fatigue,
        "sleep_or_mood_medication":
            sleep_or_mood_medication,
        "sadness_or_depressed_mood":
            sadness_or_depressed_mood,
    }

    positive_items = [
        key
        for key in CADERNETA_FALLS_ITEM_KEYS
        if responses[key]
    ]

    assessment_indicated = bool(
        positive_items
    )

    return {
        "tool":
            "brazil_caderneta_falls_checkup_2026",

        "age_years":
            age_years,

        "positive_items_count":
            len(positive_items),

        "positive_items":
            positive_items,

        "assessment_indicated":
            assessment_indicated,

        "any_yes_rule_applied":
            True,

        "weighted_score_applied":
            False,

        "foreign_weighted_score_imported":
            False,

        "fall_risk_classification_applied":
            False,

        "automatic_ivcf_inference_applied":
            False,

        "synthetic_cross_instrument_score_applied":
            False,

        "interpretation_pt": (
            (
                "Há pelo menos uma resposta positiva; "
                "a Caderneta orienta avaliação."
            )
            if assessment_indicated
            else (
                "Nenhuma resposta positiva foi registrada "
                "neste check-up. O instrumento não produz "
                "escore ponderado de risco."
            )
        ),

        "interpretation_en": (
            (
                "At least one positive response is present; "
                "the Brazilian Caderneta indicates assessment."
            )
            if assessment_indicated
            else (
                "No positive response was recorded in this "
                "check-up. The instrument does not produce "
                "a weighted risk score."
            )
        ),
    }


def calculate_ivcf20(
    *,
    age_years: int,
    self_rated_health_regular_or_poor: bool,
    stopped_shopping_due_health: bool,
    stopped_managing_money_due_health: bool,
    stopped_housework_due_health: bool,
    stopped_bathing_due_health: bool,
    forgetfulness_noted_by_others: bool,
    worsening_forgetfulness: bool,
    forgetfulness_impairs_daily_activity: bool,
    depressed_or_hopeless_last_month: bool,
    anhedonia_last_month: bool,
    unable_raise_arms_above_shoulders: bool,
    unable_handle_small_objects: bool,
    unintentional_weight_loss_criterion: bool,
    bmi_lt_22: bool,
    calf_circumference_lt_31_cm: bool,
    gait_4m_gt_5_seconds: bool,
    walking_difficulty_impairs_daily_activity: bool,
    two_or_more_falls_last_year: bool,
    urinary_or_fecal_incontinence: bool,
    vision_impairs_daily_activity: bool,
    hearing_impairs_daily_activity: bool,
    five_or_more_chronic_conditions: bool,
    five_or_more_daily_medications: bool,
    hospitalized_last_six_months: bool,
) -> dict:
    """Calculate the Brazilian national IVCF-20 score."""

    _validate_older_person_age(age_years)

    if age_years >= 85:
        age_score = 3
    elif age_years >= 75:
        age_score = 1
    else:
        age_score = 0

    health_perception_score = (
        1
        if self_rated_health_regular_or_poor
        else 0
    )

    instrumental_adl_positive = any(
        (
            stopped_shopping_due_health,
            stopped_managing_money_due_health,
            stopped_housework_due_health,
        )
    )

    instrumental_adl_score = (
        4
        if instrumental_adl_positive
        else 0
    )

    basic_adl_score = (
        6
        if stopped_bathing_due_health
        else 0
    )

    cognition_score = (
        int(forgetfulness_noted_by_others)
        + int(worsening_forgetfulness)
        + (
            2
            if forgetfulness_impairs_daily_activity
            else 0
        )
    )

    mood_score = (
        (
            2
            if depressed_or_hopeless_last_month
            else 0
        )
        + (
            2
            if anhedonia_last_month
            else 0
        )
    )

    upper_limb_score = (
        int(unable_raise_arms_above_shoulders)
        + int(unable_handle_small_objects)
    )

    aerobic_muscular_positive = any(
        (
            unintentional_weight_loss_criterion,
            bmi_lt_22,
            calf_circumference_lt_31_cm,
            gait_4m_gt_5_seconds,
        )
    )

    aerobic_muscular_score = (
        2
        if aerobic_muscular_positive
        else 0
    )

    gait_score = (
        (
            2
            if walking_difficulty_impairs_daily_activity
            else 0
        )
        + (
            2
            if two_or_more_falls_last_year
            else 0
        )
    )

    continence_score = (
        2
        if urinary_or_fecal_incontinence
        else 0
    )

    vision_score = (
        2
        if vision_impairs_daily_activity
        else 0
    )

    hearing_score = (
        2
        if hearing_impairs_daily_activity
        else 0
    )

    multiple_comorbidity_positive = any(
        (
            five_or_more_chronic_conditions,
            five_or_more_daily_medications,
            hospitalized_last_six_months,
        )
    )

    multiple_comorbidity_score = (
        4
        if multiple_comorbidity_positive
        else 0
    )

    dimension_scores = {
        "age":
            age_score,
        "health_perception":
            health_perception_score,
        "instrumental_adl":
            instrumental_adl_score,
        "basic_adl":
            basic_adl_score,
        "cognition":
            cognition_score,
        "mood":
            mood_score,
        "upper_limb_mobility":
            upper_limb_score,
        "aerobic_muscular_capacity":
            aerobic_muscular_score,
        "gait":
            gait_score,
        "continence":
            continence_score,
        "vision":
            vision_score,
        "hearing":
            hearing_score,
        "multiple_comorbidities":
            multiple_comorbidity_score,
    }

    total_score = sum(
        dimension_scores.values()
    )

    if total_score <= 6:
        classification_code = "low"
        classification_pt = (
            "Baixo risco de vulnerabilidade "
            "clínico-funcional"
        )
        classification_en = (
            "Low clinical-functional vulnerability risk"
        )
        reapplication_months = 12
    elif total_score <= 14:
        classification_code = "moderate"
        classification_pt = (
            "Moderado risco de vulnerabilidade "
            "clínico-funcional"
        )
        classification_en = (
            "Moderate clinical-functional "
            "vulnerability risk"
        )
        reapplication_months = 6
    else:
        classification_code = "high"
        classification_pt = (
            "Alto risco de vulnerabilidade "
            "clínico-funcional"
        )
        classification_en = (
            "High clinical-functional vulnerability risk"
        )
        reapplication_months = 6

    altered_dimensions = [
        key
        for key, value in dimension_scores.items()
        if value > 0
    ]

    return {
        "tool":
            "ivcf20",

        "age_years":
            age_years,

        "total_score":
            total_score,

        "classification_code":
            classification_code,

        "classification_pt":
            classification_pt,

        "classification_en":
            classification_en,

        "dimension_scores":
            dimension_scores,

        "altered_dimensions":
            altered_dimensions,

        "reapplication_months_minimum":
            reapplication_months,

        "reapply_after_sentinel_event":
            True,

        "complete_assessment_required":
            True,

        "gait_4m_gt_5_seconds":
            gait_4m_gt_5_seconds,

        "gait_4m_is_tug":
            False,

        "fall_risk_classification_applied":
            False,

        "automatic_caderneta_inference_applied":
            False,

        "synthetic_cross_instrument_score_applied":
            False,

        "interpretation_pt": (
            f"IVCF-20: {total_score}/40 — "
            f"{classification_pt}. "
            "O resultado orienta a avaliação "
            "clínico-funcional e não constitui "
            "escore isolado de risco de quedas."
        ),

        "interpretation_en": (
            f"IVCF-20: {total_score}/40 — "
            f"{classification_en}. "
            "The result supports clinical-functional "
            "assessment and is not a standalone "
            "falls-risk score."
        ),
    }


CADERNETA_FALLS_METADATA = {
    "id":
        "brazil-caderneta-falls-checkup-2026",

    "name_pt":
        "Caderneta 2026 · check-up para prevenção de quedas",

    "name_en":
        "Brazilian Caderneta 2026 · falls prevention check-up",

    "description_pt": (
        "Check-up nacional de 12 itens sim/não da "
        "Caderneta Brasileira da Pessoa Idosa 2026. "
        "Qualquer resposta positiva indica avaliação; "
        "não há escore ponderado."
    ),

    "description_en": (
        "National 12-item yes/no check-up from the "
        "2026 Brazilian Older Person Caderneta. "
        "Any positive response indicates assessment; "
        "no weighted score is applied."
    ),

    "aliases_pt": [
        "quedas",
        "prevenção de quedas",
        "caderneta da pessoa idosa",
    ],

    "aliases_en": [
        "falls",
        "falls prevention",
        "older person caderneta",
    ],

    "publisher":
        "Ministério da Saúde / SAPS",

    "source_title":
        "Caderneta Brasileira da Pessoa Idosa 2026",

    "source_version":
        "2026 edition",

    "source_url":
        CADERNETA_2026_URL,

    "source_language":
        "pt-BR",

    "canonical_language":
        "pt-BR",

    "translation_status_pt":
        "official_original",

    "translation_status_en":
        "informative_translation",

    "translation_disclaimer_required":
        False,

    "translation_disclaimer_source_url":
        None,

    "translation_note_pt": (
        "A camada PT-BR acompanha a fonte oficial brasileira."
    ),

    "translation_note_en": (
        "EN-GB text is an informative translation "
        "of the Brazilian national source."
    ),

    "population_pt":
        "Pessoas idosas, 60 anos ou mais.",

    "population_en":
        "Older people aged 60 years or over.",

    "limitations_pt": [
        (
            "O check-up não produz escore ponderado."
        ),
        (
            "Não substituir por pontuação estrangeira "
            "STEADI/NCOA."
        ),
        (
            "Não combinar automaticamente com IVCF-20."
        ),
    ],

    "limitations_en": [
        (
            "The check-up does not produce a weighted score."
        ),
        (
            "Do not replace it with a foreign "
            "STEADI/NCOA score."
        ),
        (
            "Do not automatically combine it with IVCF-20."
        ),
    ],

    "licensing_note_pt": (
        "Implementação lógica própria baseada em fonte "
        "pública oficial do Ministério da Saúde."
    ),

    "licensing_note_en": (
        "Locally implemented logic based on an official "
        "public Brazilian Ministry of Health source."
    ),

    "clinical_review_date":
        date(2026, 9, 11),

    "offline_capable":
        True,

    "brazil_applicability_status":
        "national_standard",

    "brazil_review_date":
        date(2026, 9, 11),

    "brazil_authority":
        "Ministério da Saúde / SAPS",

    "brazil_source_title":
        "Caderneta Brasileira da Pessoa Idosa 2026",

    "brazil_source_url":
        CADERNETA_2026_URL,

    "brazil_document_or_portaria":
        "Caderneta Brasileira da Pessoa Idosa 2026",

    "brazil_scope_pt":
        "Check-up nacional de prevenção de quedas para pessoas idosas.",

    "brazil_scope_en":
        "National falls-prevention check-up for older people.",

    "brazil_differs_from_international":
        True,

    "brazil_difference_notes_pt": (
        "A camada brasileira não importa escore "
        "ponderado estrangeiro; qualquer resposta "
        "positiva orienta avaliação."
    ),

    "brazil_difference_notes_en": (
        "The Brazilian layer does not import a foreign "
        "weighted score; any positive response indicates "
        "assessment."
    ),

    "final_brazil_review_status":
        "pass",
}


IVCF20_METADATA = {
    "id":
        "ivcf20",

    "name_pt":
        "IVCF-20",

    "name_en":
        "IVCF-20",

    "description_pt": (
        "Índice nacional de vulnerabilidade clínico-funcional "
        "para pessoas idosas, com pontuação de 0 a 40."
    ),

    "description_en": (
        "Brazilian national clinical-functional vulnerability "
        "index for older people, scored from 0 to 40."
    ),

    "aliases_pt": [
        "IVCF-20",
        "vulnerabilidade clínico-funcional",
        "pessoa idosa",
    ],

    "aliases_en": [
        "IVCF-20",
        "clinical-functional vulnerability",
        "older person",
    ],

    "publisher":
        "Ministério da Saúde / SAPS",

    "source_title": (
        "Caderneta Brasileira da Pessoa Idosa 2026 + "
        "Nota Informativa nº 1/2026-COPID/DGCI/SAPS/MS"
    ),

    "source_version":
        "Brazil national APS implementation reviewed 2026-09-11",

    "source_url":
        IVCF_2026_NOTE_URL,

    "source_language":
        "pt-BR",

    "canonical_language":
        "pt-BR",

    "translation_status_pt":
        "official_original",

    "translation_status_en":
        "informative_translation",

    "translation_disclaimer_required":
        False,

    "translation_disclaimer_source_url":
        None,

    "translation_note_pt": (
        "A pontuação e a interpretação seguem "
        "as fontes oficiais brasileiras."
    ),

    "translation_note_en": (
        "Scoring and interpretation follow current "
        "official Brazilian sources; EN-GB is informational."
    ),

    "population_pt":
        "Pessoas com 60 anos ou mais acompanhadas na APS.",

    "population_en":
        "People aged 60 years or over followed in primary care.",

    "limitations_pt": [
        (
            "O IVCF-20 deve ser preenchido integralmente."
        ),
        (
            "O teste de marcha de 4 metros não é TUG."
        ),
        (
            "A classificação é de vulnerabilidade "
            "clínico-funcional, não de risco isolado de quedas."
        ),
        (
            "Não combinar automaticamente com o check-up "
            "de quedas ou instrumentos STEADI."
        ),
    ],

    "limitations_en": [
        (
            "The IVCF-20 should be completed in full."
        ),
        (
            "The 4-m gait item is not TUG."
        ),
        (
            "The classification concerns clinical-functional "
            "vulnerability, not standalone falls risk."
        ),
        (
            "Do not automatically combine it with the "
            "falls check-up or STEADI instruments."
        ),
    ],

    "licensing_note_pt": (
        "Implementação de cálculo baseada nas fontes "
        "públicas oficiais do Ministério da Saúde."
    ),

    "licensing_note_en": (
        "Calculation implementation based on official "
        "public Brazilian Ministry of Health sources."
    ),

    "clinical_review_date":
        date(2026, 9, 11),

    "offline_capable":
        True,

    "brazil_applicability_status":
        "national_standard",

    "brazil_review_date":
        date(2026, 9, 11),

    "brazil_authority":
        "Ministério da Saúde / SAPS",

    "brazil_source_title": (
        "Caderneta Brasileira da Pessoa Idosa 2026 + "
        "Nota Informativa nº 1/2026-COPID/DGCI/SAPS/MS"
    ),

    "brazil_source_url":
        IVCF_2026_NOTE_URL,

    "brazil_document_or_portaria":
        "Nota Informativa nº 1/2026-COPID/DGCI/SAPS/MS",

    "brazil_scope_pt":
        "Estratificação nacional de vulnerabilidade clínico-funcional na APS.",

    "brazil_scope_en":
        "National clinical-functional vulnerability stratification in primary care.",

    "brazil_differs_from_international":
        False,

    "brazil_difference_notes_pt": (
        "Instrumento brasileiro nacional; não é tratado "
        "como variante de STEADI."
    ),

    "brazil_difference_notes_en": (
        "Brazilian national instrument; it is not treated "
        "as a STEADI variant."
    ),

    "final_brazil_review_status":
        "pass",
}
