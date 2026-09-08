# Phase 6 dependency and supply-chain review

Review date: 2026-09-07

## Production policy

Production uses `requirements.lock` with exact versions and `scripts/check_dependencies.py`. `MEDICAL_API_ENFORCE_DEPENDENCY_LOCK=true` is the production default/example, so startup preflight fails when the active virtual environment does not exactly match the reviewed lock.

The per-release venv helper installs wheels only (`--only-binary=:all:`) and verifies the lock after installation. The Dockerfile uses the same lock.

## Reviewed framework set

- FastAPI 0.141.1
- Starlette 1.6.0
- Pydantic 2.13.5 / pydantic-core 2.46.5
- SQLAlchemy 2.0.52
- Uvicorn 0.52.4
- Alembic 1.19.2

Starlette is an **explicit** pin rather than an accidental transitive version. During the review, published 2026 advisories showed older Starlette ranges affected by Host/path reconstruction issues and an `application/x-www-form-urlencoded` resource-exhaustion issue; 1.6.0 is beyond those patched ranges.

Pydantic 2.13.5 and Alembic 1.19.2 superseded the older Pass 5 pins during this review, so the production lock was refreshed rather than freezing known-stale direct dependencies.

## Audit-environment limitation

The execution environment used for this Phase 6 pass cannot resolve external package hosts from the shell/pip environment. Therefore a brand-new virtual environment containing the reviewed lock could not be downloaded and executed here. This is not hidden by silently testing an old environment: `scripts/check_dependencies.py` reports the mismatch and production preflight is configured to reject it.

Application/unit/operations tests and production-like smoke/load tests in this environment use the already-installed framework set. The exact reviewed lock must be installed and re-run on the real staging platform as an explicit Phase 7 entry gate.

## Update procedure

Do not run unconstrained `pip install -U` in production. For dependency changes:

1. review current upstream releases and advisories;
2. update `requirements.txt` + `requirements.lock` intentionally;
3. create a clean venv and run `scripts/check_dependencies.py`;
4. run all Python/frontend/migration/operations tests;
5. repeat production preflight, load and smoke tests;
6. ship as a new immutable release.
