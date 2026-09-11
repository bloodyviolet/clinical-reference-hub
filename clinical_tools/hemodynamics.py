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


BRAZIL_OBSTETRIC_SI_URL = (
    "https://bvsms.saude.gov.br/bvs/publicacoes/"
    "linha_cuidados_doenca_trofoblastica_gestacional.pdf"
)

BRAZIL_ANS_SEPSIS_URL = (
    "https://www.gov.br/ans/pt-br/centrais-de-conteudo/"
    "projeto-indicadores-manual-metodolgico-"
    "linhas-de-cuidado-3-2-pdf"
)


HEMODYNAMIC_CONTEXTS = {
    "none",
    "septic_shock",
    "obstetric_hemorrhage",
}


def calculate_hemodynamics(
    *,
    systolic_bp: float,
    diastolic_bp: float,
    heart_rate: float,
    clinical_context: str = "none",
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

    if clinical_context not in HEMODYNAMIC_CONTEXTS:
        raise ValueError(
            "clinical_context must be one of: "
            "none, septic_shock, obstetric_hemorrhage."
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

    brazil_context_guidance_applied = False

    brazil_context_rule_code = "none"
    brazil_context_threshold_value = None
    brazil_context_threshold_unit = None
    brazil_context_operator = None
    brazil_context_observed_value = None
    brazil_context_rule_met = None

    brazil_context_label_pt = (
        "Sem contexto brasileiro específico selecionado"
    )

    brazil_context_label_en = (
        "No specific Brazilian clinical context selected"
    )

    brazil_context_interpretation_pt = (
        "Nenhum limiar brasileiro dependente de contexto "
        "foi aplicado ao resultado genérico."
    )

    brazil_context_interpretation_en = (
        "No context-dependent Brazilian threshold was "
        "applied to the generic result."
    )

    if clinical_context == "septic_shock":
        brazil_context_guidance_applied = True

        brazil_context_rule_code = (
            "septic_shock_map_target"
        )

        brazil_context_threshold_value = 65.0
        brazil_context_threshold_unit = "mmHg"
        brazil_context_operator = ">="

        brazil_context_observed_value = round(
            mean_arterial_pressure,
            4,
        )

        brazil_context_rule_met = (
            mean_arterial_pressure
            >= 65.0
        )

        brazil_context_label_pt = (
            "Contexto brasileiro — choque séptico"
        )

        brazil_context_label_en = (
            "Brazilian context — septic shock"
        )

        if brazil_context_rule_met:
            brazil_context_interpretation_pt = (
                "No contexto explicitamente selecionado de "
                "choque séptico, a PAM calculada está em ou "
                "acima de 65 mmHg. Este é um alvo contextual "
                "de manejo e não um limite universal de PAM; "
                "não estabelece nem exclui diagnóstico."
            )

            brazil_context_interpretation_en = (
                "In the explicitly selected septic-shock "
                "context, calculated MAP is at or above "
                "65 mmHg. This is a contextual management "
                "target rather than a universal MAP limit; "
                "it neither establishes nor excludes diagnosis."
            )

        else:
            brazil_context_interpretation_pt = (
                "No contexto explicitamente selecionado de "
                "choque séptico, a PAM calculada está abaixo "
                "de 65 mmHg. Este é um limiar contextual de "
                "manejo e não uma classificação universal "
                "de PAM; integrar ao protocolo e quadro clínico."
            )

            brazil_context_interpretation_en = (
                "In the explicitly selected septic-shock "
                "context, calculated MAP is below 65 mmHg. "
                "This is a contextual management threshold, "
                "not a universal MAP classification; integrate "
                "with the protocol and clinical picture."
            )

    elif clinical_context == "obstetric_hemorrhage":
        brazil_context_guidance_applied = True

        brazil_context_rule_code = (
            "obstetric_hemorrhage_si_trigger"
        )

        brazil_context_threshold_value = 0.9
        brazil_context_threshold_unit = "ratio"
        brazil_context_operator = ">"

        brazil_context_observed_value = round(
            shock_index,
            4,
        )

        # The Ministry source says "acima de 0,9":
        # preserve the strict > operator.
        brazil_context_rule_met = (
            shock_index
            > 0.9
        )

        brazil_context_label_pt = (
            "Contexto brasileiro — hemorragia obstétrica"
        )

        brazil_context_label_en = (
            "Brazilian context — obstetric haemorrhage"
        )

        if brazil_context_rule_met:
            brazil_context_interpretation_pt = (
                "No contexto explicitamente selecionado de "
                "hemorragia obstétrica, o Shock Index está "
                "acima de 0,9, limiar descrito pelo Ministério "
                "da Saúde para acionamento do protocolo de "
                "hemorragia obstétrica. Não aplicar este "
                "limiar como corte universal de Shock Index."
            )

            brazil_context_interpretation_en = (
                "In the explicitly selected obstetric-"
                "haemorrhage context, Shock Index is above "
                "0.9, the Ministry of Health threshold "
                "described for activation of the obstetric "
                "haemorrhage protocol. Do not apply this as "
                "a universal Shock Index cut-off."
            )

        else:
            brazil_context_interpretation_pt = (
                "No contexto explicitamente selecionado de "
                "hemorragia obstétrica, o Shock Index não está "
                "acima de 0,9. Isso não exclui hemorragia, "
                "choque ou necessidade de escalonamento "
                "segundo avaliação clínica e protocolo."
            )

            brazil_context_interpretation_en = (
                "In the explicitly selected obstetric-"
                "haemorrhage context, Shock Index is not "
                "above 0.9. This does not exclude haemorrhage, "
                "shock, or need for escalation according to "
                "clinical assessment and protocol."
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
        "universal_threshold_inference_applied":
            False,
        "clinical_context":
            clinical_context,
        "brazil_context_guidance_applied":
            brazil_context_guidance_applied,
        "brazil_context_rule_code":
            brazil_context_rule_code,
        "brazil_context_threshold_value":
            brazil_context_threshold_value,
        "brazil_context_threshold_unit":
            brazil_context_threshold_unit,
        "brazil_context_operator":
            brazil_context_operator,
        "brazil_context_observed_value":
            brazil_context_observed_value,
        "brazil_context_rule_met":
            brazil_context_rule_met,
        "brazil_context_label_pt":
            brazil_context_label_pt,
        "brazil_context_label_en":
            brazil_context_label_en,
        "brazil_context_interpretation_pt":
            brazil_context_interpretation_pt,
        "brazil_context_interpretation_en":
            brazil_context_interpretation_en,
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
    "brazil_applicability_status":
        "complementary_brazil_guidance",
    "brazil_review_date":
        date(2026, 9, 11),
    "brazil_authority":
        "Ministério da Saúde / ANS",
    "brazil_source_title": (
        "Orientações federais contextuais para PAM em "
        "choque séptico e Shock Index em hemorragia obstétrica"
    ),
    "brazil_source_url":
        BRAZIL_OBSTETRIC_SI_URL,
    "brazil_document_or_portaria":
        None,
    "brazil_scope_pt": (
        "Limiar de PAM em choque séptico e Shock Index em "
        "hemorragia obstétrica são apresentados somente em "
        "contextos clínicos explicitamente selecionados."
    ),
    "brazil_scope_en": (
        "MAP guidance in septic shock and Shock Index guidance "
        "in obstetric haemorrhage are exposed only in explicitly "
        "selected clinical contexts."
    ),
    "brazil_differs_from_international":
        False,
    "brazil_difference_notes_pt": (
        "As fórmulas genéricas permanecem neutras. PAM 65 mmHg "
        "e Shock Index 0,9 não são convertidos em pontos de "
        "corte universais; não há limiar brasileiro universal "
        "de MSI ou pressão de pulso identificado."
    ),
    "brazil_difference_notes_en": (
        "Generic formulae remain neutral. MAP 65 mmHg and "
        "Shock Index 0.9 are not converted into universal "
        "cut-offs; no Brazilian universal MSI or pulse-pressure "
        "threshold was identified."
    ),
    "final_brazil_review_status":
        "pass",
}
