"""Acid-base and metabolic bedside calculations.

Included:
- Anion gap without potassium: Na - (Cl + HCO3)
- Albumin-corrected anion gap:
  AG + 2.5 * (4 - albumin[g/dL])
- Calculated serum osmolality:
  2*Na + glucose/18 + BUN/2.8
- Hyperglycaemia-corrected sodium using the 1.6 mmol/L
  per 100 mg/dL glucose above 100 convention
- Winter expected PaCO2:
  1.5*HCO3 + 8 ± 2
- Delta ratio:
  (AG - 12) / (24 - HCO3)

Compensation and delta interpretation are intentionally gated behind
explicit confirmation of metabolic acidosis. This module does not infer
the primary acid-base disorder from chemistry values alone.
"""

from __future__ import annotations

from datetime import date
import math


_FLOAT_ABS_TOL = 1e-9


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


def calculate_metabolic_toolkit(
    *,
    sodium_meq_l: float,
    chloride_meq_l: float | None = None,
    bicarbonate_meq_l: float | None = None,
    albumin_g_dl: float | None = None,
    glucose_mg_dl: float | None = None,
    bun_mg_dl: float | None = None,
    paco2_mm_hg: float | None = None,
    metabolic_acidosis_confirmed: bool = False,
) -> dict:
    """Calculate available metabolic/acid-base indices."""

    if sodium_meq_l <= 0:
        raise ValueError(
            "sodium_meq_l must be greater than zero."
        )

    ag_fields = (
        chloride_meq_l,
        bicarbonate_meq_l,
    )

    ag_field_count = sum(
        value is not None
        for value in ag_fields
    )

    if ag_field_count not in {0, 2}:
        raise ValueError(
            "chloride_meq_l and bicarbonate_meq_l "
            "must be supplied together."
        )

    if (
        chloride_meq_l is not None
        and chloride_meq_l <= 0
    ):
        raise ValueError(
            "chloride_meq_l must be greater than zero."
        )

    if (
        bicarbonate_meq_l is not None
        and bicarbonate_meq_l <= 0
    ):
        raise ValueError(
            "bicarbonate_meq_l must be greater than zero."
        )

    if albumin_g_dl is not None:
        if albumin_g_dl <= 0:
            raise ValueError(
                "albumin_g_dl must be greater than zero."
            )

        if ag_field_count != 2:
            raise ValueError(
                "Albumin correction requires chloride "
                "and bicarbonate values."
            )

    if (
        glucose_mg_dl is not None
        and glucose_mg_dl < 0
    ):
        raise ValueError(
            "glucose_mg_dl cannot be negative."
        )

    if bun_mg_dl is not None:
        if bun_mg_dl < 0:
            raise ValueError(
                "bun_mg_dl cannot be negative."
            )

        if glucose_mg_dl is None:
            raise ValueError(
                "glucose_mg_dl is required when "
                "bun_mg_dl is supplied."
            )

    if (
        paco2_mm_hg is not None
        and paco2_mm_hg <= 0
    ):
        raise ValueError(
            "paco2_mm_hg must be greater than zero."
        )

    has_calculation_path = (
        ag_field_count == 2
        or glucose_mg_dl is not None
    )

    if not has_calculation_path:
        raise ValueError(
            "Supply chloride+bicarbonate and/or glucose "
            "to perform a metabolic calculation."
        )

    anion_gap = None
    corrected_anion_gap = None

    if ag_field_count == 2:
        assert chloride_meq_l is not None
        assert bicarbonate_meq_l is not None

        anion_gap = (
            sodium_meq_l
            - chloride_meq_l
            - bicarbonate_meq_l
        )

        if albumin_g_dl is not None:
            corrected_anion_gap = (
                anion_gap
                + 2.5
                * (
                    4.0
                    - albumin_g_dl
                )
            )

    corrected_sodium = None
    corrected_sodium_delta = None

    if glucose_mg_dl is not None:
        glucose_excess = max(
            glucose_mg_dl - 100.0,
            0.0,
        )

        corrected_sodium_delta = (
            1.6
            * glucose_excess
            / 100.0
        )

        corrected_sodium = (
            sodium_meq_l
            + corrected_sodium_delta
        )

    calculated_osmolality = None

    if (
        glucose_mg_dl is not None
        and bun_mg_dl is not None
    ):
        calculated_osmolality = (
            2.0 * sodium_meq_l
            + glucose_mg_dl / 18.0
            + bun_mg_dl / 2.8
        )

    winter_expected = None
    winter_lower = None
    winter_upper = None
    winter_status = None
    winter_pt = None
    winter_en = None

    metabolic_acidosis_gate = (
        metabolic_acidosis_confirmed
        and bicarbonate_meq_l is not None
        and _strictly_below(
            bicarbonate_meq_l,
            24.0,
        )
    )

    if metabolic_acidosis_gate:
        assert bicarbonate_meq_l is not None

        winter_expected = (
            1.5
            * bicarbonate_meq_l
            + 8.0
        )

        winter_lower = (
            winter_expected - 2.0
        )

        winter_upper = (
            winter_expected + 2.0
        )

        if paco2_mm_hg is not None:
            if _strictly_above(
                paco2_mm_hg,
                winter_upper,
            ):
                winter_status = (
                    "paco2_above_expected"
                )

                winter_pt = (
                    "PaCO2 acima da faixa esperada pela fórmula "
                    "de Winter; isso sugere componente adicional "
                    "de acidose respiratória."
                )

                winter_en = (
                    "PaCO2 is above the Winter expected range; "
                    "this suggests an additional respiratory "
                    "acidosis component."
                )

            elif _strictly_below(
                paco2_mm_hg,
                winter_lower,
            ):
                winter_status = (
                    "paco2_below_expected"
                )

                winter_pt = (
                    "PaCO2 abaixo da faixa esperada pela fórmula "
                    "de Winter; isso sugere componente adicional "
                    "de alcalose respiratória."
                )

                winter_en = (
                    "PaCO2 is below the Winter expected range; "
                    "this suggests an additional respiratory "
                    "alkalosis component."
                )

            else:
                winter_status = (
                    "within_expected"
                )

                winter_pt = (
                    "PaCO2 dentro da faixa esperada pela fórmula "
                    "de Winter para compensação respiratória."
                )

                winter_en = (
                    "PaCO2 is within the Winter expected range "
                    "for respiratory compensation."
                )

    delta_ratio = None
    delta_applied = False
    delta_basis = None
    delta_code = None
    delta_pt = None
    delta_en = None

    ag_for_delta = (
        corrected_anion_gap
        if corrected_anion_gap is not None
        else anion_gap
    )

    delta_gate = (
        metabolic_acidosis_gate
        and ag_for_delta is not None
        and _strictly_above(
            ag_for_delta,
            12.0,
        )
    )

    if delta_gate:
        assert bicarbonate_meq_l is not None
        assert ag_for_delta is not None

        denominator = (
            24.0
            - bicarbonate_meq_l
        )

        if _strictly_above(
            denominator,
            0.0,
        ):
            delta_ratio = (
                (
                    ag_for_delta
                    - 12.0
                )
                / denominator
            )

            delta_applied = True

            delta_basis = (
                "albumin_corrected"
                if corrected_anion_gap
                is not None
                else "uncorrected"
            )

            if _strictly_below(
                delta_ratio,
                1.0,
            ):
                delta_code = (
                    "suggests_additional_nagma"
                )

                delta_pt = (
                    "Delta ratio <1 sugere componente adicional "
                    "de acidose metabólica com ânion gap normal."
                )

                delta_en = (
                    "Delta ratio <1 suggests an additional "
                    "normal-anion-gap metabolic acidosis."
                )

            elif _strictly_above(
                delta_ratio,
                2.0,
            ):
                delta_code = (
                    "suggests_additional_metabolic_alkalosis"
                )

                delta_pt = (
                    "Delta ratio >2 sugere alcalose metabólica "
                    "adicional ou bicarbonato basal previamente "
                    "elevado."
                )

                delta_en = (
                    "Delta ratio >2 suggests additional metabolic "
                    "alkalosis or a previously elevated baseline "
                    "bicarbonate."
                )

            else:
                delta_code = (
                    "compatible_with_predominant_hagma"
                )

                delta_pt = (
                    "Delta ratio entre 1 e 2 é compatível com "
                    "acidose metabólica de ânion gap elevado "
                    "predominante, sem excluir outros processos."
                )

                delta_en = (
                    "A delta ratio between 1 and 2 is compatible "
                    "with predominant high-anion-gap metabolic "
                    "acidosis, without excluding other processes."
                )

    validity_notes_pt: list[str] = []
    validity_notes_en: list[str] = []

    if not metabolic_acidosis_confirmed:
        validity_notes_pt.append(
            "Compensação pela fórmula de Winter e delta ratio "
            "não foram interpretados porque acidose metabólica "
            "não foi confirmada explicitamente."
        )

        validity_notes_en.append(
            "Winter compensation and delta-ratio interpretation "
            "were not applied because metabolic acidosis was not "
            "explicitly confirmed."
        )

    elif not metabolic_acidosis_gate:
        validity_notes_pt.append(
            "A análise de compensação/delta não foi aplicada "
            "porque o bicarbonato informado não estava abaixo "
            "de 24 mEq/L ou estava ausente."
        )

        validity_notes_en.append(
            "Compensation/delta analysis was not applied because "
            "the supplied bicarbonate was not below 24 mEq/L or "
            "was unavailable."
        )

    elif not delta_applied:
        validity_notes_pt.append(
            "O delta ratio não foi aplicado porque o ânion gap "
            "utilizado não excedeu 12 mEq/L."
        )

        validity_notes_en.append(
            "The delta ratio was not applied because the selected "
            "anion gap did not exceed 12 mEq/L."
        )

    if albumin_g_dl is None and anion_gap is not None:
        validity_notes_pt.append(
            "Ânion gap não corrigido por albumina; valores de "
            "referência também dependem do método/laboratório."
        )

        validity_notes_en.append(
            "Anion gap was not albumin-corrected; reference "
            "intervals also depend on laboratory methodology."
        )

    if glucose_mg_dl is not None:
        validity_notes_pt.append(
            "Sódio corrigido usa a convenção de +1,6 mEq/L "
            "por 100 mg/dL de glicose acima de 100 mg/dL."
        )

        validity_notes_en.append(
            "Corrected sodium uses the +1.6 mEq/L per "
            "100 mg/dL glucose above 100 mg/dL convention."
        )

    return {
        "tool":
            "acid_base_metabolic",
        "sodium_meq_l":
            round(sodium_meq_l, 1),
        "chloride_meq_l":
            (
                round(chloride_meq_l, 1)
                if chloride_meq_l is not None
                else None
            ),
        "bicarbonate_meq_l":
            (
                round(bicarbonate_meq_l, 1)
                if bicarbonate_meq_l is not None
                else None
            ),
        "albumin_g_dl":
            (
                round(albumin_g_dl, 2)
                if albumin_g_dl is not None
                else None
            ),
        "glucose_mg_dl":
            (
                round(glucose_mg_dl, 1)
                if glucose_mg_dl is not None
                else None
            ),
        "bun_mg_dl":
            (
                round(bun_mg_dl, 1)
                if bun_mg_dl is not None
                else None
            ),
        "paco2_mm_hg":
            (
                round(paco2_mm_hg, 1)
                if paco2_mm_hg is not None
                else None
            ),
        "anion_gap_meq_l":
            (
                round(anion_gap, 1)
                if anion_gap is not None
                else None
            ),
        "albumin_corrected_anion_gap_meq_l":
            (
                round(
                    corrected_anion_gap,
                    1,
                )
                if corrected_anion_gap
                is not None
                else None
            ),
        "anion_gap_formula":
            "Na - (Cl + HCO3), potassium excluded",
        "albumin_correction_formula":
            "AG + 2.5 * (4 - albumin[g/dL])",
        "albumin_correction_applied":
            corrected_anion_gap is not None,
        "calculated_osmolality_mosm_kg":
            (
                round(
                    calculated_osmolality,
                    1,
                )
                if calculated_osmolality
                is not None
                else None
            ),
        "osmolality_formula":
            "2*Na + glucose/18 + BUN/2.8",
        "corrected_sodium_meq_l":
            (
                round(
                    corrected_sodium,
                    1,
                )
                if corrected_sodium
                is not None
                else None
            ),
        "corrected_sodium_delta_meq_l":
            (
                round(
                    corrected_sodium_delta,
                    1,
                )
                if corrected_sodium_delta
                is not None
                else None
            ),
        "corrected_sodium_method":
            (
                "Na + 1.6*((glucose-100)/100), "
                "for glucose above 100 mg/dL"
                if glucose_mg_dl is not None
                else None
            ),
        "metabolic_acidosis_confirmed":
            metabolic_acidosis_confirmed,
        "winter_analysis_applied":
            metabolic_acidosis_gate,
        "winter_expected_paco2_mm_hg":
            (
                round(
                    winter_expected,
                    1,
                )
                if winter_expected
                is not None
                else None
            ),
        "winter_lower_mm_hg":
            (
                round(winter_lower, 1)
                if winter_lower
                is not None
                else None
            ),
        "winter_upper_mm_hg":
            (
                round(winter_upper, 1)
                if winter_upper
                is not None
                else None
            ),
        "winter_compensation_status":
            winter_status,
        "winter_interpretation_pt":
            winter_pt,
        "winter_interpretation_en":
            winter_en,
        "delta_analysis_applied":
            delta_applied,
        "delta_ag_basis":
            delta_basis,
        "delta_ratio":
            (
                round(delta_ratio, 2)
                if delta_ratio is not None
                else None
            ),
        "delta_interpretation_code":
            delta_code,
        "delta_interpretation_pt":
            delta_pt,
        "delta_interpretation_en":
            delta_en,
        "validity_notes_pt":
            validity_notes_pt,
        "validity_notes_en":
            validity_notes_en,
        "interpretation_pt": (
            "Resultados matemáticos de apoio à avaliação "
            "metabólica/ácido-base. Devem ser integrados ao pH, "
            "gasometria, contexto clínico, método laboratorial "
            "e tendências seriadas."
        ),
        "interpretation_en": (
            "Mathematical results supporting metabolic/acid-base "
            "assessment. They must be integrated with pH, blood "
            "gas data, clinical context, laboratory methodology "
            "and serial trends."
        ),
    }


METABOLIC_METADATA = {
    "id":
        "acid-base-metabolic",
    "name_pt":
        "Ácido-base e metabolismo",
    "name_en":
        "Acid-base and metabolic toolkit",
    "description_pt": (
        "Ânion gap, correção por albumina, osmolalidade "
        "calculada, sódio corrigido por hiperglicemia e, "
        "quando explicitamente válido, Winter e delta ratio."
    ),
    "description_en": (
        "Anion gap, albumin correction, calculated osmolality, "
        "hyperglycaemia-corrected sodium and, when explicitly "
        "valid, Winter compensation and delta ratio."
    ),
    "aliases_pt": [
        "anion gap",
        "ânion gap",
        "AG",
        "osmolalidade",
        "sódio corrigido",
        "Winter",
        "delta ratio",
        "delta-delta",
        "acidose metabólica",
    ],
    "aliases_en": [
        "anion gap",
        "AG",
        "osmolality",
        "corrected sodium",
        "Winter formula",
        "delta ratio",
        "delta-delta",
        "metabolic acidosis",
    ],
    "publisher": (
        "Merck Manual; NCBI; ADA/EASD/JBDS/AACE/DTS "
        "consensus literature"
    ),
    "source_title": (
        "Acid-base disorders and hyperglycaemic-crisis "
        "calculation references"
    ),
    "source_version": (
        "Acid-base references reviewed 2026-09-11; "
        "hyperglycaemic-crises consensus 2024"
    ),
    "source_url": (
        "https://www.merckmanuals.com/professional/"
        "nephrology/acid-base-regulation-and-disorders/"
        "acid-base-disorders"
    ),
    "source_language":
        "en",
    "canonical_language":
        "en",
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
        "as fórmulas matemáticas são mantidas explicitamente."
    ),
    "translation_note_en": (
        "EN-GB explanations are locally authored; "
        "the mathematical formulae are explicitly preserved."
    ),
    "population_pt": (
        "Adultos em avaliação metabólica e ácido-base."
    ),
    "population_en": (
        "Adults undergoing metabolic and acid-base assessment."
    ),
    "limitations_pt": [
        (
            "O módulo não determina automaticamente o distúrbio "
            "ácido-base primário."
        ),
        (
            "Winter e delta ratio somente são interpretados "
            "quando acidose metabólica é confirmada explicitamente."
        ),
        (
            "Intervalos de referência do ânion gap variam conforme "
            "laboratório e metodologia."
        ),
        (
            "Sódio corrigido usa o fator 1,6 mEq/L por "
            "100 mg/dL de glicose acima de 100; outras convenções "
            "existem na literatura."
        ),
        (
            "Osmolalidade calculada não substitui osmolalidade "
            "medida quando houver suspeita de osmóis não medidos."
        ),
    ],
    "limitations_en": [
        (
            "The module does not automatically determine the "
            "primary acid-base disorder."
        ),
        (
            "Winter and delta-ratio interpretation are only "
            "applied when metabolic acidosis is explicitly confirmed."
        ),
        (
            "Anion-gap reference intervals vary with laboratory "
            "methodology."
        ),
        (
            "Corrected sodium uses the 1.6 mEq/L per "
            "100 mg/dL glucose above 100 convention; other "
            "coefficients exist in the literature."
        ),
        (
            "Calculated osmolality does not replace measured "
            "osmolality when unmeasured osmoles are suspected."
        ),
    ],
    "licensing_note_pt": (
        "Fórmulas matemáticas implementadas com explicações "
        "clínicas próprias e referências públicas."
    ),
    "licensing_note_en": (
        "Mathematical formulae implemented with locally authored "
        "clinical explanations and public references."
    ),
    "clinical_review_date":
        date(2026, 9, 11),
    "offline_capable":
        True,
}
