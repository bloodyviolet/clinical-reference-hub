"""Royal College of Physicians NEWS2 scoring engine.

The scoring algorithm follows the NEWS2 physiological parameter chart.
Human-readable explanatory text is locally authored and bilingual.

PT-BR material is an informational/local translation and must not be
represented as an RCP-approved translation.
"""

from __future__ import annotations

from datetime import date
from typing import Literal


Consciousness = Literal[
    "alert",
    "new_confusion",
    "voice",
    "pain",
    "unresponsive",
]


SOURCE_URL = (
    "https://www.rcp.ac.uk/resources/"
    "national-early-warning-score-news-2/"
)


def _respiration_score(value: int) -> int:
    if value <= 8:
        return 3
    if value <= 11:
        return 1
    if value <= 20:
        return 0
    if value <= 24:
        return 2
    return 3


def _spo2_scale1_score(value: int) -> int:
    if value <= 91:
        return 3
    if value <= 93:
        return 2
    if value <= 95:
        return 1
    return 0


def _spo2_scale2_score(
    value: int,
    supplemental_oxygen: bool,
) -> int:
    if value <= 83:
        return 3
    if value <= 85:
        return 2
    if value <= 87:
        return 1
    if value <= 92:
        return 0

    # >=93% on room air scores zero.
    if not supplemental_oxygen:
        return 0

    if value <= 94:
        return 1
    if value <= 96:
        return 2
    return 3


def _systolic_bp_score(value: int) -> int:
    if value <= 90:
        return 3
    if value <= 100:
        return 2
    if value <= 110:
        return 1
    if value <= 219:
        return 0
    return 3


def _pulse_score(value: int) -> int:
    if value <= 40:
        return 3
    if value <= 50:
        return 1
    if value <= 90:
        return 0
    if value <= 110:
        return 1
    if value <= 130:
        return 2
    return 3


def _temperature_score(value: float) -> int:
    if value <= 35.0:
        return 3
    if value <= 36.0:
        return 1
    if value <= 38.0:
        return 0
    if value <= 39.0:
        return 1
    return 2


def _clinical_response(
    total: int,
    red_parameter: bool,
) -> dict:
    if total >= 7:
        return {
            "aggregate_band": "high",
            "aggregate_label_pt": "Alto — total ≥7",
            "aggregate_label_en": "High — total ≥7",
            "trigger_code": "high",
            "trigger_label_pt": "Resposta de emergência",
            "trigger_label_en": "Emergency response",
            "monitoring_code": "continuous",
            "monitoring_pt": (
                "Monitorização contínua dos sinais vitais."
            ),
            "monitoring_en": (
                "Continuous monitoring of vital signs."
            ),
            "response_pt": (
                "Avaliação emergencial por equipe com competências "
                "em cuidados críticos e escalonamento conforme "
                "protocolo local."
            ),
            "response_en": (
                "Emergency assessment by a team with critical-care "
                "competencies and escalation according to local policy."
            ),
        }

    if total >= 5:
        return {
            "aggregate_band": "medium",
            "aggregate_label_pt": "Médio — total 5–6",
            "aggregate_label_en": "Medium — total 5–6",
            "trigger_code": "medium",
            "trigger_label_pt": "Resposta urgente",
            "trigger_label_en": "Urgent response",
            "monitoring_code": "minimum_hourly",
            "monitoring_pt": "Monitorização no mínimo a cada 1 hora.",
            "monitoring_en": "Monitoring at least hourly.",
            "response_pt": (
                "Solicitar avaliação clínica urgente por profissional "
                "ou equipe competente no cuidado ao paciente agudamente "
                "enfermo."
            ),
            "response_en": (
                "Request urgent clinical assessment by a clinician "
                "or team competent in acute illness."
            ),
        }

    if red_parameter:
        return {
            "aggregate_band": "low",
            "aggregate_label_pt": "Baixo — total 1–4",
            "aggregate_label_en": "Low — total 1–4",
            "trigger_code": "single_red",
            "trigger_label_pt": "Parâmetro isolado com escore 3",
            "trigger_label_en": "Single parameter score of 3",
            "monitoring_code": "minimum_hourly",
            "monitoring_pt": "Monitorização no mínimo a cada 1 hora.",
            "monitoring_en": "Monitoring at least hourly.",
            "response_pt": (
                "Informar a equipe médica responsável e solicitar "
                "revisão clínica para definir necessidade de "
                "escalonamento."
            ),
            "response_en": (
                "Inform the responsible medical team and request "
                "clinical review to determine whether escalation "
                "is required."
            ),
        }

    if total >= 1:
        return {
            "aggregate_band": "low",
            "aggregate_label_pt": "Baixo — total 1–4",
            "aggregate_label_en": "Low — total 1–4",
            "trigger_code": "low",
            "trigger_label_pt": "Baixo",
            "trigger_label_en": "Low",
            "monitoring_code": "minimum_4_to_6_hourly",
            "monitoring_pt": (
                "Monitorização no mínimo a cada 4–6 horas."
            ),
            "monitoring_en": (
                "Monitoring at least every 4–6 hours."
            ),
            "response_pt": (
                "Avaliação por enfermeiro e decisão clínica quanto "
                "à frequência de observações ou necessidade de "
                "escalonamento."
            ),
            "response_en": (
                "Registered-nurse assessment and clinical decision "
                "on observation frequency or escalation."
            ),
        }

    return {
        "aggregate_band": "zero",
        "aggregate_label_pt": "NEWS2 total 0",
        "aggregate_label_en": "NEWS2 total 0",
        "trigger_code": "zero",
        "trigger_label_pt": "Monitorização de rotina",
        "trigger_label_en": "Routine monitoring",
        "monitoring_code": "minimum_12_hourly",
        "monitoring_pt": (
            "Monitorização no mínimo a cada 12 horas."
        ),
        "monitoring_en": (
            "Monitoring at least every 12 hours."
        ),
        "response_pt": (
            "Manter monitorização NEWS2 de rotina conforme "
            "protocolo local."
        ),
        "response_en": (
            "Continue routine NEWS2 monitoring according "
            "to local policy."
        ),
    }


def calculate_news2(
    *,
    respiration_rate: int,
    spo2: int,
    spo2_scale: int,
    scale2_prescribed: bool,
    supplemental_oxygen: bool,
    systolic_bp: int,
    pulse: int,
    consciousness: Consciousness,
    temperature: float,
) -> dict:
    """Calculate a complete NEWS2 observation set."""

    if respiration_rate <= 0:
        raise ValueError(
            "respiration_rate must be greater than zero."
        )

    if not 1 <= spo2 <= 100:
        raise ValueError(
            "spo2 must be between 1 and 100 percent."
        )

    if spo2_scale not in {1, 2}:
        raise ValueError(
            "spo2_scale must be 1 or 2."
        )

    if spo2_scale == 2 and not scale2_prescribed:
        raise ValueError(
            "SpO2 Scale 2 requires an explicitly prescribed "
            "88-92% target under qualified clinical direction."
        )

    if systolic_bp <= 0:
        raise ValueError(
            "systolic_bp must be greater than zero."
        )

    if pulse <= 0:
        raise ValueError(
            "pulse must be greater than zero."
        )

    if consciousness not in {
        "alert",
        "new_confusion",
        "voice",
        "pain",
        "unresponsive",
    }:
        raise ValueError(
            "Invalid consciousness value."
        )

    if not 20.0 <= temperature <= 50.0:
        raise ValueError(
            "temperature must be between 20.0 and 50.0 C."
        )

    spo2_score = (
        _spo2_scale1_score(spo2)
        if spo2_scale == 1
        else _spo2_scale2_score(
            spo2,
            supplemental_oxygen,
        )
    )

    components = {
        "respiration_rate":
            _respiration_score(respiration_rate),
        "spo2": spo2_score,
        "supplemental_oxygen":
            2 if supplemental_oxygen else 0,
        "systolic_bp":
            _systolic_bp_score(systolic_bp),
        "pulse":
            _pulse_score(pulse),
        "consciousness":
            0 if consciousness == "alert" else 3,
        "temperature":
            _temperature_score(temperature),
    }

    total = sum(components.values())

    red_parameter = any(
        score == 3
        for name, score in components.items()
        if name != "supplemental_oxygen"
    )

    response = _clinical_response(
        total,
        red_parameter,
    )

    return {
        "tool": "news2",
        "total": total,
        "components": components,
        "spo2_scale": spo2_scale,
        "scale2_prescribed": scale2_prescribed,
        "supplemental_oxygen": supplemental_oxygen,
        "single_parameter_red_score": red_parameter,
        "clinical_judgement_note_pt": (
            "O NEWS2 complementa, mas não substitui, "
            "o julgamento clínico."
        ),
        "clinical_judgement_note_en": (
            "NEWS2 supplements, but does not replace, "
            "clinical judgement."
        ),
        **response,
    }


NEWS2_METADATA = {
    "id": "news2",
    "name_pt": "National Early Warning Score 2 (NEWS2)",
    "name_en": "National Early Warning Score 2 (NEWS2)",
    "description_pt": (
        "Escore de alerta precoce para identificação e "
        "comunicação de deterioração clínica aguda."
    ),
    "description_en": (
        "Early warning score for identifying and communicating "
        "acute clinical deterioration."
    ),
    "aliases_pt": [
        "NEWS2",
        "escore de alerta precoce",
        "deterioração clínica",
    ],
    "aliases_en": [
        "NEWS2",
        "National Early Warning Score 2",
        "clinical deterioration",
        "early warning score",
    ],
    "publisher": "Royal College of Physicians",
    "source_title": (
        "National Early Warning Score (NEWS) 2: "
        "Standardising the assessment of acute-illness "
        "severity in the NHS"
    ),
    "source_version": (
        "NEWS2, December 2017; additional implementation "
        "guidance, April 2021"
    ),
    "source_url": SOURCE_URL,
    "source_language": "en-GB",
    "canonical_language": "en-GB",
    "translation_status_pt":
        "local_translation_with_disclaimer_required",
    "translation_status_en":
        "official_original",
    "translation_disclaimer_required": True,
    "translation_disclaimer_source_url": SOURCE_URL,
    "translation_note_pt": (
        "A apresentação PT-BR é uma tradução local informativa "
        "e não deve ser apresentada como tradução aprovada pelo RCP. "
        "Consulte o original em inglês antes do uso clínico."
    ),
    "translation_note_en": (
        "The PT-BR presentation is a local informational "
        "translation and must not be represented as RCP-approved."
    ),
    "population_pt": (
        "Adultos com 16 anos ou mais em contextos de "
        "avaliação de doença aguda."
    ),
    "population_en": (
        "Adults aged 16 years or older in acute-illness "
        "assessment contexts."
    ),
    "limitations_pt": [
        (
            "Não utilizar em crianças menores de 16 anos."
        ),
        (
            "O NEWS2 não foi validado para uso rotineiro durante "
            "a gestação. O relatório RCP 2017 informa que NEWS "
            "pode ser utilizado até 20 semanas; após 20 semanas, "
            "deve ser utilizado um sistema obstétrico específico."
        ),
        (
            "A Escala SpO2 2 exige alvo de 88–92% explicitamente "
            "definido sob direção clínica qualificada."
        ),
        (
            "O NEWS2 complementa e não substitui o "
            "julgamento clínico."
        ),
    ],
    "limitations_en": [
        "Do not use in children younger than 16 years.",
        (
            "NEWS2 has not been validated for routine use during "
            "pregnancy. The RCP 2017 report states that NEWS may "
            "be used up to 20 weeks; after 20 weeks, a specific "
            "obstetric early-warning system should be used."
        ),
        (
            "SpO2 Scale 2 requires an explicitly prescribed "
            "88–92% target under qualified clinical direction."
        ),
        (
            "NEWS2 supplements and does not replace "
            "clinical judgement."
        ),
    ],
    "licensing_note_pt": (
        "O RCP permite reprodução do NEWS2 sob condições "
        "específicas de atribuição, integridade do material "
        "e tratamento de traduções."
    ),
    "licensing_note_en": (
        "The RCP permits NEWS2 reproduction subject to "
        "specific attribution, integrity and translation "
        "conditions."
    ),
    "clinical_review_date": date(2026, 9, 10),
    "offline_capable": True,
}
