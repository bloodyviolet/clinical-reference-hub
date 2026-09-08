from datetime import date
from urllib.parse import urlparse

from sqlalchemy import inspect

import database
from policy_data import POLICY_DATA, iter_policy_records

REQUIRED_COLUMNS = {
    "policy_name", "directive", "target_demographic", "clinical_guideline",
    "source_title", "source_url", "last_clinical_review", "status", "evidence_level",
}


def _assert_migrated_schema() -> None:
    inspector = inspect(database.engine)
    if "public_health_policies" not in inspector.get_table_names():
        raise RuntimeError("Policy table is missing. Run `alembic upgrade head` first.")
    columns = {column["name"] for column in inspector.get_columns("public_health_policies")}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise RuntimeError(
            "Database schema is older than the application. Run `alembic upgrade head`. "
            f"Missing columns: {', '.join(sorted(missing))}"
        )



def _validate_record(record: dict) -> None:
    for key in REQUIRED_COLUMNS:
        if not str(record.get(key) or "").strip():
            raise ValueError(f"Blank required policy field {key!r} for {record.get('policy_name')} / {record.get('directive')}")
    parsed = urlparse(record["source_url"])
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Policy source_url must be an absolute HTTPS URL: {record['source_url']!r}")
    if record["status"] not in {"current", "superseded", "historical", "needs_review"}:
        raise ValueError(f"Invalid policy status: {record['status']!r}")
    if record["evidence_level"] not in {"current_override", "pinpoint_policy", "policy_context", "policy_level"}:
        raise ValueError(f"Invalid policy evidence_level: {record['evidence_level']!r}")
    for field in ("source_publication_date", "effective_from", "effective_until", "last_clinical_review"):
        value = record.get(field)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{field} must be YYYY-MM-DD: {value!r}") from exc
    text = " ".join(str(record.get(key) or "") for key in ("directive", "target_demographic", "clinical_guideline"))
    if "[cite:" in text.lower():
        raise ValueError(f"Raw citation placeholder detected in {record['policy_name']} / {record['directive']}")

def seed_policies(policy_names=None) -> int:
    _assert_migrated_schema()
    selected = {name.upper() for name in policy_names} if policy_names else set(POLICY_DATA)
    unknown = selected - set(POLICY_DATA)
    if unknown:
        raise ValueError(f"Unknown policies: {', '.join(sorted(unknown))}")

    records = list(iter_policy_records(selected))
    if not records:
        raise ValueError("Policy seed dataset is empty; refusing to delete existing data.")

    for record in records:
        _validate_record(record)
    entries = [database.PublicHealthPolicy(**record) for record in records]
    db = database.SessionLocal()
    try:
        with db.begin():
            db.query(database.PublicHealthPolicy).filter(
                database.PublicHealthPolicy.policy_name.in_(selected)
            ).delete(synchronize_session=False)
            db.add_all(entries)
        print(
            f"Successfully seeded {len(entries)} directives across "
            f"{len(selected)} policy/policies: {', '.join(sorted(selected))}."
        )
        return len(entries)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_policies()
