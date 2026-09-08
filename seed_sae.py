import csv
from pathlib import Path

import database
from sqlalchemy import inspect

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "sae_bilingual_final.csv"
LINKS_FILE = BASE_DIR / "data" / "sae_nnn_links.csv"
REQUIRED_COLUMNS = {
    "code", "description_en", "description_pt",
    "intervention_en", "intervention_pt", "outcome_en", "outcome_pt",
    "nanda_edition", "nanda_domain", "nanda_class", "nanda_source_page", "nanda_pdf_page",
    "nic_edition", "nic_code", "nic_label_en", "nic_label_pt",
    "noc_edition", "noc_code", "noc_label_en", "noc_label_pt",
    "mapping_status", "mapping_confidence", "mapping_methodology",
    "mapping_review_date", "mapping_reference", "mapping_rationale", "mapping_notes",
}


def _load_rows():
    if not CSV_FILE.is_file():
        raise FileNotFoundError(f"CSV not found: {CSV_FILE}")

    with CSV_FILE.open(mode="r", encoding="utf-8-sig", newline="") as file:
        first_line = file.readline()
        file.seek(0)
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(file, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")

        reader.fieldnames = [str(field).strip() for field in reader.fieldnames]
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        entries = []
        seen_codes = set()
        for line_number, row in enumerate(reader, start=2):
            normalized = {key: (row.get(key) or "").strip() for key in REQUIRED_COLUMNS}
            if any(not normalized[key] for key in REQUIRED_COLUMNS):
                raise ValueError(f"Blank required value on CSV line {line_number}.")

            raw_code = normalized["code"]
            if not raw_code.isdigit() or len(raw_code) > 5:
                raise ValueError(f"Invalid NANDA code on CSV line {line_number}: {raw_code!r}")
            code = raw_code.zfill(5)
            if code in seen_codes:
                continue
            seen_codes.add(code)

            if not (normalized["nic_code"].isdigit() and len(normalized["nic_code"]) == 4):
                raise ValueError(f"Invalid NIC code on CSV line {line_number}: {normalized['nic_code']!r}")
            if not (normalized["noc_code"].isdigit() and len(normalized["noc_code"]) == 4):
                raise ValueError(f"Invalid NOC code on CSV line {line_number}: {normalized['noc_code']!r}")
            if not normalized["nanda_source_page"].isdigit():
                raise ValueError(f"Invalid NANDA source page on CSV line {line_number}: {normalized['nanda_source_page']!r}")
            if not normalized["nanda_pdf_page"].isdigit():
                raise ValueError(f"Invalid NANDA PDF page on CSV line {line_number}: {normalized['nanda_pdf_page']!r}")
            if normalized["mapping_confidence"] not in {"high", "moderate", "review_required"}:
                raise ValueError(f"Invalid mapping confidence on CSV line {line_number}: {normalized['mapping_confidence']!r}")
            if normalized["mapping_status"] != "curated_current_editions_contextual":
                raise ValueError(f"Unexpected mapping status on CSV line {line_number}: {normalized['mapping_status']!r}")
            if not normalized["mapping_reference"].startswith(("https://", "http://")):
                raise ValueError(f"Invalid mapping reference URL on CSV line {line_number}.")

            entries.append(
                database.SAEDiagnostic(
                    code=code,
                    description_en=normalized["description_en"],
                    description_pt=normalized["description_pt"],
                    intervention_en=normalized["intervention_en"],
                    intervention_pt=normalized["intervention_pt"],
                    outcome_en=normalized["outcome_en"],
                    outcome_pt=normalized["outcome_pt"],
                    nanda_edition=normalized["nanda_edition"],
                    nanda_domain=normalized["nanda_domain"],
                    nanda_class=normalized["nanda_class"],
                    nanda_source_page=normalized["nanda_source_page"],
                    nanda_pdf_page=normalized["nanda_pdf_page"],
                    nic_edition=normalized["nic_edition"],
                    nic_code=normalized["nic_code"],
                    nic_label_en=normalized["nic_label_en"],
                    nic_label_pt=normalized["nic_label_pt"],
                    noc_edition=normalized["noc_edition"],
                    noc_code=normalized["noc_code"],
                    noc_label_en=normalized["noc_label_en"],
                    noc_label_pt=normalized["noc_label_pt"],
                    mapping_status=normalized["mapping_status"],
                    mapping_confidence=normalized["mapping_confidence"],
                    mapping_methodology=normalized["mapping_methodology"],
                    mapping_review_date=normalized["mapping_review_date"],
                    mapping_reference=normalized["mapping_reference"],
                    mapping_rationale=normalized["mapping_rationale"],
                    mapping_notes=normalized["mapping_notes"],
                )
            )

    if not entries:
        raise ValueError("CSV contains no valid SAE records.")
    return entries


LINK_REQUIRED_COLUMNS = {
    "nanda_code", "classification", "code", "label_en", "label_pt", "edition", "role",
    "applicability", "applicability_en", "applicability_pt", "confidence", "verification_status", "source_language", "source_reference",
    "source_page", "review_date", "notes",
}


def _load_links():
    if not LINKS_FILE.is_file():
        raise FileNotFoundError(f"NNN link CSV not found: {LINKS_FILE}")
    with LINKS_FILE.open(mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("NNN link CSV has no header row.")
        reader.fieldnames = [str(field).strip() for field in reader.fieldnames]
        missing = LINK_REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"NNN link CSV is missing required columns: {', '.join(sorted(missing))}")

        rows = []
        seen = set()
        primary_counts = {}
        for line_number, row in enumerate(reader, start=2):
            normalized = {key: (row.get(key) or "").strip() for key in LINK_REQUIRED_COLUMNS}
            for key in LINK_REQUIRED_COLUMNS - {"source_page", "notes"}:
                if not normalized[key]:
                    raise ValueError(f"Blank {key} on NNN link CSV line {line_number}.")
            nanda_code = normalized["nanda_code"]
            if not (nanda_code.isdigit() and len(nanda_code) == 5):
                raise ValueError(f"Invalid NANDA code on NNN link CSV line {line_number}: {nanda_code!r}")
            if normalized["classification"] not in {"NIC", "NOC"}:
                raise ValueError(f"Invalid classification on NNN link CSV line {line_number}.")
            if not (normalized["code"].isdigit() and len(normalized["code"]) == 4):
                raise ValueError(f"Invalid classification code on NNN link CSV line {line_number}: {normalized['code']!r}")
            if normalized["role"] not in {"primary", "alternative"}:
                raise ValueError(f"Invalid role on NNN link CSV line {line_number}.")
            if normalized["confidence"] not in {"high", "moderate", "review_required"}:
                raise ValueError(f"Invalid confidence on NNN link CSV line {line_number}.")
            key = (nanda_code, normalized["classification"], normalized["code"], normalized["role"])
            if key in seen:
                raise ValueError(f"Duplicate NNN link on line {line_number}: {key}")
            seen.add(key)
            if normalized["role"] == "primary":
                pkey = (nanda_code, normalized["classification"])
                primary_counts[pkey] = primary_counts.get(pkey, 0) + 1
            rows.append(normalized)

    diagnoses = {row["nanda_code"] for row in rows}
    for nanda_code in diagnoses:
        for classification in ("NIC", "NOC"):
            if primary_counts.get((nanda_code, classification)) != 1:
                raise ValueError(f"Expected exactly one primary {classification} link for {nanda_code}.")
    return rows


def _assert_migrated_schema() -> None:
    inspector = inspect(database.engine)
    tables = set(inspector.get_table_names())
    if "sae_diagnostics" not in tables or "sae_classification_links" not in tables:
        raise RuntimeError("SAE/link tables are missing. Run `alembic upgrade head` first.")
    required = {
        "code", "description_en", "description_pt", "intervention_en",
        "intervention_pt", "outcome_en", "outcome_pt", "mapping_status",
        "mapping_methodology", "mapping_review_date", "mapping_notes",
        "nanda_edition", "nanda_domain", "nanda_class", "nanda_source_page", "nanda_pdf_page",
        "nic_edition", "nic_code", "nic_label_en", "nic_label_pt",
        "noc_edition", "noc_code", "noc_label_en", "noc_label_pt",
        "mapping_confidence", "mapping_reference", "mapping_rationale",
    }
    columns = {column["name"] for column in inspector.get_columns("sae_diagnostics")}
    missing = required - columns
    if missing:
        raise RuntimeError(
            "Database schema is older than the application. Run `alembic upgrade head`. "
            f"Missing SAE columns: {', '.join(sorted(missing))}"
        )


def seed_database():
    _assert_migrated_schema()
    entries = _load_rows()  # Validate the replacement dataset before touching existing data.
    link_rows = _load_links()
    entry_codes = {entry.code for entry in entries}
    unknown_links = sorted({row["nanda_code"] for row in link_rows} - entry_codes)
    if unknown_links:
        raise ValueError(f"NNN links reference unknown NANDA codes: {', '.join(unknown_links[:10])}")

    db = database.SessionLocal()
    try:
        with db.begin():
            db.query(database.SAEClassificationLink).delete(synchronize_session=False)
            db.query(database.SAEDiagnostic).delete(synchronize_session=False)
            db.add_all(entries)
            db.flush()
            by_code = {entry.code: entry for entry in entries}
            links = []
            for index, row in enumerate(link_rows):
                links.append(database.SAEClassificationLink(
                    sae_diagnostic_id=by_code[row["nanda_code"]].id,
                    classification=row["classification"],
                    code=row["code"],
                    label_en=row["label_en"],
                    label_pt=row["label_pt"],
                    edition=row["edition"],
                    role=row["role"],
                    applicability=row["applicability"],
                    applicability_en=row["applicability_en"],
                    applicability_pt=row["applicability_pt"],
                    confidence=row["confidence"],
                    verification_status=row["verification_status"],
                    source_language=row["source_language"],
                    source_reference=row["source_reference"],
                    source_page=row["source_page"] or None,
                    review_date=row["review_date"],
                    notes=row["notes"] or None,
                    sort_order=0 if row["role"] == "primary" else 100 + index,
                ))
            db.add_all(links)
        print(f"Successfully seeded {len(entries)} bilingual diagnoses and {len(link_rows)} contextual NIC/NOC links into SQLite.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
