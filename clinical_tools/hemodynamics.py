"""Adult bedside haemodynamic calculations.

Calculations:

- Pulse pressure = SBP - DBP
- Approximate MAP = DBP + 1/3(SBP - DBP)
- Shock Index = HR / SBP
- Modified Shock Index = HR / MAP

No universal SI/MSI prognostic threshold is applied because published
cut-points and reference distributions vary by population and clinical
condition.
"""

from __future__ import annotations

from datetime import date


MAP_SOURCE_URL = (
    "https://www.ncbi.nlm.nih.gov/books/NBK493197/"
)

SI_SOURCE_URL = (
    "https://pubmed.ncbi.nlm.nih.gov/31616192/"
)

MSI_SOURCE_URL = (
    "https://pubmed.ncbi.nlm.nih.gov/37215239/"
)


def calculate_hemodynamics(
    *,
    systolic_bp: float,
    diastolic_bp: float,
    heart_rate: float,
) -> dict:
    """Calculate basic non-invasive haemodynamic indices."""

    values = {
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "heart_rate": heart_rate,
    }

    for name, value in values.items():
        if value <= 0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

    if systolic_bp < diastolic_bp:
        raise ValueError(
            "systolic_bp cannot be lower than diastolic_bp."
        )

    pulse_pressure = (
        systolic_bp
        - diastolic_bp
    )

    mean_arterial_pressure = (
        diastolic_bp
        + pulse_pressure / 3.0
    )

    shock_index = (
        heart_rate
        / systolic_bp
    )

    modified_shock_index = (
        heart_rate
        / mean_arterial_pressure
    )

    return {
        "tool": "hemodynamics",
        "systolic_bp_mm_hg":
            round(systolic_bp, 1),
        "diastolic_bp_mm_hg":
            round(diastolic_bp, 1),
        "heart_rate_bpm":
            round(heart_rate, 1),
        "pulse_pressure_mm_hg":
            round(pulse_pressure, 1),
        "mean_arterial_pressure_mm_hg":
            round(
                mean_arterial_pressure,
                1,
            ),
        "shock_index":
            round(shock_index, 3),
        "modified_shock_index":
            round(
                modified_shock_index,
                3,
            ),
        "map_method":
            "DBP + 1/3(SBP - DBP)",
        "pulse_pressure_method":
            "SBP - DBP",
        "shock_index_method":
            "HR / SBP",
        "modified_shock_index_method":
            "HR / MAP",
        "threshold_classification_applied":
            False,
        "interpretation_pt": (
            "Os índices são auxiliares de avaliação hemodinâmica "
            "e devem ser interpretados junto ao contexto clínico, "
            "tendência dos sinais vitais, perfusão e comorbidades. "
            "Não foi aplicado um ponto de corte universal para "
            "Shock Index ou Modified Shock Index."
        ),
        "interpretation_en": (
            "These indices are adjuncts to haemodynamic assessment "
            "and should be interpreted with the clinical context, "
            "vital-sign trends, perfusion and comorbidities. "
            "No universal Shock Index or Modified Shock Index "
            "cut-off has been applied."
        ),
        "map_note_pt": (
            "A PAM calculada é uma aproximação baseada em PAS/PAD "
            "e não substitui a PAM derivada diretamente da curva "
            "arterial quando esta estiver disponível."
        ),
        "map_note_en": (
            "Calculated MAP is an approximation derived from "
            "SBP/DBP and does not replace MAP obtained directly "
            "from an arterial waveform when available."
        ),
    }


HEMODYNAMICS_METADATA = {
    "id": "hemodynamics",
    "name_pt": (
        "Hemodinâmica — PAM, pressão de pulso, "
        "Shock Index e Modified Shock Index"
    ),
    "name_en": (
        "Haemodynamics — MAP, pulse pressure, "
        "Shock Index and Modified Shock Index"
    ),
    "description_pt": (
        "Cálculos hemodinâmicos à beira-leito a partir de "
        "pressão arterial sistólica, diastólica e frequência cardíaca."
    ),
    "description_en": (
        "Bedside haemodynamic calculations from systolic blood "
        "pressure, diastolic blood pressure and heart rate."
    ),
    "aliases_pt": [
        "PAM",
        "pressão arterial média",
        "pressão de pulso",
        "índice de choque",
        "Shock Index",
        "Modified Shock Index",
        "MSI",
    ],
    "aliases_en": [
        "MAP",
        "mean arterial pressure",
        "pulse pressure",
        "shock index",
        "modified shock index",
        "MSI",
    ],
    "publisher": (
        "NCBI Bookshelf / PubMed-indexed literature"
    ),
    "source_title": (
        "Cardiovascular physiology and shock-index literature"
    ),
    "source_version": (
        "MAP/pulse-pressure physiology; SI/MSI definitions "
        "reviewed 2026-09-11"
    ),
    "source_url": MAP_SOURCE_URL,
    "source_language": "en",
    "canonical_language": "en",
    "translation_status_pt":
        "local_translation",
    "translation_status_en":
        "informative_translation",
    "translation_disclaimer_required":
        False,
    "translation_disclaimer_source_url":
        None,
    "translation_note_pt": (
        "Explicações PT-BR são redação clínica local; "
        "as fórmulas matemáticas permanecem inalteradas."
    ),
    "translation_note_en": (
        "EN-GB explanations are locally authored; "
        "the mathematical formulae are unchanged."
    ),
    "population_pt": (
        "Adultos em avaliação hemodinâmica à beira-leito."
    ),
    "population_en": (
        "Adults undergoing bedside haemodynamic assessment."
    ),
    "limitations_pt": [
        (
            "A PAM calculada por PAS/PAD é uma aproximação e "
            "pode divergir da PAM derivada da curva arterial."
        ),
        (
            "Shock Index e Modified Shock Index não estabelecem "
            "diagnóstico de choque isoladamente."
        ),
        (
            "Pontos de corte prognósticos de SI/MSI variam conforme "
            "idade, população e condição clínica; este módulo não "
            "aplica um limiar universal."
        ),
        (
            "Fármacos, arritmias, marca-passo, estado fisiológico "
            "e técnica de aferição podem alterar a interpretação."
        ),
    ],
    "limitations_en": [
        (
            "MAP calculated from SBP/DBP is an approximation and "
            "may differ from arterial-waveform-derived MAP."
        ),
        (
            "Shock Index and Modified Shock Index do not establish "
            "a diagnosis of shock in isolation."
        ),
        (
            "Prognostic SI/MSI cut-offs vary by age, population "
            "and clinical condition; this module does not apply "
            "a universal threshold."
        ),
        (
            "Medication, arrhythmia, pacing, physiological state "
            "and measurement technique can affect interpretation."
        ),
    ],
    "licensing_note_pt": (
        "Fórmulas implementadas como cálculos matemáticos com "
        "explicações clínicas próprias e referências públicas."
    ),
    "licensing_note_en": (
        "Formulae implemented as mathematical calculations with "
        "locally authored clinical explanations and public references."
    ),
    "clinical_review_date":
        date(2026, 9, 11),
    "offline_capable":
        True,
}
