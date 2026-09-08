import os
from pathlib import Path

from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "medical.db"
DATABASE_URL = os.getenv("MEDICAL_API_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
SQLITE_BUSY_TIMEOUT_MS = int(os.getenv("MEDICAL_API_SQLITE_BUSY_TIMEOUT_MS", "5000"))

connect_args = {"check_same_thread": False, "timeout": max(0.1, SQLITE_BUSY_TIMEOUT_MS / 1000)} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        finally:
            cursor.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SAEDiagnostic(Base):
    __tablename__ = "sae_diagnostics"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True, nullable=False)
    description_en = Column(Text, nullable=False)
    description_pt = Column(Text, nullable=False)
    intervention_en = Column(Text, nullable=False)
    intervention_pt = Column(Text, nullable=False)
    outcome_en = Column(Text, nullable=False)
    outcome_pt = Column(Text, nullable=False)
    mapping_status = Column(String(30), nullable=False, default="suggested_unverified")
    mapping_methodology = Column(Text, nullable=False, default="Local curated/suggested NANDA-to-NIC/NOC linkage; not an official crosswalk.")
    mapping_review_date = Column(String(10), nullable=True)
    mapping_notes = Column(Text, nullable=True)

    # Structured classification provenance. Nullable at the schema layer so a legacy
    # database can be migrated without fabricating classification metadata; the
    # curated Pass 4 seed requires and populates every field.
    nanda_edition = Column(Text, nullable=True)
    nanda_domain = Column(String(4), nullable=True)
    nanda_class = Column(String(4), nullable=True)
    nanda_source_page = Column(String(12), nullable=True)
    nanda_pdf_page = Column(String(12), nullable=True)
    nic_edition = Column(Text, nullable=True)
    nic_code = Column(String(8), index=True, nullable=True)
    nic_label_en = Column(Text, nullable=True)
    nic_label_pt = Column(Text, nullable=True)
    noc_edition = Column(Text, nullable=True)
    noc_code = Column(String(8), index=True, nullable=True)
    noc_label_en = Column(Text, nullable=True)
    noc_label_pt = Column(Text, nullable=True)
    mapping_confidence = Column(String(20), nullable=True)
    mapping_reference = Column(Text, nullable=True)
    mapping_rationale = Column(Text, nullable=True)

    classification_links = relationship(
        "SAEClassificationLink",
        back_populates="diagnostic",
        cascade="all, delete-orphan",
        order_by="SAEClassificationLink.sort_order, SAEClassificationLink.classification, SAEClassificationLink.code",
    )


class SAEClassificationLink(Base):
    __tablename__ = "sae_classification_links"
    __table_args__ = (
        UniqueConstraint(
            "sae_diagnostic_id", "classification", "code", "role",
            name="uq_sae_classification_link",
        ),
    )

    id = Column(Integer, primary_key=True)
    sae_diagnostic_id = Column(Integer, ForeignKey("sae_diagnostics.id", ondelete="CASCADE"), index=True, nullable=False)
    classification = Column(String(3), index=True, nullable=False)
    code = Column(String(8), index=True, nullable=False)
    label_en = Column(Text, nullable=False)
    label_pt = Column(Text, nullable=False)
    edition = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)
    applicability = Column(Text, nullable=False)
    applicability_en = Column(Text, nullable=False)
    applicability_pt = Column(Text, nullable=False)
    confidence = Column(String(20), nullable=False)
    verification_status = Column(String(40), nullable=False)
    source_language = Column(String(10), nullable=False, default="es")
    source_reference = Column(Text, nullable=False)
    source_page = Column(String(40), nullable=True)
    review_date = Column(String(10), nullable=False)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)

    diagnostic = relationship("SAEDiagnostic", back_populates="classification_links")


class PublicHealthPolicy(Base):
    __tablename__ = "public_health_policies"
    __table_args__ = (
        UniqueConstraint("policy_name", "directive", name="uq_policy_directive"),
    )

    id = Column(Integer, primary_key=True)
    policy_name = Column(String(20), index=True, nullable=False)
    directive = Column(String, nullable=False)
    target_demographic = Column(String, nullable=False)
    clinical_guideline = Column(Text, nullable=False)

    # Provenance/version metadata. ISO dates are stored as YYYY-MM-DD strings to keep
    # the SQLite file portable and human-inspectable without dialect-specific types.
    source_title = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_page = Column(String(40), nullable=True)
    source_publication_date = Column(String(10), nullable=True)
    effective_from = Column(String(10), nullable=True)
    effective_until = Column(String(10), nullable=True)
    last_clinical_review = Column(String(10), nullable=False)
    source_version = Column(String(80), nullable=True)
    status = Column(String(20), nullable=False, default="current")
    review_notes = Column(Text, nullable=True)
    evidence_level = Column(String(30), nullable=False, default="policy_level")



def sqlite_database_path() -> Path:
    """Return the configured SQLite file path or raise for non-SQLite deployments."""
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != "sqlite":
        raise RuntimeError("This operation is only supported for SQLite database URLs.")
    database = url.database
    if not database or database == ":memory:":
        raise RuntimeError("A file-backed SQLite database is required for this operation.")
    path = Path(database)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    return path


def assert_database_health(*, quick_check: bool = True) -> str:
    """Verify connectivity and, for SQLite, perform a lightweight integrity check."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        if quick_check and DATABASE_URL.startswith("sqlite"):
            result = connection.execute(text("PRAGMA quick_check")).scalar()
            if result != "ok":
                raise RuntimeError(f"SQLite quick_check failed: {result}")
    return "ok"


def current_migration_head() -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    return ScriptDirectory.from_config(config).get_current_head() or ""


def assert_schema_current() -> str:
    """Fail fast when the persisted DB has not been migrated to this build."""
    from sqlalchemy import inspect, text

    expected = current_migration_head()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "alembic_version" not in tables:
        raise RuntimeError("Database is not Alembic-managed. Run `python migrate.py` before starting the API.")
    with engine.connect() as connection:
        row = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
    actual = row[0] if row else ""
    if actual != expected:
        raise RuntimeError(
            f"Database schema revision {actual or '<none>'} does not match application head {expected}. "
            "Run `python migrate.py`."
        )
    if "pnaism_policies" in tables:
        raise RuntimeError("Legacy pnaism_policies table still exists; run `python migrate.py`.")
    return actual

def init_db() -> None:
    """Upgrade the configured database to the current Alembic revision."""
    from alembic import command
    from alembic.config import Config

    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    command.upgrade(config, "head")


if __name__ == "__main__":
    init_db()
    print(f"Database schema upgraded successfully using {DATABASE_URL}.")
