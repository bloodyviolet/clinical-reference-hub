"""Bedside oxygenation ratio calculations.

Calculations:

- P/F ratio = PaO2 / FiO2 fraction
- S/F ratio = SpO2 / FiO2 fraction

FiO2 must be supplied explicitly. This module does not infer FiO2 from
oxygen flow rate or delivery-device labels.

The ratios are not used here to independently diagnose or severity-stage
ARDS. S/F interpretation carries an explicit caution when SpO2 is >97%.
"""

from __future__ import annotations

from datetime import date


GLOBAL_ARDS_SOURCE_URL = (
    "https://pubmed.ncbi.nlm.nih.gov/37487152/"
)

PULSE_OX_SOURCE_URL = (
    "https://pubmed.ncbi.nlm.nih.gov/36049490/"
)


BRAZIL_RESPIRATORY_SURVEILLANCE_URL = (
    "https://www.gov.br/saude/pt-br/"
    "centrais-de-conteudo/publicacoes/notas-tecnicas/"
    "2026/nota-tecnica-no-11-2026-cgcovid.pdf/view"
)

BRAZIL_CONITEC_PCDT_CATALOG_URL = (
    "https://www.gov.br/conitec/pt-br/assuntos/"
    "avaliacao-de-tecnologias-em-saude/"
    "protocolos-clinicos-e-diretrizes-terapeuticas/pcdt"
)


def calculate_oxygenation(
    *,
    fio2_percent: float,
    pao2_mm_hg: float | None = None,
    spo2_percent: float | None = None,
) -> dict:
    """Calculate P/F and/or S/F from explicit FiO2."""

    if not 21 <= fio2_percent <= 100:
        raise ValueError(
            "fio2_percent must be between 21 and 100."
        )

    if (
        pao2_mm_hg is None
        and spo2_percent is None
    ):
        raise ValueError(
            "At least one of pao2_mm_hg or "
            "spo2_percent must be supplied."
        )

    if (
        pao2_mm_hg is not None
        and pao2_mm_hg <= 0
    ):
        raise ValueError(
            "pao2_mm_hg must be greater than zero."
        )

    if (
        spo2_percent is not None
        and not 1 <= spo2_percent <= 100
    ):
        raise ValueError(
            "spo2_percent must be between 1 and 100."
        )

    fio2_fraction = (
        fio2_percent
        / 100.0
    )

    pf_ratio = (
        pao2_mm_hg / fio2_fraction
        if pao2_mm_hg is not None
        else None
    )

    sf_ratio = (
        spo2_percent / fio2_fraction
        if spo2_percent is not None
        else None
    )

    sf_above_97_caution = (
        spo2_percent > 97
        if spo2_percent is not None
        else None
    )

    global_ards_sf_threshold_applicable = (
        spo2_percent <= 97
        if spo2_percent is not None
        else None
    )

    return {
        "tool": "oxygenation_ratios",
        "fio2_percent":
            round(fio2_percent, 1),
        "fio2_fraction":
            round(fio2_fraction, 4),
        "pao2_mm_hg":
            (
                round(pao2_mm_hg, 1)
                if pao2_mm_hg is not None
                else None
            ),
        "spo2_percent":
            (
                round(spo2_percent, 1)
                if spo2_percent is not None
                else None
            ),
        "pf_ratio_mm_hg":
            (
                round(pf_ratio, 1)
                if pf_ratio is not None
                else None
            ),
        "sf_ratio":
            (
                round(sf_ratio, 1)
                if sf_ratio is not None
                else None
            ),
        "pf_method":
            "PaO2 / FiO2 fraction",
        "sf_method":
            "SpO2 / FiO2 fraction",
        "ards_classification_applied":
            False,
        "sf_spo2_above_97_caution":
            sf_above_97_caution,
        "global_ards_sf_threshold_applicable":
            global_ards_sf_threshold_applicable,
        "interpretation_pt": (
            "As relações P/F e S/F quantificam oxigenação, "
            "mas não estabelecem diagnóstico nem gravidade de "
            "SDRA isoladamente. A interpretação exige contexto "
            "clínico, suporte respiratório e os demais critérios "
            "da definição aplicável."
        ),
        "interpretation_en": (
            "P/F and S/F ratios quantify oxygenation but do not "
            "independently establish an ARDS diagnosis or severity. "
            "Interpretation requires clinical context, respiratory "
            "support and the other criteria of the applicable "
            "definition."
        ),
        "sf_note_pt": (
            (
                "SpO2 acima de 97% reduz a utilidade discriminativa "
                "da relação S/F; o limiar S/F da definição global "
                "de SDRA não deve ser aplicado neste valor."
            )
            if sf_above_97_caution
            else (
                "Quando usada na definição global de SDRA, a relação "
                "S/F é considerada com SpO2 ≤97%; a relação isolada "
                "não confirma SDRA."
            )
            if spo2_percent is not None
            else None
        ),
        "sf_note_en": (
            (
                "SpO2 above 97% reduces the discriminatory utility "
                "of the S/F ratio; the Global ARDS S/F threshold "
                "should not be applied to this value."
            )
            if sf_above_97_caution
            else (
                "When used in the Global ARDS definition, the S/F "
                "ratio is considered with SpO2 ≤97%; the ratio alone "
                "does not confirm ARDS."
            )
            if spo2_percent is not None
            else None
        ),
        "fio2_note_pt": (
            "A FiO2 foi informada explicitamente. Este módulo não "
            "estima FiO2 a partir de fluxo de oxigênio ou do tipo "
            "de dispositivo."
        ),
        "fio2_note_en": (
            "FiO2 was supplied explicitly. This module does not "
            "estimate FiO2 from oxygen flow rate or delivery-device "
            "type."
        ),
    }


OXYGENATION_METADATA = {
    "id": "oxygenation-ratios",
    "name_pt": (
        "Oxigenação — relações P/F e S/F"
    ),
    "name_en": (
        "Oxygenation — P/F and S/F ratios"
    ),
    "description_pt": (
        "Cálculo das relações PaO2/FiO2 e SpO2/FiO2 "
        "a partir de FiO2 explicitamente informada."
    ),
    "description_en": (
        "Calculation of PaO2/FiO2 and SpO2/FiO2 ratios "
        "from explicitly supplied FiO2."
    ),
    "aliases_pt": [
        "P/F",
        "PaO2 FiO2",
        "PaO2/FiO2",
        "S/F",
        "SpO2 FiO2",
        "SpO2/FiO2",
        "oxigenação",
        "SDRA",
    ],
    "aliases_en": [
        "P/F ratio",
        "PaO2 FiO2",
        "PaO2/FiO2",
        "S/F ratio",
        "SpO2 FiO2",
        "SpO2/FiO2",
        "oxygenation",
        "ARDS",
    ],
    "publisher": (
        "Global ARDS Definition consensus group"
    ),
    "source_title": (
        "A New Global Definition of Acute "
        "Respiratory Distress Syndrome"
    ),
    "source_version": (
        "Global ARDS Definition 2023; "
        "oxygenation criteria reviewed 2026-09-11"
    ),
    "source_url":
        GLOBAL_ARDS_SOURCE_URL,
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
        "as relações matemáticas permanecem inalteradas."
    ),
    "translation_note_en": (
        "EN-GB explanations are locally authored; "
        "the mathematical ratios are unchanged."
    ),
    "population_pt": (
        "Pacientes em avaliação de oxigenação quando "
        "PaO2 e/ou SpO2 e FiO2 são conhecidos."
    ),
    "population_en": (
        "Patients undergoing oxygenation assessment when "
        "PaO2 and/or SpO2 and FiO2 are known."
    ),
    "limitations_pt": [
        (
            "A relação isolada não estabelece diagnóstico "
            "nem gravidade de SDRA."
        ),
        (
            "A FiO2 deve ser conhecida; este módulo não a "
            "estima a partir do fluxo ou do dispositivo."
        ),
        (
            "A relação S/F perde precisão/utilidade em "
            "saturações elevadas; a definição global de SDRA "
            "restringe seu critério a SpO2 ≤97%."
        ),
        (
            "A oximetria de pulso pode ser afetada por "
            "perfusão inadequada, artefato e limitações "
            "relacionadas à medição."
        ),
    ],
    "limitations_en": [
        (
            "The ratio alone does not establish an ARDS "
            "diagnosis or severity."
        ),
        (
            "FiO2 must be known; this module does not estimate "
            "it from flow rate or delivery-device type."
        ),
        (
            "S/F becomes less accurate/useful at high oxygen "
            "saturations; the Global ARDS definition restricts "
            "its criterion to SpO2 ≤97%."
        ),
        (
            "Pulse oximetry may be affected by poor perfusion, "
            "artefact and measurement-related limitations."
        ),
    ],
    "licensing_note_pt": (
        "Relações matemáticas implementadas com explicações "
        "clínicas próprias e referências públicas."
    ),
    "licensing_note_en": (
        "Mathematical ratios implemented with locally authored "
        "clinical explanations and public references."
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
        "Ministério da Saúde / SVSA; CONITEC",

    "brazil_source_title": (
        "Nota Técnica nº 11/2026-CGCOVID/DEDT/SVSA/MS "
        "e revisão do catálogo oficial de PCDT da CONITEC"
    ),

    "brazil_source_url":
        BRAZIL_RESPIRATORY_SURVEILLANCE_URL,

    "brazil_document_or_portaria":
        "Nota Técnica nº 11/2026-CGCOVID/DEDT/SVSA/MS",

    "brazil_scope_pt": (
        "A fonte nacional vigente trata de vigilância de vírus "
        "respiratórios e definição de caso de SRAG. Nenhuma "
        "variante nacional geral de cálculo P/F ou S/F foi "
        "identificada no corpus oficial auditado."
    ),

    "brazil_scope_en": (
        "The current national source addresses respiratory-virus "
        "surveillance and the SRAG case definition. No general "
        "Brazilian national P/F or S/F calculation variant was "
        "identified in the audited official corpus."
    ),

    "brazil_differs_from_international":
        False,

    "brazil_difference_notes_pt": (
        "A definição nacional de vigilância de SRAG inclui "
        "SpO2 <=94% em ar ambiente entre critérios de piora, "
        "mas esse limiar epidemiológico não substitui P/F ou "
        "S/F e não é aplicado como diagnóstico/classificação "
        "de SDRA. Não foi identificada adoção formal pelo SUS "
        "da definição Global ARDS 2023 como definição nacional "
        "genérica."
    ),

    "brazil_difference_notes_en": (
        "The national SRAG surveillance definition includes "
        "room-air SpO2 <=94% among deterioration criteria, but "
        "this epidemiological threshold does not replace P/F or "
        "S/F and is not applied as ARDS diagnosis/classification. "
        "Formal SUS adoption of the 2023 Global ARDS definition "
        "as a generic national definition was not identified."
    ),

    "final_brazil_review_status":
        "pass",
}
