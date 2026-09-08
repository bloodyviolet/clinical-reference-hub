# Clinical Reference Hub 🩺

*(Scroll down for the Portuguese version / Role para baixo para a versão em Português)*

---

## 🇬🇧 English (UK)

A bilingual FastAPI/SQLite reference API and web dashboard for Nursing Care Systematisation (SAE) and Brazilian public-health policies (SUS).

### Features

- **Bilingual SAE / NNN database:** 277 current NANDA-I 2024–2026 diagnoses with structured primary NIC 8th / NOC 7th mappings, per-row confidence, rationale, source reference and NANDA page provenance in Portuguese (pt-BR) and English (en-GB).
- **SUS policy explorer:** unified policy model for PNAISM, PNAISH, PNAISC, PNAB, PNSTT, PNSPI and PNSIPN.
- **Policy provenance:** source URL/title, publication/effective dates, source version, pinpoint locator, evidence tier, clinical-review date/status and review notes are returned by API v1.
- **Clinical calculators/scales:** guarded inputs and fail-closed validation for the included decision-support calculators.
- **Versioned API:** typed Pydantic responses under `/api/v1`, with deprecated legacy routes retained for compatibility.
- **Alembic migrations:** persisted databases are upgraded rather than implicitly recreated.

### Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python migrate.py
python seed_sae.py
python seed_policies.py

uvicorn main:app --host 127.0.0.1 --port 8000
```

The database schema is checked at application startup. If the SQLite file is behind the code migration head, startup fails with an instruction to run `python migrate.py`.

### API v1

- `GET /api/v1/healthz`
- `GET /api/v1/sae/search?q=...&limit=20&offset=0`
- `GET /api/v1/sae/metadata`
- `GET /api/v1/nanda/{code}`
- `GET /api/v1/nic`
- `GET /api/v1/nic/{code}`
- `GET /api/v1/noc`
- `GET /api/v1/noc/{code}`
- `GET /api/v1/policies`
- `GET /api/v1/policies/{POLICY}`
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

Legacy `/healthz`, `/sae/search`, `/policy/{name}` and `/pnaism/` routes remain available but are deprecated.

### SAE / NNN mapping status

The bundled SAE database is at mapping revision **Pass 5 / API 1.3**:

- NANDA-I 2024–2026, 13th edition: 277/277 project diagnoses reconciled;
- NIC 8th edition: 120 codes represented across primary/contextual links;
- NOC 7th edition: 136 codes represented across primary/contextual links;
- 627 total classification links (554 primary + 73 contextual alternatives);
- primary confidence: 229 high / 48 moderate;
- all 277 rows include rationale/reference and printed + actual PDF page metadata;
- user-facing English is localised to **en-GB** and Portuguese to **pt-BR**, while classification codes/editions remain the canonical identifiers.

The crosswalk is curated by this project and is not presented as an official INKA/University of Iowa linkage. See `SAE_MAPPING_QC.md` and `sae_mapping_review.csv`.

### Production / rights-sensitive deployment

The dashboard ships with a locally built Tailwind stylesheet; the browser Play CDN is no longer used. To rebuild it after editing classes:

```bash
npm install
npm run build:css
```

Runtime hardening switches:

```bash
# Disable Swagger/ReDoc/OpenAPI routes
MEDICAL_API_ENABLE_DOCS=false

# Enable HSTS only when the service is actually behind HTTPS
MEDICAL_API_HSTS=true

# Optional administrative kill-switch for SAE/NANDA/NIC/NOC endpoints
MEDICAL_API_ENABLE_SAE=false
```

This Pass 6 package is intentionally configured with SAE enabled and includes the institutional NANDA-I 2024–2026 PDF in the public `/docs/` tree, following the deployment/license context supplied for this project. The actual institutional agreement remains controlling; see `LICENSING_REVIEW.md`.

Public NANDA-I reference: `/docs/Nanda-I%202024-2026.pdf`.

### Tests / QC

```bash
pip install -r requirements-dev.txt
pytest -q
node tests/frontend_qc.js
alembic check
```

See `QC_FIXES.md` for the remediation history and `CLINICAL_CONTENT_QC.md` for the current clinical-content review scope/limitations.

---

## 🇧🇷 Português (BR)

API e dashboard bilíngues em FastAPI/SQLite para Sistematização da Assistência de Enfermagem (SAE) e consulta de políticas públicas brasileiras de saúde (SUS).

### Funcionalidades

- **Base SAE / NNN bilíngue:** 277 diagnósticos NANDA-I 2024–2026 reconciliados com a fonte atual, com mapeamentos primários estruturados para NIC 8ª ed. e NOC 7ª ed., confiança, racional, referência e páginas NANDA.
- **Explorador de políticas do SUS:** modelo unificado para PNAISM, PNAISH, PNAISC, PNAB, PNSTT, PNSPI e PNSIPN.
- **Proveniência das políticas:** título/URL da fonte, datas, versão normativa, data/status de revisão clínica e observações de QC disponíveis pela API v1.
- **Calculadoras e escalas clínicas:** validações de entrada e rejeição de estados inválidos nas ferramentas incluídas.
- **API versionada:** respostas tipadas com Pydantic em `/api/v1`, mantendo rotas antigas como compatibilidade depreciada.
- **Migrações Alembic:** bancos persistidos são migrados em vez de recriados implicitamente.

### Instalação local

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python migrate.py
python seed_sae.py
python seed_policies.py

uvicorn main:app --host 127.0.0.1 --port 8000
```

A revisão do banco é validada na inicialização. Se o SQLite estiver atrás da revisão esperada, a API falha de forma explícita e orienta executar `python migrate.py`.

### Segurança clínica

As calculadoras e mapeamentos são ferramentas de apoio/educação e não substituem avaliação individual, protocolos locais, conferência de medicamentos ou julgamento clínico profissional. Consulte `CLINICAL_CONTENT_QC.md`, `POLICY_PROVENANCE_QC.md` e `SAE_MAPPING_QC.md` para o estado exato da validação clínica, documental e dos mapeamentos.

---

## Tech Stack

- Python / FastAPI / Pydantic
- SQLAlchemy / SQLite / Alembic
- HTML / JavaScript / Tailwind CSS 4.1.10 compiled locally
- Uvicorn; suitable for deployment behind a hardened reverse proxy

## Author / Autor

**Saulo de Tarso Sobral Alves (Bloodviolet)**


## Pass 6 — production/operations hardening

Pass 6.1 hotfix advances the runtime API version to **1.4.1** while keeping the Alembic database revision at `0005`. It fixes Portuguese SAE intervention leakage, replaces the CSP-blocked external PWA icon with packaged local icons, and adds versioned offline SAE/policy bundles with frontend fallback. The underlying Pass 6 production hardening remains unchanged. The packaged PWA/favicon now uses the user-selected **Nursing Clinical Hub** brand artwork; the exact original source plus a transparent isolated icon master are kept under `brand/` for the planned future app.

Pass 6 advances the runtime API version to **1.4** without changing clinical classification content or database revision (`0005`). It adds production fail-closed configuration, TrustedHost/proxy controls, request IDs, JSON access logs without query strings, in-app defence-in-depth rate limiting, separate liveness/readiness endpoints, exact dependency-lock enforcement, online SQLite backup/verified restore/rollback tooling, nginx TLS/rate-limit templates, hardened systemd units, a non-root Docker deployment option, load probes and a complete `DEPLOYMENT_RUNBOOK.md`.

Production installations should create a per-release virtual environment with `scripts/create_release_venv.sh`, keep the database outside the immutable release tree, set `MEDICAL_API_ENFORCE_DEPENDENCY_LOCK=true`, and run behind nginx (or an equivalent trusted reverse proxy). See `SECURITY_DEPENDENCY_REVIEW.md` and `PHASE6_VERIFICATION.md`.

Phase 6 deliberately does **not** perform Phase 7 staging/UAT, clinician acceptance, screen-reader/browser UAT or real-host TLS/DNS acceptance.

## Pass 5 — Licensed NIC/NOC source audit and contextual NNN links

Pass 5 uses the institutionally supplied Spanish NIC 8th-edition and NOC 7th-edition references for the NNN audit while keeping the deployed interface/API bilingual in **English UK (en-GB) + Brazilian Portuguese (pt-BR)**.

The main structural change is that NNN mapping is no longer represented as if each NANDA-I diagnosis had exactly one universally correct NIC and one universally correct NOC. API **v1.3** / database revision **0005** retains a compatibility primary pair for backward compatibility and adds one-to-many contextual NIC/NOC links.

Current NNN dataset:

- 277 NANDA-I diagnoses;
- 554 primary NIC/NOC links;
- 73 contextual alternatives;
- 627 total classification links;
- 26 diagnoses with contextual alternatives;
- primary confidence 229 high / 48 moderate;
- 120 distinct NIC codes and 136 distinct NOC codes represented across all links.

The contextual alternatives cover cases where phase, age, substance, risk direction, or care setting materially changes the appropriate classification target. See `NNN_CURRENT_EDITION_AUDIT.md`, `SAE_MAPPING_QC.md`, `sae_mapping_review.csv`, `nnn_link_review.csv`, and `data/nnn_source_manifest.json`.

The supplied NIC/NOC source books are audit/reference material and are **not** copied into the deployment ZIP. The public NANDA-I PDF configuration remains unchanged from Pass 4 under the stated institutional license context.


## Pass 6.1 offline bundle maintenance

After intentionally changing SAE or policy content, rebuild the packaged offline datasets before release verification:

```bash
python scripts/build_offline_data.py
```

Production preflight fails if the offline SAE/policy bundle counts or database revision no longer match the packaged runtime database.

### Pass 6.1.1 browser-offline follow-up

Pass 6.1.1 advances the runtime API version to **1.4.2** without a schema change. Real browser UAT showed that Pass 6.1's two-stage offline fallback could still leave SAE search and policy requests at service-worker 503 responses. Pass 6.1.1 moves the browser-facing offline API fallback into the service worker itself, retains a direct Cache Storage fallback in the frontend, forces fresh shell precaching, and cache-busts the manifest URL to eliminate stale PWA metadata. See `PASS611_HOTFIX_QC.md`.
