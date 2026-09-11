"""Brazil Ministry methanol/toxicology context calculations.

This module is intentionally isolated from the generic acid-base
toolkit.

It implements source-specific calculations from the Brazilian Ministry
methanol workflow and must never silently replace general metabolic
formulae.

Important unit contract:
- sodium, potassium, chloride, bicarbonate: mmol/L;
- glucose: mmol/L;
- urea: mmol/L;
- measured osmolality: mOsm/kg.

Urea is not BUN. mg/dL values must not be silently reused here.
"""

from __future__ import annotations

from datetime import date
import math


_FLOAT_ABS_TOL = 1e-9


MINISTRY_JOINT_NOTE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "centrais-de-conteudo/publicacoes/notas-tecnicas/"
    "2025/nota-tecnica-conjunta-no-376-2025-"
    "svsa-saes-sectics-ms.pdf/view"
)

MINISTRY_METHANOL_FLOWCHART_URL = (
    "https://www.gov.br/saude/pt-br/"
    "composicao/saes/publicacoes/"
    "fluxograma-metanol.pdf/view"
)


def _strictly_above(
    value: float,
    threshold: float,
) -> bool:
    return (
        value > threshold
        and not math.isclose(
            value,
            threshold,
            rel_tol=0.0,
            abs_tol=_FLOAT_ABS_TOL,
        )
    )


def calculate_brazil_methanol_context(
    *,
    explicit_methanol_context: bool,
    sodium_mmol_l: float,
    potassium_mmol_l: float | None = None,
    chloride_mmol_l: float | None = None,
    bicarbonate_mmol_l: float | None = None,
    glucose_mmol_l: float | None = None,
    urea_mmol_l: float | None = None,
    measured_osmolality_mosm_kg: float | None = None,
) -> dict:
    """Calculate explicitly selected Ministry methanol context."""

    if explicit_methanol_context is not True:
        raise ValueError(
            "explicit_methanol_context must be true."
        )

    if sodium_mmol_l <= 0:
        raise ValueError(
            "sodium_mmol_l must be greater than zero."
        )

    ag_fields = (
        potassium_mmol_l,
        chloride_mmol_l,
        bicarbonate_mmol_l,
    )

    ag_count = sum(
        value is not None
        for value in ag_fields
    )

    if ag_count not in {0, 3}:
        raise ValueError(
            "potassium_mmol_l, chloride_mmol_l and "
            "bicarbonate_mmol_l must be supplied together "
            "for the Ministry methanol anion gap."
        )

    for name, value in (
        (
            "potassium_mmol_l",
            potassium_mmol_l,
        ),
        (
            "chloride_mmol_l",
            chloride_mmol_l,
        ),
        (
            "bicarbonate_mmol_l",
            bicarbonate_mmol_l,
        ),
    ):
        if (
            value is not None
            and value <= 0
        ):
            raise ValueError(
                f"{name} must be greater than zero."
            )

    glucose_present = (
        glucose_mmol_l is not None
    )

    urea_present = (
        urea_mmol_l is not None
    )

    if glucose_present != urea_present:
        raise ValueError(
            "glucose_mmol_l and urea_mmol_l must be "
            "supplied together for the Ministry calculated "
            "osmolality."
        )

    if (
        glucose_mmol_l is not None
        and glucose_mmol_l < 0
    ):
        raise ValueError(
            "glucose_mmol_l cannot be negative."
        )

    if (
        urea_mmol_l is not None
        and urea_mmol_l < 0
    ):
        raise ValueError(
            "urea_mmol_l cannot be negative."
        )

    if (
        measured_osmolality_mosm_kg is not None
        and measured_osmolality_mosm_kg <= 0
    ):
        raise ValueError(
            "measured_osmolality_mosm_kg must be "
            "greater than zero."
        )

    if (
        measured_osmolality_mosm_kg is not None
        and not glucose_present
    ):
        raise ValueError(
            "Measured osmolality requires glucose_mmol_l "
            "and urea_mmol_l so the Ministry calculated "
            "osmolality and osmolar gap can be derived."
        )

    if (
        ag_count == 0
        and not glucose_present
    ):
        raise ValueError(
            "Supply the complete methanol anion-gap inputs "
            "and/or glucose_mmol_l + urea_mmol_l."
        )

    ministry_anion_gap = None

    if ag_count == 3:
        assert potassium_mmol_l is not None
        assert chloride_mmol_l is not None
        assert bicarbonate_mmol_l is not None

        ministry_anion_gap = (
            sodium_mmol_l
            + potassium_mmol_l
            - bicarbonate_mmol_l
            - chloride_mmol_l
        )

    ministry_calculated_osmolality = None

    if glucose_present:
        assert glucose_mmol_l is not None
        assert urea_mmol_l is not None

        ministry_calculated_osmolality = (
            (
                glucose_mmol_l
                + urea_mmol_l
                + 1.86 * sodium_mmol_l
            )
            / 0.93
        )

    osmolar_gap = None

    if (
        measured_osmolality_mosm_kg is not None
        and ministry_calculated_osmolality is not None
    ):
        osmolar_gap = (
            measured_osmolality_mosm_kg
            - ministry_calculated_osmolality
        )

    anion_gap_gt_12 = (
        _strictly_above(
            ministry_anion_gap,
            12.0,
        )
        if ministry_anion_gap is not None
        else None
    )

    osmolar_gap_gt_10 = (
        _strictly_above(
            osmolar_gap,
            10.0,
        )
        if osmolar_gap is not None
        else None
    )

    osmolar_gap_gt_25 = (
        _strictly_above(
            osmolar_gap,
            25.0,
        )
        if osmolar_gap is not None
        else None
    )

    notes_pt = [
        (
            "Contexto toxicológico de metanol foi selecionado "
            "explicitamente; este cálculo não substitui o "
            "painel metabólico geral."
        ),
        (
            "A fórmula toxicológica do ânion gap inclui "
            "potássio."
        ),
        (
            "A osmolalidade calculada deste contexto usa "
            "glicose e ureia em mmol/L; ureia não é BUN."
        ),
        (
            "Gap osmolar só é calculado quando a osmolalidade "
            "medida é informada."
        ),
        (
            "Os limiares de gap são orientação contextual e "
            "não estabelecem diagnóstico isoladamente."
        ),
        (
            "Gap osmolar normal não exclui intoxicação por "
            "metanol em apresentação tardia."
        ),
    ]

    notes_en = [
        (
            "Methanol toxicology context was explicitly "
            "selected; this calculation does not replace the "
            "general metabolic toolkit."
        ),
        (
            "The toxicology anion-gap formula includes "
            "potassium."
        ),
        (
            "Calculated osmolality in this context uses "
            "glucose and urea in mmol/L; urea is not BUN."
        ),
        (
            "Osmolar gap is calculated only when measured "
            "osmolality is explicitly supplied."
        ),
        (
            "Gap thresholds are contextual guidance and do "
            "not independently establish a diagnosis."
        ),
        (
            "A normal osmolar gap does not exclude late "
            "methanol poisoning."
        ),
    ]

    return {
        "tool":
            "brazil_methanol_context",

        "explicit_methanol_context":
            True,

        "sodium_mmol_l":
            round(
                sodium_mmol_l,
                2,
            ),

        "potassium_mmol_l":
            (
                round(
                    potassium_mmol_l,
                    2,
                )
                if potassium_mmol_l is not None
                else None
            ),

        "chloride_mmol_l":
            (
                round(
                    chloride_mmol_l,
                    2,
                )
                if chloride_mmol_l is not None
                else None
            ),

        "bicarbonate_mmol_l":
            (
                round(
                    bicarbonate_mmol_l,
                    2,
                )
                if bicarbonate_mmol_l is not None
                else None
            ),

        "glucose_mmol_l":
            (
                round(
                    glucose_mmol_l,
                    2,
                )
                if glucose_mmol_l is not None
                else None
            ),

        "urea_mmol_l":
            (
                round(
                    urea_mmol_l,
                    2,
                )
                if urea_mmol_l is not None
                else None
            ),

        "measured_osmolality_mosm_kg":
            (
                round(
                    measured_osmolality_mosm_kg,
                    2,
                )
                if measured_osmolality_mosm_kg is not None
                else None
            ),

        "ministry_anion_gap_mmol_l":
            (
                round(
                    ministry_anion_gap,
                    2,
                )
                if ministry_anion_gap is not None
                else None
            ),

        "ministry_anion_gap_formula":
            "(Na + K) - (HCO3 + Cl)",

        "ministry_anion_gap_potassium_included":
            True,

        "anion_gap_gt_12":
            anion_gap_gt_12,

        "ministry_calculated_osmolality_mosm_kg":
            (
                round(
                    ministry_calculated_osmolality,
                    2,
                )
                if ministry_calculated_osmolality is not None
                else None
            ),

        "ministry_calculated_osmolality_formula":
            "(glucose + urea + (1.86 * sodium)) / 0.93",

        "ministry_osmolality_input_unit":
            "mmol/L",

        "ministry_osmolality_uses_urea_not_bun":
            True,

        "osmolar_gap_mosm_kg":
            (
                round(
                    osmolar_gap,
                    2,
                )
                if osmolar_gap is not None
                else None
            ),

        "osmolar_gap_formula":
            (
                "measured osmolality - "
                "Ministry calculated osmolality"
            ),

        "osmolar_gap_calculation_applied":
            osmolar_gap is not None,

        "osmolar_gap_gt_10":
            osmolar_gap_gt_10,

        "osmolar_gap_gt_25":
            osmolar_gap_gt_25,

        "normal_osmolar_gap_excludes_late_poisoning":
            False,

        "methanol_diagnosis_applied":
            False,

        "automatic_toxicology_context_inference_applied":
            False,

        "thresholds_contextual_only":
            True,

        "urea_bun_substitution_applied":
            False,

        "unit_domain_mixed":
            False,

        "validity_notes_pt":
            notes_pt,

        "validity_notes_en":
            notes_en,

        "interpretation_pt": (
            "Resultados do contexto brasileiro de intoxicação "
            "por metanol são apoio ao fluxo clínico do "
            "Ministério da Saúde. História, quadro clínico, "
            "tempo de exposição, gasometria, exames diretos "
            "quando disponíveis e discussão com CIATox "
            "permanecem necessários."
        ),

        "interpretation_en": (
            "Results from the Brazilian methanol-poisoning "
            "context support the Ministry of Health clinical "
            "workflow. Exposure history, clinical findings, "
            "timing, blood gas data, direct testing when "
            "available and CIATox consultation remain relevant."
        ),
    }


METHANOL_METADATA = {
    "id":
        "brazil-methanol-context",

    "name_pt":
        "Contexto SUS · intoxicação por metanol",

    "name_en":
        "Brazil SUS · methanol poisoning context",

    "description_pt": (
        "Cálculos toxicológicos específicos do fluxo federal "
        "de intoxicação por metanol, separados do painel "
        "metabólico geral."
    ),

    "description_en": (
        "Toxicology-specific calculations from the Brazilian "
        "federal methanol-poisoning workflow, isolated from "
        "the general metabolic toolkit."
    ),

    "aliases_pt": [
        "metanol",
        "gap osmolar",
        "ânion gap com potássio",
        "intoxicação por álcool tóxico",
        "CIATox",
    ],

    "aliases_en": [
        "methanol",
        "osmolar gap",
        "anion gap with potassium",
        "toxic alcohol poisoning",
        "CIATox",
    ],

    "publisher":
        "Ministério da Saúde / SVSA / SAES / SECTICS",

    "source_title": (
        "Nota Técnica Conjunta nº 376/2025-"
        "SVSA/SAES/SECTICS/MS + Fluxograma SAES "
        "de manejo da intoxicação por metanol"
    ),

    "source_version":
        "Federal methanol guidance reviewed 2026-09-11",

    "source_url":
        MINISTRY_JOINT_NOTE_URL,

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
        "O conteúdo clínico-fonte é brasileiro e em português; "
        "as descrições PT-BR preservam a distinção entre o "
        "fluxo toxicológico e o painel metabólico geral."
    ),

    "translation_note_en": (
        "The clinical source material is Brazilian Portuguese; "
        "EN-GB text is an informative local translation."
    ),

    "population_pt": (
        "Pacientes com suspeita clínica explicitamente "
        "selecionada de intoxicação por metanol."
    ),

    "population_en": (
        "Patients with an explicitly selected clinical "
        "context of suspected methanol poisoning."
    ),

    "limitations_pt": [
        (
            "O cálculo não diagnostica intoxicação por "
            "metanol isoladamente."
        ),
        (
            "Gap osmolar requer osmolalidade medida."
        ),
        (
            "A fórmula de osmolalidade deste contexto usa "
            "glicose e ureia em mmol/L; ureia não é BUN."
        ),
        (
            "Gap osmolar normal não exclui apresentação tardia."
        ),
        (
            "Os limiares exibidos pertencem ao fluxo "
            "toxicológico e não são referências metabólicas "
            "universais."
        ),
    ],

    "limitations_en": [
        (
            "The calculation does not independently diagnose "
            "methanol poisoning."
        ),
        (
            "Osmolar gap requires measured osmolality."
        ),
        (
            "This context's osmolality formula uses glucose "
            "and urea in mmol/L; urea is not BUN."
        ),
        (
            "A normal osmolar gap does not exclude a late "
            "presentation."
        ),
        (
            "Displayed thresholds belong to the toxicology "
            "workflow and are not universal metabolic "
            "reference ranges."
        ),
    ],

    "licensing_note_pt": (
        "Implementação matemática própria baseada em fonte "
        "pública oficial do Ministério da Saúde."
    ),

    "licensing_note_en": (
        "Locally implemented mathematics based on an official "
        "public Brazilian Ministry of Health source."
    ),

    "clinical_review_date":
        date(2026, 9, 11),

    "offline_capable":
        True,

    "brazil_applicability_status":
        "complementary_brazil_guidance",

    "brazil_review_date":
        date(2026, 9, 11),

    "brazil_authority": (
        "Ministério da Saúde / SVSA / SAES / SECTICS"
    ),

    "brazil_source_title": (
        "Nota Técnica Conjunta nº 376/2025 + "
        "Fluxograma SAES de metanol"
    ),

    "brazil_source_url":
        MINISTRY_METHANOL_FLOWCHART_URL,

    "brazil_document_or_portaria":
        "Nota Técnica Conjunta nº 376/2025",

    "brazil_scope_pt": (
        "Contexto toxicológico federal específico; não "
        "substitui o painel metabólico geral."
    ),

    "brazil_scope_en": (
        "Specific federal toxicology context; it does not "
        "replace the general metabolic toolkit."
    ),

    "brazil_differs_from_international":
        True,

    "brazil_difference_notes_pt": (
        "O fluxo de metanol inclui potássio no ânion gap e "
        "usa convenção própria de osmolalidade em mmol/L."
    ),

    "brazil_difference_notes_en": (
        "The methanol workflow includes potassium in the "
        "anion gap and uses its own mmol/L osmolality "
        "convention."
    ),

    "final_brazil_review_status":
        "pass",
}
