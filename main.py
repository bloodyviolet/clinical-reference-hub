from contextlib import asynccontextmanager
import logging
import unicodedata
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

import database
import schemas
from clinical_tools.news2 import NEWS2_METADATA, calculate_news2
from clinical_tools.renal import (
    AKI_METADATA,
    CKD_METADATA,
    EGFR_METADATA,
    calculate_egfr_ckd_epi_2021,
    calculate_kdigo_aki,
    classify_ckd,
)
from clinical_tools.hemodynamics import (
    HEMODYNAMICS_METADATA,
    calculate_hemodynamics,
)
from clinical_tools.oxygenation import (
    OXYGENATION_METADATA,
    calculate_oxygenation,
)
from clinical_tools.metabolic import (
    METABOLIC_METADATA,
    calculate_metabolic_toolkit,
)
from clinical_tools.growth import (
    GROWTH_METADATA,
    calculate_who_growth,
)
from config import load_settings
from observability import RateLimitMiddleware, RequestContextMiddleware, configure_logging
from scripts.clinical_content import file_hash, validate_release_content

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdfs"
ASSET_DIR = BASE_DIR / "assets"
INDEX_FILE = BASE_DIR / "index.html"
MANIFEST_FILE = BASE_DIR / "manifest.json"
SERVICE_WORKER_FILE = BASE_DIR / "sw.js"
FAVICON_FILE = ASSET_DIR / "icons" / "favicon.ico"
CLINICAL_CONTENT_MANIFEST_FILE = (
    BASE_DIR / "data" / "clinical_content_manifest.json"
)
API_VERSION = "1.4.5"

_CLINICAL_CONTENT_CERTIFICATION: dict | None = None
settings = load_settings()
configure_logging(level=settings.log_level, json_logs=settings.json_logs)
logger = logging.getLogger("medical_api")

# Compatibility aliases retained for existing tests/deployments that introspect these flags.
ENABLE_API_DOCS = settings.enable_api_docs
ENABLE_HSTS = settings.enable_hsts
ENABLE_SAE = settings.enable_sae


def _assert_runtime_files() -> None:
    required = (
        INDEX_FILE, MANIFEST_FILE, SERVICE_WORKER_FILE,
        ASSET_DIR / "app.css", ASSET_DIR / "app.js",
        ASSET_DIR / "growth-tools.js",
        ASSET_DIR / "offline" / "sae.json", ASSET_DIR / "offline" / "policies.json",
        ASSET_DIR / "reference" / "who-growth" / "who2006_weight_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "who2006_length_height_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "who2006_bmi_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "who2006_head_circumference_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "who2006_weight_for_length.json",
        ASSET_DIR / "reference" / "who-growth" / "who2006_weight_for_height.json",
        ASSET_DIR / "reference" / "who-growth" / "who2007_weight_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "who2007_height_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "who2007_bmi_for_age.json",
        ASSET_DIR / "reference" / "who-growth" / "BRAZIL_SISVAN.json",
        ASSET_DIR / "reference" / "who-growth" / "SOURCES.json",
        ASSET_DIR / "reference" / "who-growth" / "NOTICE.txt",
        ASSET_DIR / "reference" / "who-growth" / "GPL-3.0.txt",
        CLINICAL_CONTENT_MANIFEST_FILE,
        ASSET_DIR / "icons" / "icon-192.png", ASSET_DIR / "icons" / "icon-512.png",
        ASSET_DIR / "icons" / "apple-touch-icon.png", ASSET_DIR / "icons" / "favicon.ico",
        ASSET_DIR / "icons" / "favicon-32.png", ASSET_DIR / "icons" / "favicon-16.png",
        PDF_DIR / "Nanda-I 2024-2026.pdf",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required runtime files are missing: " + ", ".join(missing))


def _certify_clinical_content() -> dict:
    global _CLINICAL_CONTENT_CERTIFICATION

    content = validate_release_content(
        BASE_DIR,
        database.sqlite_database_path(),
        CLINICAL_CONTENT_MANIFEST_FILE,
    )

    _CLINICAL_CONTENT_CERTIFICATION = {
        "database_revision":
            content["database_revision"],
        "manifest_version":
            content["manifest_version"],
        "manifest_sha256":
            file_hash(
                CLINICAL_CONTENT_MANIFEST_FILE
            ),
    }

    return dict(
        _CLINICAL_CONTENT_CERTIFICATION
    )


def _require_content_certification(
    revision: str,
) -> dict:
    global _CLINICAL_CONTENT_CERTIFICATION

    # Production must have been certified by lifespan startup.
    # Development/test retains a lazy path for direct TestClient
    # calls that do not enter the lifespan context.
    if _CLINICAL_CONTENT_CERTIFICATION is None:
        if settings.environment == "production":
            raise RuntimeError(
                "Clinical content startup certification "
                "is unavailable."
            )

        _certify_clinical_content()

    state = _CLINICAL_CONTENT_CERTIFICATION

    if state is None:
        raise RuntimeError(
            "Clinical content certification unavailable."
        )

    if state["database_revision"] != revision:
        raise RuntimeError(
            "Runtime database revision differs from "
            "the startup-certified clinical content."
        )

    return dict(state)


@asynccontextmanager
async def lifespan(_: FastAPI):
    warnings = settings.assert_valid()
    for warning in warnings:
        logger.warning(warning, extra={"event": "configuration_warning"})
    _assert_runtime_files()
    database.assert_database_health(quick_check=True)
    revision = database.assert_schema_current()

    certification = _certify_clinical_content()

    if certification["database_revision"] != revision:
        raise RuntimeError(
            "Clinical content certification revision "
            "does not match runtime schema revision."
        )

    logger.info(
        "application_ready",
        extra={
            "event": "application_ready",
            "database_revision": revision,
            "api_version": API_VERSION,
            "clinical_content": "certified",
            "clinical_content_manifest_sha256":
                certification["manifest_sha256"],
        },
    )
    try:
        yield
    finally:
        database.engine.dispose()
        logger.info("application_shutdown", extra={"event": "application_shutdown", "api_version": API_VERSION})


app = FastAPI(
    lifespan=lifespan,
    title="Clinical Reference API & Dashboard",
    description="Bilingual SAE Diagnostics and Brazilian Public Health Policies",
    version=API_VERSION,
    docs_url="/api/docs" if ENABLE_API_DOCS else None,
    redoc_url="/api/redoc" if ENABLE_API_DOCS else None,
    openapi_url="/api/openapi.json" if ENABLE_API_DOCS else None,
)

app.mount("/docs", StaticFiles(directory=str(PDF_DIR), check_dir=True), name="docs")
app.mount("/assets", StaticFiles(directory=str(ASSET_DIR), check_dir=True), name="assets")

# TrustedHost blocks Host-header attacks. In production the settings validator forbids '*'.
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
# This limiter is defence-in-depth. The supplied nginx configuration is authoritative
# when multiple workers/instances are used.
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.rate_limit_enabled,
    api_limit_per_minute=settings.api_rate_limit_per_minute,
    search_limit_per_minute=settings.search_rate_limit_per_minute,
    max_clients=settings.rate_limit_max_clients,
)
app.add_middleware(RequestContextMiddleware, log_client_ip=settings.log_client_ip)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'",
    )
    if request.url.path.startswith("/api/"):
        # Clinical reference responses should not remain stale in shared/intermediary caches.
        response.headers.setdefault("Cache-Control", "no-store")
    elif request.url.path in {"/", "/sw.js", "/manifest.json"}:
        response.headers.setdefault("Cache-Control", "no-cache")
    if ENABLE_HSTS:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
api_v1 = APIRouter(prefix="/api/v1")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _normalise_search(value: object) -> str:
    text = unicodedata.normalize(
        "NFD",
        str(value or ""),
    )

    return "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    ).casefold()


def _sae_searchable_values(
    row: database.SAEDiagnostic,
) -> tuple[object, ...]:
    values: list[object] = [
        row.code,
        row.description_pt,
        row.description_en,
        row.nic_code,
        row.nic_label_pt,
        row.nic_label_en,
        row.noc_code,
        row.noc_label_pt,
        row.noc_label_en,
    ]

    for link in row.classification_links:
        values.extend(
            (
                link.code,
                link.label_pt,
                link.label_en,
            )
        )

    return tuple(values)


def _require_sae_enabled() -> None:
    if not ENABLE_SAE:
        raise HTTPException(
            status_code=503,
            detail="SAE/NANDA/NIC/NOC content is disabled by this deployment's administrator.",
        )


def _classification_link_payload(link: database.SAEClassificationLink) -> dict:
    return {
        "classification": link.classification,
        "code": link.code,
        "label_en": link.label_en,
        "label_pt": link.label_pt,
        "edition": link.edition,
        "role": link.role,
        "applicability": link.applicability,
        "applicability_en": link.applicability_en,
        "applicability_pt": link.applicability_pt,
        "confidence": link.confidence,
        "verification_status": link.verification_status,
        "source_language": link.source_language,
        "source_reference": link.source_reference,
        "source_page": link.source_page,
        "review_date": link.review_date,
        "notes": link.notes,
    }


def _sae_payload(row: database.SAEDiagnostic) -> dict:
    base = schemas.SAEDiagnosticOut.model_validate(row).model_dump()
    links = list(row.classification_links)
    base["nic_links"] = [_classification_link_payload(link) for link in links if link.classification == "NIC"]
    base["noc_links"] = [_classification_link_payload(link) for link in links if link.classification == "NOC"]
    return base


def _search_sae_rows(q: str, limit: int, offset: int, db: Session):
    _require_sae_enabled()

    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be blank.",
        )

    needle = _normalise_search(query)

    rows = (
        db.query(database.SAEDiagnostic)
        .options(
            selectinload(
                database.SAEDiagnostic.classification_links
            )
        )
        .order_by(
            database.SAEDiagnostic.code.asc()
        )
        .all()
    )

    matching = [
        row
        for row in rows
        if any(
            needle in _normalise_search(value)
            for value in _sae_searchable_values(row)
        )
    ]

    results = matching[
        offset:offset + limit
    ]

    if not results:
        raise HTTPException(
            status_code=404,
            detail=(
                "Nenhum diagnóstico encontrado "
                f"para a busca: '{query}'"
            ),
        )

    return query, results


def _get_policy_rows(policy_name: str, db: Session):
    name_clean = policy_name.strip().upper()
    if not name_clean or len(name_clean) > 20:
        raise HTTPException(status_code=422, detail="Invalid policy name.")

    results = (
        db.query(database.PublicHealthPolicy)
        .filter(database.PublicHealthPolicy.policy_name == name_clean)
        .order_by(database.PublicHealthPolicy.directive.asc())
        .all()
    )
    if not results:
        raise HTTPException(status_code=404, detail=f"No directives found for policy: {name_clean}")
    return name_clean, results


@app.get("/")
def read_root():
    if not INDEX_FILE.is_file():
        raise HTTPException(status_code=404, detail="index.html not found on server.")
    return FileResponse(INDEX_FILE)


@app.get("/favicon.ico", include_in_schema=False)
def read_favicon():
    return FileResponse(FAVICON_FILE, media_type="image/x-icon")


@app.get("/manifest.json")
def read_manifest():
    return FileResponse(MANIFEST_FILE)


@app.get("/sw.js")
def read_sw():
    return FileResponse(SERVICE_WORKER_FILE, media_type="application/javascript")


@api_v1.get("/livez", response_model=schemas.LivenessResponse)
def api_liveness():
    # Deliberately does not touch the database; this distinguishes process health
    # from readiness and prevents restart loops during a transient DB/storage issue.
    return {"status": "ok", "api_version": API_VERSION}


def _readiness_payload() -> dict:
    _assert_runtime_files()
    database.assert_database_health(quick_check=False)
    revision = database.assert_schema_current()
    certification = _require_content_certification(
        revision
    )

    return {
        "status": "ok",
        "database": "ok",
        "assets": "ok",
        "api_version": API_VERSION,
        "database_revision": revision,
        "sae_enabled": ENABLE_SAE,
        "clinical_content": "certified",
        "clinical_content_manifest_sha256":
            certification["manifest_sha256"],
    }


@api_v1.get("/readyz", response_model=schemas.ReadinessResponse)
def api_readiness():
    return _readiness_payload()


@api_v1.get("/healthz", response_model=schemas.ReadinessResponse)
def api_healthcheck():
    # Backwards-compatible v1 health endpoint now has readiness semantics.
    return _readiness_payload()


@api_v1.get("/sae/search", response_model=schemas.SAESearchResponse)
def api_search_sae(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query, results = _search_sae_rows(q, limit, offset, db)
    return {
        "query": query,
        "limit": limit,
        "offset": offset,
        "returned": len(results),
        "items": [_sae_payload(row) for row in results],
    }


@api_v1.get("/sae/metadata", response_model=schemas.SAEMetadataResponse)
def api_sae_metadata(db: Session = Depends(get_db)):
    _require_sae_enabled()
    record_count = db.query(func.count(database.SAEDiagnostic.id)).scalar() or 0
    link_count = db.query(func.count(database.SAEClassificationLink.id)).scalar() or 0
    contextual_count = (
        db.query(func.count(func.distinct(database.SAEClassificationLink.sae_diagnostic_id)))
        .filter(database.SAEClassificationLink.role == "alternative")
        .scalar() or 0
    )
    confidence_rows = (
        db.query(database.SAEDiagnostic.mapping_confidence, func.count(database.SAEDiagnostic.id))
        .group_by(database.SAEDiagnostic.mapping_confidence)
        .all()
    )
    status_rows = (
        db.query(database.SAEDiagnostic.mapping_status, func.count(database.SAEDiagnostic.id))
        .group_by(database.SAEDiagnostic.mapping_status)
        .all()
    )
    statuses = {status: count for status, count in status_rows if status}
    mapping_status = next(iter(statuses)) if len(statuses) == 1 else "mixed"
    return {
        "record_count": record_count,
        "link_count": link_count,
        "diagnoses_with_contextual_alternatives": contextual_count,
        "mapping_model": "compatibility primary plus contextual one-to-many NIC/NOC links",
        "code_format": "five-digit NANDA-I diagnostic identifier",
        "mapping_status": mapping_status,
        "mapping_methodology": "Context-aware educational mapping curated against current NANDA-I/NIC/NOC editions. Legacy primary NIC/NOC fields remain for compatibility, while contextual alternatives are exposed as one-to-many links. This is not an official crosswalk and does not substitute for clinical judgment.",
        "nanda_reference": "NANDA-I Nursing Diagnoses: Definitions and Classification 2024-2026, 13th edition",
        "nic_reference": "Nursing Interventions Classification (NIC), 8th edition",
        "noc_reference": "Nursing Outcomes Classification (NOC), 7th edition",
        "confidence_counts": {str(level or "unrated"): count for level, count in confidence_rows},
        "licensing_profile": "institutional_nonprofit_enabled",
        "licensing_note": "This build serves the NANDA-I reference PDF and enables SAE/NNN endpoints based on the deployer's stated institutional license. The actual institutional agreement remains controlling for redistribution and software-use scope.",
        "english_variant": "en-GB",
        "portuguese_variant": "pt-BR",
    }


def _normalized_nanda_code(raw_code: str) -> str:
    code = raw_code.strip()
    if not code.isdigit() or len(code) > 5:
        raise HTTPException(status_code=422, detail="NANDA-I code must contain 1 to 5 digits.")
    return code.zfill(5)


def _normalized_classification_code(raw_code: str, label: str) -> str:
    code = raw_code.strip()
    if not code.isdigit() or len(code) != 4:
        raise HTTPException(status_code=422, detail=f"{label} code must contain exactly 4 digits.")
    return code


@api_v1.get("/nanda/{code}", response_model=schemas.SAEDiagnosticOut)
def api_get_nanda(code: str, db: Session = Depends(get_db)):
    _require_sae_enabled()
    normalized = _normalized_nanda_code(code)
    row = db.query(database.SAEDiagnostic).filter(database.SAEDiagnostic.code == normalized).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"NANDA-I diagnosis not found: {normalized}")
    return _sae_payload(row)


def _classification_index(kind: str, db: Session):
    _require_sae_enabled()
    rows = (
        db.query(
            database.SAEClassificationLink.code,
            database.SAEClassificationLink.label_en,
            database.SAEClassificationLink.label_pt,
            database.SAEClassificationLink.edition,
            func.count(func.distinct(database.SAEClassificationLink.sae_diagnostic_id)),
        )
        .filter(database.SAEClassificationLink.classification == kind)
        .group_by(
            database.SAEClassificationLink.code,
            database.SAEClassificationLink.label_en,
            database.SAEClassificationLink.label_pt,
            database.SAEClassificationLink.edition,
        )
        .order_by(database.SAEClassificationLink.code.asc())
        .all()
    )
    return {
        "classification": kind,
        "returned": len(rows),
        "items": [
            {"code": code, "label_en": en, "label_pt": pt, "edition": edition, "mapped_diagnoses": count}
            for code, en, pt, edition, count in rows
        ],
    }


def _classification_detail(kind: str, raw_code: str, db: Session):
    _require_sae_enabled()
    code = _normalized_classification_code(raw_code, kind)
    rows = (
        db.query(database.SAEClassificationLink, database.SAEDiagnostic)
        .join(database.SAEDiagnostic, database.SAEDiagnostic.id == database.SAEClassificationLink.sae_diagnostic_id)
        .filter(
            database.SAEClassificationLink.classification == kind,
            database.SAEClassificationLink.code == code,
        )
        .order_by(database.SAEDiagnostic.code.asc(), database.SAEClassificationLink.role.asc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"{kind} code not found in curated mappings: {code}")

    first_link = rows[0][0]
    linked = []
    seen = set()
    for link, diagnosis in rows:
        key = (diagnosis.code, link.role, link.applicability)
        if key in seen:
            continue
        seen.add(key)
        linked.append({
            "nanda_code": diagnosis.code,
            "description_en": diagnosis.description_en,
            "description_pt": diagnosis.description_pt,
            "role": link.role,
            "applicability": link.applicability,
            "applicability_en": link.applicability_en,
            "applicability_pt": link.applicability_pt,
            "confidence": link.confidence,
            "verification_status": link.verification_status,
        })
    return {
        "classification": kind,
        "code": code,
        "label_en": first_link.label_en,
        "label_pt": first_link.label_pt,
        "edition": first_link.edition,
        "mapped_diagnoses": len({diagnosis.code for _, diagnosis in rows}),
        "linked_diagnoses": linked,
    }


@api_v1.get("/nic", response_model=schemas.ClassificationIndexResponse)
def api_nic_index(db: Session = Depends(get_db)):
    return _classification_index("NIC", db)


@api_v1.get("/nic/{code}", response_model=schemas.ClassificationMappingResponse)
def api_nic_detail(code: str, db: Session = Depends(get_db)):
    return _classification_detail("NIC", code, db)


@api_v1.get("/noc", response_model=schemas.ClassificationIndexResponse)
def api_noc_index(db: Session = Depends(get_db)):
    return _classification_index("NOC", db)


@api_v1.get("/noc/{code}", response_model=schemas.ClassificationMappingResponse)
def api_noc_detail(code: str, db: Session = Depends(get_db)):
    return _classification_detail("NOC", code, db)


@api_v1.get("/policies", response_model=schemas.PolicyIndexResponse)
def api_policy_index(db: Session = Depends(get_db)):
    rows = (
        db.query(database.PublicHealthPolicy.policy_name, func.count(database.PublicHealthPolicy.id))
        .group_by(database.PublicHealthPolicy.policy_name)
        .order_by(database.PublicHealthPolicy.policy_name.asc())
        .all()
    )
    return {"items": [{"policy_name": name, "directives": count} for name, count in rows]}


@api_v1.get("/policies/{policy_name}", response_model=schemas.PolicyListResponse)
def api_get_policy(policy_name: str, db: Session = Depends(get_db)):
    name, results = _get_policy_rows(policy_name, db)
    return {"policy_name": name, "returned": len(results), "items": results}


@api_v1.get(
    "/tools/news2/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_news2_metadata():
    """Return NEWS2 provenance and bilingual metadata."""
    return NEWS2_METADATA


@api_v1.post(
    "/tools/news2",
    response_model=schemas.NEWS2Response,
)
def api_news2_calculate(
    payload: schemas.NEWS2Input,
):
    """Calculate NEWS2 from one complete observation set."""
    try:
        return calculate_news2(
            respiration_rate=payload.respiration_rate,
            spo2=payload.spo2,
            spo2_scale=payload.spo2_scale,
            scale2_prescribed=payload.scale2_prescribed,
            supplemental_oxygen=payload.supplemental_oxygen,
            systolic_bp=payload.systolic_bp,
            pulse=payload.pulse,
            consciousness=payload.consciousness,
            temperature=payload.temperature,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/egfr-ckd-epi-2021/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_egfr_metadata():
    return EGFR_METADATA


@api_v1.post(
    "/tools/egfr-ckd-epi-2021",
    response_model=schemas.EGFRResponse,
)
def api_calculate_egfr(
    payload: schemas.EGFRInput,
):
    try:
        return calculate_egfr_ckd_epi_2021(
            age_years=payload.age_years,
            sex=payload.sex,
            serum_creatinine=payload.serum_creatinine,
            creatinine_unit=payload.creatinine_unit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/ckd-classification/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_ckd_metadata():
    return CKD_METADATA


@api_v1.post(
    "/tools/ckd-classification",
    response_model=schemas.CKDClassificationResponse,
)
def api_classify_ckd(
    payload: schemas.CKDClassificationInput,
):
    try:
        return classify_ckd(
            egfr_ml_min_1_73m2=payload.egfr_ml_min_1_73m2,
            acr=payload.acr,
            acr_unit=payload.acr_unit,
            chronicity_at_least_3_months=(
                payload.chronicity_at_least_3_months
            ),
            other_kidney_damage_marker=(
                payload.other_kidney_damage_marker
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/kdigo-aki/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_kdigo_aki_metadata():
    return AKI_METADATA


@api_v1.post(
    "/tools/kdigo-aki",
    response_model=schemas.KDIGOAKIResponse,
)
def api_calculate_kdigo_aki(
    payload: schemas.KDIGOAKIInput,
):
    try:
        return calculate_kdigo_aki(
            current_creatinine=payload.current_creatinine,
            current_creatinine_unit=(
                payload.current_creatinine_unit
            ),
            baseline_creatinine=payload.baseline_creatinine,
            baseline_creatinine_unit=(
                payload.baseline_creatinine_unit
            ),
            baseline_interval_hours=(
                payload.baseline_interval_hours
            ),
            weight_kg=payload.weight_kg,
            urine_output_ml=payload.urine_output_ml,
            urine_output_duration_hours=(
                payload.urine_output_duration_hours
            ),
            anuria_duration_hours=(
                payload.anuria_duration_hours
            ),
            renal_replacement_therapy=(
                payload.renal_replacement_therapy
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/hemodynamics/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_hemodynamics_metadata():
    return HEMODYNAMICS_METADATA


@api_v1.post(
    "/tools/hemodynamics",
    response_model=schemas.HemodynamicsResponse,
)
def api_calculate_hemodynamics(
    payload: schemas.HemodynamicsInput,
):
    try:
        return calculate_hemodynamics(
            systolic_bp=payload.systolic_bp,
            diastolic_bp=payload.diastolic_bp,
            heart_rate=payload.heart_rate,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/oxygenation/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_oxygenation_metadata():
    return OXYGENATION_METADATA


@api_v1.post(
    "/tools/oxygenation",
    response_model=schemas.OxygenationResponse,
)
def api_calculate_oxygenation(
    payload: schemas.OxygenationInput,
):
    try:
        return calculate_oxygenation(
            fio2_percent=payload.fio2_percent,
            pao2_mm_hg=payload.pao2_mm_hg,
            spo2_percent=payload.spo2_percent,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/acid-base-metabolic/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_metabolic_metadata():
    return METABOLIC_METADATA


@api_v1.post(
    "/tools/acid-base-metabolic",
    response_model=schemas.MetabolicToolkitResponse,
)
def api_calculate_metabolic(
    payload: schemas.MetabolicToolkitInput,
):
    try:
        return calculate_metabolic_toolkit(
            sodium_meq_l=payload.sodium_meq_l,
            chloride_meq_l=payload.chloride_meq_l,
            bicarbonate_meq_l=payload.bicarbonate_meq_l,
            albumin_g_dl=payload.albumin_g_dl,
            glucose_mg_dl=payload.glucose_mg_dl,
            bun_mg_dl=payload.bun_mg_dl,
            paco2_mm_hg=payload.paco2_mm_hg,
            metabolic_acidosis_confirmed=(
                payload.metabolic_acidosis_confirmed
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@api_v1.get(
    "/tools/who-growth/meta",
    response_model=schemas.ClinicalToolMetadataResponse,
)
def api_growth_metadata():
    return GROWTH_METADATA


@api_v1.post(
    "/tools/who-growth",
    response_model=schemas.GrowthResponse,
)
def api_calculate_who_growth(
    payload: schemas.GrowthInput,
):
    try:
        return calculate_who_growth(
            sex=payload.sex,
            age_value=payload.age_value,
            age_unit=payload.age_unit,
            age_basis=payload.age_basis,
            weight_kg=payload.weight_kg,
            length_height_cm=payload.length_height_cm,
            measurement_position=(
                payload.measurement_position
            ),
            head_circumference_cm=(
                payload.head_circumference_cm
            ),
            oedema=payload.oedema,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


app.include_router(api_v1)

# ---------------------------------------------------------------------------
# Compatibility routes (deprecated): preserve the original frontend/API shape
# while clients migrate to /api/v1. They intentionally reuse the same queries.
# ---------------------------------------------------------------------------
@app.get("/healthz", deprecated=True)
def healthcheck_compat():
    _readiness_payload()
    return {"status": "ok"}


@app.get("/sae/search", deprecated=True)
def search_sae_compat(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    _, results = _search_sae_rows(q, limit, offset, db)
    return results


@app.get("/policy/{policy_name}", deprecated=True)
def get_policy_compat(policy_name: str, db: Session = Depends(get_db)):
    name, results = _get_policy_rows(policy_name, db)
    return [
        {
            "id": row.id,
            "policy_name": name,
            "directive": row.directive,
            "target_demographic": row.target_demographic,
            "clinical_guideline": row.clinical_guideline,
        }
        for row in results
    ]


@app.get("/pnaism/", deprecated=True)
def get_pnaism_compat(db: Session = Depends(get_db)):
    _, results = _get_policy_rows("PNAISM", db)
    return [
        {
            "id": row.id,
            "directive": row.directive,
            "target_demographic": row.target_demographic,
            "clinical_guideline": row.clinical_guideline,
        }
        for row in results
    ]
