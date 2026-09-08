from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.rebuild_sae_mappings import (
    CSV_PATH,
    NIC,
    NOC,
    NIC_EDITION,
    NOC_EDITION,
    NIC8_LIST_REF,
    NOC7_LIST_REF,
    to_en_gb,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "sae_nnn_links.csv"

F04_REVIEW_PATH = (
    ROOT
    / "data"
    / "f04_review"
    / "f04_applicability_review_20260908.json"
)

F04_REVIEW = json.loads(
    F04_REVIEW_PATH.read_text(encoding="utf-8")
)

F04_PT_BY_EN = {
    item["applicability_en"]: item["applicability_pt"]
    for item in F04_REVIEW["items"]
}

if len(F04_REVIEW["items"]) != 50 or len(F04_PT_BY_EN) != 50:
    raise ValueError(
        "F-04 reviewed applicability corpus must contain "
        "exactly 50 unique EN→PT-BR entries."
    )

PRIMARY_APPLICABILITY_EN = (
    "Compatibility primary selected for the diagnosis; "
    "consider alternative/context-specific links before "
    "finalising a care plan."
)

PRIMARY_APPLICABILITY_PT = (
    "Mapeamento primário de compatibilidade selecionado para "
    "o diagnóstico; considerar vínculos alternativos/específicos "
    "ao contexto antes de finalizar o plano de cuidados."
)


def pt_for_applicability(
    applicability: str,
    role: str,
) -> str:
    if role == "primary":
        if applicability != PRIMARY_APPLICABILITY_EN:
            raise ValueError(
                "Unexpected primary applicability wording: "
                f"{applicability!r}"
            )
        return PRIMARY_APPLICABILITY_PT

    if role != "alternative":
        raise ValueError(
            f"Unexpected classification-link role: {role!r}"
        )

    translated = F04_PT_BY_EN.get(applicability)

    if not translated:
        raise KeyError(
            "Reviewed PT-BR applicability missing for "
            f"{applicability!r}"
        )

    return translated


REVIEW_DATE = "2026-09-07"
NIC_SOURCE = "Institutional Spanish NIC 8th edition source reviewed; current code/label cross-check against NIC 8th current classification listing"
NOC_SOURCE = "Institutional Spanish NOC 7th edition source reviewed; current code/label cross-check against NOC 7th current classification listing"


def spec(classification: str, code: str, role: str, applicability: str, confidence: str = "high", *, status: str = "contextual_current_edition") -> dict[str, str]:
    catalog = NIC if classification == "NIC" else NOC
    edition = NIC_EDITION if classification == "NIC" else NOC_EDITION
    ref = NIC8_LIST_REF if classification == "NIC" else NOC7_LIST_REF
    label_en, label_pt = catalog[code]
    return {
        "classification": classification,
        "code": code,
        "label_en": to_en_gb(label_en),
        "label_pt": label_pt,
        "edition": edition,
        "role": role,
        "applicability": applicability,
        "applicability_en": applicability,
        "applicability_pt": pt_for_applicability(applicability, role),
        "confidence": confidence,
        "verification_status": status,
        "source_language": "es",
        "source_reference": f"{NIC_SOURCE if classification == 'NIC' else NOC_SOURCE}; {ref}",
        "source_page": "",
        "review_date": REVIEW_DATE,
        "notes": "Selection remains patient/context dependent; use the licensed classification definitions, activities/indicators and scales.",
    }


# Alternatives are deliberately contextual rather than pretending that every diagnosis has one
# universally correct intervention/outcome.  The attached NIC source explicitly presents several
# ways to locate interventions and requires clinical selection; the NOC source likewise describes
# outcome selection as dependent on the diagnosis/problem, patient, preferences and care context.
ALTERNATIVES: dict[str, list[dict[str, str]]] = {
    # Childbearing process: phase-specific intervention/outcome choices.
    "00208": [
        spec("NIC", "6760", "alternative", "Use when preparation for labour/childbirth is the dominant need."),
        spec("NIC", "6830", "alternative", "Use during labour/intrapartum care."),
        spec("NIC", "6930", "alternative", "Use in the postpartum phase."),
        spec("NOC", "2510", "alternative", "Use for intrapartum maternal status."),
        spec("NOC", "2511", "alternative", "Use for postpartum/puerperium maternal status."),
    ],
    "00221": [
        spec("NIC", "6760", "alternative", "Use when deficits relate to childbirth preparation."),
        spec("NIC", "6830", "alternative", "Use when the ineffective process is occurring intrapartum."),
        spec("NIC", "6930", "alternative", "Use when the care problem is postpartum."),
        spec("NOC", "2510", "alternative", "Use for intrapartum maternal status."),
        spec("NOC", "2511", "alternative", "Use for postpartum/puerperium maternal status."),
    ],
    "00227": [
        spec("NIC", "6760", "alternative", "Use for antenatal preparation/risk reduction."),
        spec("NIC", "6830", "alternative", "Use if risk is being managed during labour."),
        spec("NIC", "6930", "alternative", "Use for postpartum risk management."),
        spec("NOC", "2510", "alternative", "Use for intrapartum maternal status."),
        spec("NOC", "2511", "alternative", "Use for postpartum/puerperium maternal status."),
    ],
    "00349": [
        spec("NIC", "6771", "alternative", "Antepartum fetal surveillance when clinically indicated."),
        spec("NIC", "6834", "alternative", "High-risk intrapartum care when labour is underway."),
        spec("NOC", "0111", "alternative", "Use when fetal prenatal status is the principal outcome."),
        spec("NOC", "0112", "alternative", "Use when fetal intrapartum status is the principal outcome."),
    ],

    # Development: NIC/NOC selections change with developmental age.
    "00305": [
        spec("NIC", "5680", "alternative", "Age 1-5 years: development teaching for early childhood."),
        spec("NIC", "5650", "alternative", "Age 6-12 years: development teaching for middle childhood."),
        spec("NIC", "5670", "alternative", "Age 12-21 years: adolescent development teaching."),
        spec("NOC", "0127", "alternative", "Age 6-7 years."),
        spec("NOC", "0128", "alternative", "Age 8-10 years."),
        spec("NOC", "0129", "alternative", "Early adolescence."),
        spec("NOC", "0131", "alternative", "Middle adolescence."),
        spec("NOC", "0130", "alternative", "Late adolescence."),
    ],
    "00314": [
        spec("NIC", "5680", "alternative", "Age 1-5 years: development teaching for early childhood."),
        spec("NIC", "5650", "alternative", "Age 6-12 years: development teaching for middle childhood."),
        spec("NIC", "5670", "alternative", "Age 12-21 years: adolescent development teaching."),
        spec("NOC", "0127", "alternative", "Age 6-7 years."),
        spec("NOC", "0128", "alternative", "Age 8-10 years."),
        spec("NOC", "0129", "alternative", "Early adolescence."),
        spec("NOC", "0131", "alternative", "Middle adolescence."),
        spec("NOC", "0130", "alternative", "Late adolescence."),
    ],
    "00315": [
        spec("NOC", "0120", "alternative", "Age 1 month."),
        spec("NOC", "0100", "alternative", "Age 2 months."),
        spec("NOC", "0101", "alternative", "Age 4 months."),
        spec("NOC", "0102", "alternative", "Age 6 months."),
        spec("NOC", "0125", "alternative", "Age 9 months."),
        spec("NOC", "0103", "alternative", "Age 12 months."),
        spec("NOC", "0126", "alternative", "Age 18 months."),
    ],
    "00316": [
        spec("NOC", "0120", "alternative", "Age 1 month."),
        spec("NOC", "0100", "alternative", "Age 2 months."),
        spec("NOC", "0101", "alternative", "Age 4 months."),
        spec("NOC", "0102", "alternative", "Age 6 months."),
        spec("NOC", "0125", "alternative", "Age 9 months."),
        spec("NOC", "0103", "alternative", "Age 12 months."),
        spec("NOC", "0126", "alternative", "Age 18 months."),
    ],

    # Breast/chestfeeding: current NIC 8th removed legacy 1054 from the current list.
    "00461": [
        spec("NIC", "3660", "alternative", "Use when an established nipple-areolar wound/skin lesion requires wound care.", "moderate"),
    ],
    "00462": [
        spec("NIC", "3590", "alternative", "Use for skin surveillance when integrity is threatened but not yet impaired.", "moderate"),
        spec("NOC", "1101", "alternative", "Use to trend tissue integrity when prevention is focused on maintaining intact tissue.", "moderate"),
    ],
    "00333": [spec("NOC", "1002", "alternative", "Use after breastfeeding has been established and maintenance is the target.")],
    "00334": [spec("NOC", "1002", "alternative", "Use when maintenance of breastfeeding is the clinically relevant prevention target.")],
    "00347": [spec("NOC", "1002", "alternative", "Use when maintaining an established breastfeeding pattern is the target.")],
    "00371": [spec("NOC", "1002", "alternative", "Use when maintaining breastfeeding is the target after establishment.")],
    "00382": [spec("NOC", "1002", "alternative", "Use when maintenance is the relevant risk/prevention outcome.")],
    "00406": [spec("NOC", "1002", "alternative", "Use when maintenance is the relevant risk/prevention outcome.")],
    "00479": [spec("NOC", "1002", "alternative", "Use when readiness focuses on sustained breastfeeding." )],

    # Risk/safety outcomes that are more specific than generic risk control in selected contexts.
    "00362": [
        spec("NOC", "1928", "alternative", "Use when hypertension is the identified direction of instability."),
        spec("NOC", "1933", "alternative", "Use when hypotension is the identified direction of instability."),
    ],
    "00311": [spec("NOC", "0414", "alternative", "Use when cardiopulmonary physiologic function is the monitored consequence rather than risk behaviour.")],
    "00087": [spec("NOC", "1902", "alternative", "Use when a generic patient risk-control outcome is required by the local care-plan framework.", "moderate")],
    "00291": [spec("NOC", "1902", "alternative", "Fallback generic risk-control outcome when thrombus-specific indicators are not applicable.", "moderate")],
    "00290": [spec("NOC", "1908", "alternative", "Use when the focus is general risk recognition/detection rather than elopement-specific risk.", "moderate")],

    # Substance withdrawal: substance-specific and longer-term alternatives.
    "00258": [
        spec("NIC", "4512", "alternative", "Use specifically for alcohol withdrawal."),
        spec("NIC", "4510", "alternative", "Use for broader substance-use treatment beyond acute withdrawal."),
        spec("NOC", "1407", "alternative", "Use for longer-term consequences of substance addiction rather than acute withdrawal severity."),
    ],
    "00259": [
        spec("NIC", "4512", "alternative", "Use specifically for alcohol withdrawal risk/management when alcohol is the substance."),
        spec("NIC", "4510", "alternative", "Use for broader substance-use treatment beyond acute withdrawal."),
        spec("NOC", "1407", "alternative", "Use for longer-term consequences of substance addiction rather than acute withdrawal severity."),
    ],

    # Community coping: distinguish resilience from general community health status.
    "00076": [spec("NOC", "2701", "alternative", "Use when the desired outcome is overall community health status rather than resilience/coping capacity.")],
    "00456": [spec("NOC", "2701", "alternative", "Use when the desired outcome is overall community health status rather than resilience/coping capacity.")],
}


CURRENT_EDITION_VERIFIED_PRIMARY_CODES = {
    "5244", "6960", "6800", "8274", "1015", "0414", "1613", "2509", "2704",
    "0910", "1405", "2108", "1932", "1920", "1914", "0204", "1947", "2501",
}


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        diagnoses = list(csv.DictReader(f))

    rows: list[dict[str, str]] = []
    for diag in diagnoses:
        nanda_code = str(diag["code"]).zfill(5)
        for classification in ("NIC", "NOC"):
            prefix = classification.lower()
            code = diag[f"{prefix}_code"]
            status = "current_edition_verified" if code in CURRENT_EDITION_VERIFIED_PRIMARY_CODES else "curated_current_edition"
            rows.append({
                "nanda_code": nanda_code,
                **spec(
                    classification,
                    code,
                    "primary",
                    "Compatibility primary selected for the diagnosis; consider alternative/context-specific links before finalising a care plan.",
                    diag.get("mapping_confidence") or "moderate",
                    status=status,
                ),
            })
        for item in ALTERNATIVES.get(nanda_code, []):
            rows.append({"nanda_code": nanda_code, **item})

    # Stable deterministic ordering: diagnosis, classification, primary first, then code.
    rows.sort(key=lambda r: (r["nanda_code"], r["classification"], 0 if r["role"] == "primary" else 1, r["code"]))
    fields = [
        "nanda_code", "classification", "code", "label_en", "label_pt", "edition", "role",
        "applicability", "applicability_en", "applicability_pt", "confidence", "verification_status", "source_language", "source_reference",
        "source_page", "review_date", "notes",
    ]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    primary = sum(1 for r in rows if r["role"] == "primary")
    alternatives = len(rows) - primary
    print(f"Wrote {len(rows)} NNN links: primary={primary}, alternatives={alternatives}, diagnoses={len(diagnoses)}")


if __name__ == "__main__":
    main()
