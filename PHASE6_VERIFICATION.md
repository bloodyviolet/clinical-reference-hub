# Phase 6 production/operations verification

> **Pass 6.1 note:** this document records the original Pass 6 / API 1.4 verification. The Pass 6.1 hotfix supersedes the runtime identity with API 1.4.1; see `PASS61_HOTFIX_QC.md`.


Date: 2026-09-07

## Scope boundary

This report covers Phase 6 only: production process/configuration hardening, reverse proxy, observability, rate limiting, health/readiness, dependency policy, database operations, backup/restore/rollback, service/container templates and local performance/operational tests. **No Phase 7 staging/UAT, clinician acceptance, assistive-technology UAT or final go/no-go acceptance is claimed here.**

## Application/runtime result

- API runtime version: **1.4**.
- Alembic/content database remains **0005**; Phase 6 makes no clinical mapping/schema changes.
- Source test suite: **31/31 passed**.
- Frontend calculator/static/contextual-NNN QC: passed.
- JavaScript syntax and Python compilation: passed.
- `alembic current`: `0005 (head)`.
- `alembic check`: no schema drift.
- Development preflight content counts: 277 SAE diagnoses / 627 classification links / 54 policy directives.

## Production HTTP/security smoke

Uvicorn was started from `/tmp` against a separate runtime DB with production configuration (exact dependency-lock enforcement disabled only because this audit host cannot download the reviewed wheels). Verified:

- liveness/readiness, SAE metadata, NANDA/NIC/NOC detail, root UI and public NANDA PDF return 200;
- NANDA PDF is `application/pdf` and 18,889,938 bytes;
- Swagger/OpenAPI UI disabled in production profile;
- disallowed Host rejected with HTTP 400;
- valid caller/proxy request ID preserved as `X-Request-ID`;
- HSTS emitted;
- search safety-net rate limiter produced 200/200/200/429 at a configured limit of three/minute;
- structured application logs include request IDs but **do not include query strings** (`q=00339` was absent);
- graceful SIGTERM shutdown completed and emitted the application-shutdown event.

## Load/concurrency probes on this audit host

These are local single-process measurements, not capacity commitments:

- `/api/v1/livez`: 400 requests, concurrency 32, 100% success, ~750.7 req/s, p95 ~59.4 ms.
- `/api/v1/nanda/00208`: 500 requests, concurrency 32, 100% success, ~181.8 req/s, p95 ~283.3 ms.
- `/api/v1/sae/search?q=00339`: 300 requests, concurrency 24, 100% success, ~180.4 req/s, p95 ~204.1 ms.

The clinical/read load results exercise SQLite concurrent reads and NNN serialization. Real staging hardware/network capacity testing remains Phase 7.

## Database operations drill

Against a disposable copy of the database:

1. online SQLite backup created;
2. adjacent SHA-256/size metadata generated and verified;
3. migration-with-backup procedure executed at revision 0005;
4. a known data mutation was introduced;
5. stopped-service restore replaced it with the verified backup;
6. `PRAGMA quick_check` and Alembic revision revalidated;
7. rollback helper created a pre-rollback safety backup and atomically switched a temporary current-release symlink;
8. target-release/backup revision guard passed.

## nginx/systemd/container template validation

- nginx 1.26.3: generated TLS test configuration passed `nginx -t`.
- systemd service, backup service and timer: `systemd-analyze verify` passed after substituting audit-safe paths/user values.
- Compose YAML parsed successfully; production dependency-lock setting present.
- shell syntax for production start and container entrypoint passed.
- A Docker/Podman daemon is not installed in this audit environment, so an actual image build/run cannot be executed here. That host-specific build is an explicit Phase 7 staging entry gate.

## Dependency review / fail-closed result

Reviewed production direct framework set:

- FastAPI 0.141.1
- Starlette 1.6.0
- Pydantic 2.13.5 / pydantic-core 2.46.5
- SQLAlchemy 2.0.52
- Uvicorn 0.52.4
- Alembic 1.19.2

`requirements.lock` pins the complete minimal runtime version set used by the supplied deployment recipes. Production defaults to `MEDICAL_API_ENFORCE_DEPENDENCY_LOCK=true`.

The shell/pip environment in this audit container has no external package-DNS access. Its already-installed FastAPI/Starlette/SQLAlchemy/Uvicorn versions are older than the reviewed lock. This condition was deliberately tested: production preflight exited non-zero with `Runtime dependency lock mismatch`. No claim is made that the old audit-host environment equals the deployable production environment.

## Phase 6 conclusion

**PASS for all Phase 6 work executable in this environment**, subject to the documented infrastructure boundary: the reviewed lock and Docker/systemd/nginx topology must be installed and exercised on the real staging host before release acceptance. That staging installation and human/clinical/accessibility UAT is Phase 7 and has not begun.
