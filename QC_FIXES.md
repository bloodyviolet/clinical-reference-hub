# QC Remediation Log

## Pass 1 — runtime, safety and calculator hardening

- Resolved SQLite, PDF, HTML, manifest, and service-worker paths relative to the application directory rather than the process working directory.
- Added a database-backed health check and connected the UI status badge to it.
- Hardened SAE search: blank input rejection, 100-character query cap, literal `%`/`_` handling, deterministic ordering, `limit`/`offset`, and a maximum of 100 records per request.
- Reworked the service worker so offline/network failures return HTTP 503 rather than fake HTTP 200 success responses.
- Made SAE and policy rendering HTML-escape all database-derived fields before interpolation.
- Made seed operations transactional and validate replacement data before destructive deletes.
- Converted obsolete HTTP seeders into compatibility wrappers around the transactional local seeder.
- Updated confirmed stale PNAISM/PNSIPN clinical content.
- Hardened medication, BMI, Cockcroft-Gault, fluid, McDonald, Glasgow and Apgar calculators.
- Restored browser zoom and added pinned dependencies/regression tests.

## Pass 2 — schema/API/provenance and clinical-content structure

### Database and migrations

- Added Alembic as the schema source of truth.
- Added migration `0001` to:
  - migrate legacy databases into a single `public_health_policies` table;
  - copy legacy PNAISM rows into that table;
  - remove `pnaism_policies`;
  - add policy provenance/version/review fields.
- Added migration `0002` to normalize the legacy SAE table:
  - `code` is schema-level `NOT NULL`;
  - redundant primary-key index is removed;
  - the unique code index now matches SQLAlchemy metadata exactly.
- `alembic check` reports **no pending schema drift**.
- `database.init_db()` now upgrades through Alembic instead of bypassing migrations with `create_all()`.
- The application fails fast at Uvicorn startup if the database revision does not match the migration head.
- `MEDICAL_API_DATABASE_URL` can override the SQLite location for testing/deployment.

### Unified public-policy model

- Removed the separate `PNAISMPolicy` ORM model.
- PNAISM is now stored and queried exactly like every other public-health policy.
- Added a uniqueness constraint on `(policy_name, directive)`.
- Every seeded policy row now has:
  - `source_title`
  - `source_url`
  - `source_page`
  - `source_publication_date`
  - `effective_from`
  - `effective_until`
  - `last_clinical_review`
  - `source_version`
  - `status`
  - `review_notes`
- Centralized all policy content and source metadata in `policy_data.py` so seed scripts cannot silently diverge.
- Added `seed_policies.py` as the canonical seeder; legacy `seed_pnaism.py` and `seed_all_policies.py` remain compatible wrappers.
- Policy seeding validates required fields, HTTPS source URLs, ISO dates, statuses, and rejects raw `[cite: ...]` placeholders.

### API v1 and typed responses

- Added Pydantic response schemas in `schemas.py`.
- Added versioned endpoints:
  - `GET /api/v1/healthz`
  - `GET /api/v1/sae/search`
  - `GET /api/v1/policies`
  - `GET /api/v1/policies/{policy_name}`
- SAE search now returns a typed envelope with query/limit/offset/returned/items.
- Policy endpoints return provenance and clinical-review metadata.
- `/api/docs`, `/api/redoc`, and `/api/openapi.json` are enabled for the versioned API.
- Original `/healthz`, `/sae/search`, `/policy/{name}`, and `/pnaism/` routes remain as deprecated compatibility routes with their legacy response shapes.
- The frontend now consumes `/api/v1` rather than the compatibility routes.
- Policy cards now display the source, source version, review date and status; outbound source links are restricted to HTTPS.

### First systematic clinical-content QC sweep

The pass reviewed all policy rows for obvious stale labels, unsafe overstatement, obsolete implementation names, stale epidemiological percentages, and source mismatch. This is **not yet a source-page-by-source-page legal/clinical verification of every sentence**; rows using only the base policy source state that limitation in `review_notes`.

Corrections include:

- PNAISH prostate content now explicitly states that MS/INCA does not recommend population PSA/DRE screening of asymptomatic men and emphasizes diagnosis of symptomatic disease/shared decision-making when screening is requested.
- PNAB `NASF` current-implementation wording replaced with the current `eMulti` model and Portaria GM/MS nº 635/2023.
- PNAISC neonatal screening timing corrected (heel-prick 48 h–5th day; heart screen 24–48 h; eye/hearing timing clarified).
- PNAISC micronutrient text no longer implies universal supplementation outside current programme criteria.
- PNAISM breast and cervical screening split into separate directives with separate current sources.
- PNAISM terminology updated from `DST` to `IST`.
- PNAISM climacteric care no longer presents hormone therapy as blanket treatment; it requires individual clinical indication and risk/benefit/contraindication review.
- PNAISM incarcerated-women wording now reflects current federal childbirth/immediate-puerperium restraint protections rather than an overbroad abortion-handcuff claim.
- PNSTT wording no longer presumes occupational causal nexus or hard-codes notification/CAT mechanics where the applicable legal flow can vary.
- PNSPI IVCF-20 content is tied to current Ministry implementation in e-SUS APS.
- PNSIPN stale 2012 percentages and race-essentialist diagnostic wording were removed; content now focuses on equity, access, determinants and current clinical pathways.
- Stale-content scan now finds **zero** occurrences of `Rede Cegonha`, `RAMI`, `NASF`, `DST`, `[cite:]`, the old 25–59 cervical range, or the previously identified 2012 race statistics in seeded policy text.

## Verification after Pass 2

- **13/13** Python regression/migration tests passing.
- Frontend calculator/API assertions passing.
- Python compilation passing.
- JavaScript syntax check passing.
- `alembic check`: no new upgrade operations detected.
- Fresh-database migration tested.
- Emulated legacy two-policy-table migration tested with data preservation.
- Actual bundled database upgraded to revision `0002`.
- Runtime smoke test from `/tmp` (wrong working directory) passed for UI, health, SAE, PNAISM and OpenAPI.
- Unified policy database contains **54 directives across 7 policies**.
- All 54 policy rows have nonblank source title/HTTPS URL/review date/status.

## Pass 3 — production assets, evidence tiers, SAE mapping provenance and deployment hardening

### Frontend / production assets

- Removed the Tailwind browser Play CDN and replaced it with `assets/app.css`, generated locally from the dashboard class set.
- Added a pinned `package.json` + `scripts/build_css.cjs` local build step using Tailwind 4.1.10 / PostCSS 8.5.6.
- Service-worker app shell now caches the local stylesheet.
- Fixed an invalid duplicate/nested drip-calculator `<form>` discovered during the accessibility pass.
- Added explicit `for`/`id` associations for all calculator/scale labels, tab semantics (`tablist`/`tab`/`tabpanel`), `aria-selected`, and live regions for dynamic status/results.

### Security / deployment controls

- Added baseline response headers: CSP, `X-Content-Type-Options`, frame denial, referrer policy, permissions policy and COOP.
- Added optional HSTS via `MEDICAL_API_HSTS=true` for real HTTPS deployments.
- Added optional API-documentation disabling via `MEDICAL_API_ENABLE_DOCS=false`.
- Added `MEDICAL_API_ENABLE_SAE=false` so public deployments can disable NANDA/NIC/NOC-backed endpoints when applicable rights have not been confirmed.

### SAE data and mapping QC

- Added migration `0003` with SAE mapping provenance fields and policy `evidence_level`.
- Corrected diagnosis-code normalization: all 277 project codes now persist/display as five-digit identifiers, preserving leading zeroes.
- Added per-row `mapping_status`, `mapping_methodology`, optional review date and review notes.
- Current 277 mappings are deliberately marked `suggested_unverified`; the API no longer implies that the local NANDA→NIC→NOC links are an official crosswalk.
- Added `GET /api/v1/sae/metadata` with mapping/licensing context.
- Structural mapping audit: 277/277 EN/PT NIC/NOC identifier pairs are internally consistent; the dataset uses 44 unique NIC identifiers and 41 unique NOC identifiers.
- Added `sae_mapping_review.csv` to prioritize semantic review by reuse concentration.

### Classification-content redistribution review

- Removed the bundled NANDA-I PDF from the publicly served `/docs/` tree.
- Removed obsolete `nanda.csv`, leaving `sae_bilingual_final.csv` as the single project SAE seed dataset.
- Added `private_references/` guidance and ignore rules for licensed local source copies.
- Added `LICENSING_REVIEW.md`; the deployer must confirm the actual permissions applicable to software/database/public redistribution.

### Policy provenance / clinical-content QC

- Added machine-readable evidence tiers: `current_override`, `pinpoint_policy`, `policy_context`, `policy_level`.
- All 54 rows are now classified: **10 current overrides, 40 pinpoint base-policy rows, 4 policy-context rows, 0 generic policy-only rows**.
- Added article/page/section locators for the base-policy rows where direct support was identified.
- Explicitly downgraded broad/contextual rows instead of overstating direct policy support.
- Updated the PNAISM legal-interruption summary to current Ministry access wording and removed technique-specific wording that could be interpreted as universal.
- Added `POLICY_PROVENANCE_QC.md`.

## Verification after Pass 3

- **18/18** Python API/migration/security regression tests passing.
- Frontend calculator and production-static assertions passing.
- Inline JavaScript syntax check passing.
- Python compilation passing.
- `alembic check`: no new upgrade operations detected.
- Bundled database at revision `0003`.
- **277/277** SAE identifiers are five-digit numeric strings.
- **277/277** SAE rows carry `suggested_unverified` mapping status.
- **54/54** policy rows have a nonblank source locator.
- Policy evidence distribution: **10 current_override / 40 pinpoint_policy / 4 policy_context / 0 policy_level**.
- Wrong-working-directory runtime smoke check still succeeds with local CSS/static assets.
- Bundled NANDA-I PDF now returns 404 because it is no longer in the public static tree.
- Rights-sensitive switches tested: docs disabled → 404; SAE disabled → 503 while health/policies remain available.

## Remaining work

- Perform semantic, source-by-source clinical validation of all 277 NANDA→NIC→NOC links using appropriately licensed classification sources; the structural audit alone does not certify mappings.
- After semantic review, record reviewer/date/methodology and promote only verified mapping rows from `suggested_unverified`.
- Conduct a real browser accessibility pass (keyboard-only navigation, screen reader, contrast/focus testing), beyond static markup checks.
- Consider eliminating inline JavaScript/event handlers so CSP can drop `script-src 'unsafe-inline'`.
- Add reverse-proxy deployment examples (TLS termination, trusted proxy headers, rate limiting) for the intended hosting platform.
- Consider SQLite FTS5/accent-normalized SAE search if dataset size or query volume grows materially.

## Pass 4 — current-edition NNN remap, licensed SAE restoration, structured classification API and CSP completion

### Licensed SAE / NANDA restoration

- Restored `pdfs/Nanda-I 2024-2026.pdf` to the publicly served `/docs/` tree at the deployer's request and under the stated institutional non-profit license context.
- SAE/NANDA/NIC/NOC remains enabled by default; `MEDICAL_API_ENABLE_SAE=false` is retained only as an optional administrative deployment switch.
- Updated `LICENSING_REVIEW.md` so this build documents the selected institutional deployment profile without asserting that non-profit status alone creates redistribution rights.

### Current-edition baseline and NANDA reconciliation

- Confirmed the September 2026 baselines:
  - NANDA-I 2024–2026, 13th edition (current diagnosis classification);
  - NIC 8th edition;
  - NOC 7th edition.
- Confirmed from INKA that NANDA 360 / the 14th-edition integrated classification is expected in 2027 rather than treating an unpublished taxonomy as current.
- Parsed the institutional NANDA-I PDF and confirmed **277/277** project diagnosis codes are present in the current classification.
- Added NANDA edition/domain/class, printed source page and actual PDF-viewer page to each SAE row.
- Re-sourced Portuguese diagnosis labels from the detailed 2024–2026 records; **17 labels** changed from the inherited CSV, including substantive current-wording corrections and line-wrap repairs.
- Dashboard NANDA deep links now use the actual PDF page rather than incorrectly treating the printed page number as the PDF page index.

### NANDA → NIC → NOC rebuild

- Rebuilt all **277** primary mappings against the current-edition baseline.
- Mapping status is now `curated_current_editions` for 277/277 rows.
- Confidence distribution: **217 high / 60 moderate**.
- Mapping diversity increased from 44 → **108 unique NIC** codes and 41 → **108 unique NOC** codes.
- Added structured fields for NIC/NOC edition, code and bilingual label plus mapping confidence, reference and rationale.
- Generated locally authored intervention/evaluation guidance rather than reproducing classification definitions/activities/indicator text.
- Rebuilt `sae_mapping_review.csv` with current mappings, reuse counts, evidence basis and review priority.
- Locked known corrections into tests, including `00322 → NIC 0620`, `00339 → NIC 5515 / NOC 2015`, `00475 → NIC 5100 / NOC 1203`, and `00348 → NIC 1160 / NOC 0110`.
- The API explicitly describes the links as a project-curated crosswalk, **not** an official INKA/Iowa linkage.

### Structured SAE / NANDA / NIC / NOC API

- Added migration `0004` with structured NNN provenance fields and NIC/NOC indexes.
- API version advanced to **1.2**.
- Added:
  - `GET /api/v1/nanda/{code}`
  - `GET /api/v1/nic`
  - `GET /api/v1/nic/{code}`
  - `GET /api/v1/noc`
  - `GET /api/v1/noc/{code}`
- SAE search now also accepts NIC/NOC codes and bilingual NIC/NOC labels.
- `GET /api/v1/sae/metadata` now reports the current editions, confidence distribution and institutional deployment profile.

### Frontend / CSP completion

- Moved all application JavaScript out of `index.html` into `assets/app.js`.
- Removed every inline `onclick`, `onsubmit` and `onchange` handler and replaced them with declarative data attributes / event listeners.
- Added keyboard navigation for the tablist (arrow keys, Home, End).
- Tightened CSP from `script-src 'self' 'unsafe-inline'` to **`script-src 'self'`**.
- Updated the service-worker app shell to cache `assets/app.js` and bumped the cache version.
- SAE result cards now show structured NIC/NOC codes/labels, confidence, mapping rationale/reference, NANDA domain/class and source-page links.

## Verification after Pass 4

- **22/22** Python API/migration/security regression tests passing.
- Frontend calculator and static-hardening assertions passing.
- `node --check assets/app.js` passing.
- `alembic check`: no new upgrade operations detected.
- Bundled database revision: **0004**.
- SAE rows: **277**; all five-digit codes.
- Current mapping status: **277/277 `curated_current_editions`**.
- Mapping confidence: **217 high / 60 moderate**.
- Unique primary NIC/NOC codes: **108 / 108**.
- NANDA provenance: **277/277** domain/class/printed-page/PDF-page fields populated.
- Public NANDA-I PDF endpoint restored and covered by regression test.
- Inline event handlers/scripts removed; CSP no longer needs `'unsafe-inline'`.
- Bilingual locale gate: **277/277** rows have populated EN/PT diagnosis, intervention, outcome, NIC-label and NOC-label fields; API metadata declares **en-GB + pt-BR**.
- en-GB regression scan rejects inherited US spellings such as `Behavior`, `Counseling`, `Organization`, `Aging` and `Labor` in deployed English NNN text.
- Final deployment smoke test from `/tmp` passed for UI, assets, health, SAE metadata, NANDA/NIC/NOC endpoints, API docs and the public NANDA-I PDF.

## Remaining NNN work

- Institution-level expert review should focus first on the **60 moderate-confidence** mappings, then the 97 high-confidence rows whose evidence is primarily current-edition baseline + semantic fit rather than a diagnosis-specific published linkage.
- A single NIC/NOC pair is intentionally only a primary educational mapping; real care plans may require multiple interventions/outcomes and patient-specific selection of licensed activities/indicators.
- If the institution can provide machine-readable/licensed NIC 8th and NOC 7th source exports, a future pass can perform exhaustive code/label reconciliation against those local licensed sources rather than relying on edition metadata plus peer-reviewed/public evidence for code-label checks.

# Pass 5 — Licensed NIC/NOC source audit and contextual NNN mapping

Review date: **2026-09-07**

## Source verification

- Added the institutionally supplied Spanish **NIC 8th edition** and **NOC 7th edition** as audit sources (not bundled in the deployment package).
- Recorded source hashes/page counts and audit purpose in `data/nnn_source_manifest.json`.
- Preserved the API/display language contract as **en-GB + pt-BR**; source language is recorded separately as `es`.
- Added `NNN_CURRENT_EDITION_AUDIT.md` documenting methodology, limitations and code corrections.

## NNN data-model upgrade

- Added Alembic migration `0005_contextual_nnn_links`.
- Added `sae_classification_links`, allowing one diagnosis to carry multiple context-specific NIC/NOC choices.
- Retained one NIC and one NOC compatibility primary in the existing SAE record for backward compatibility.
- API version advanced to **1.3**.
- SAE/NANDA responses now expose `nic_links` and `noc_links` with role, applicability, confidence, verification status, source language/reference and review metadata.
- NIC/NOC index/detail endpoints now aggregate the link table rather than only the legacy primary fields.
- Search now matches contextual NIC/NOC codes and bilingual labels.

## Current-edition corrections

- Removed legacy NIC `1054` from the mapping set; breastfeeding care uses current NIC `5244` where appropriate.
- Removed legacy NIC `6780`; current phase-specific pregnancy codes are used instead.
- Corrected NIC `8274` to the current label **Child Care**.
- Corrected gastrointestinal-function outcome from NOC `1050` to `1015`.
- Corrected/strengthened current NOC targets including `0414`, `0910`, `1405`, `1613`, `1914`, `1920`, `1932`, `2108`, `2509`, `2501`, `2704` and related context-specific alternatives.
- Added pregnancy-phase, developmental-age, withdrawal/substance, breastfeeding/skin, haemodynamic-risk and community-context alternatives.

## Current counts

- 277 diagnoses.
- 554 compatibility primary links.
- 73 contextual alternatives.
- 627 total NNN links.
- 26 diagnoses with contextual alternatives.
- Primary confidence: 229 high / 48 moderate.
- 110 unique primary NIC / 115 unique primary NOC codes.
- 120 NIC / 136 NOC codes represented across all links.
- Mapping status: 277/277 `curated_current_editions_contextual`.

## QC artifacts

- Refreshed `sae_mapping_review.csv` (277 diagnosis-level rows).
- Added `nnn_link_review.csv` (627 link-level rows).
- Added `data/nnn_source_manifest.json`.
- Updated `SAE_MAPPING_QC.md`.

## Automated verification status before final package gate

- Python API/migration suite: **25 tests passing**.
- Alembic current: `0005`.
- `alembic check`: no schema drift.
- Frontend JS syntax and static QC passing after contextual-link UI rendering was added.

# Pass 6 — production and operations hardening

Review date: **2026-09-07**

- API runtime version advanced to **1.4**; clinical data and Alembic schema remain at Pass 5 / `0005`.
- Added fail-closed production configuration validation for allowed hosts, HTTPS public origin, trusted proxy IP/CIDRs, HSTS and rate limiting.
- Added `TrustedHostMiddleware`, separate `/api/v1/livez` and `/api/v1/readyz`, request IDs, structured JSON access logs and privacy-preserving omission of query strings.
- Added an in-process sliding-window rate limiter as defence in depth; nginx remains authoritative for multi-process deployments.
- Added SQLite foreign-key/busy-timeout configuration and readiness/integrity checks.
- Added online-consistent backup, SHA-256 metadata verification, stopped-service restore, migration-with-backup and revision-guarded atomic release rollback tooling.
- Added exact production dependency lock enforcement and per-release venv creation. Starlette is explicitly pinned at 1.6.0 to avoid resolving older 2026-vulnerable ranges.
- Refreshed reviewed direct dependencies to FastAPI 0.141.1, Starlette 1.6.0, Pydantic 2.13.5, SQLAlchemy 2.0.52, Uvicorn 0.52.4 and Alembic 1.19.2.
- Added hardened nginx reference configuration: TLS 1.2/1.3, HSTS on proxy errors, 64 KiB body cap, request IDs, HTTP 429 rate-limit semantics, search/general budgets, health exemptions and upstream Server suppression.
- Added hardened systemd service/backup timer and non-root Docker/Compose reference deployment.
- Added production preflight, dependency check, health probe and dependency-free concurrency/load probe.
- Added `DEPLOYMENT_RUNBOOK.md` and `SECURITY_DEPENDENCY_REVIEW.md`.
- Expanded automated suite from 26 to **31 tests** with production config, rate limiter, readiness/request-ID/cache and backup/restore regression coverage.
- Phase 7 staging/UAT work is intentionally excluded from this pass.


## Pass 6.1 UAT hotfix

Triggered by browser UAT after the successful Pass 6 production cutover.

- Fixed a generator defect where all 277 Portuguese `intervention_pt` strings embedded the English NANDA diagnosis text. `local_activity_text()` now receives both language variants and uses `description_pt` in the Portuguese sentence.
- Regenerated `sae_bilingual_final.csv` and `medical.db`; all 277 Portuguese intervention strings now contain the Portuguese diagnosis and none contain the full English diagnosis.
- Replaced the external Flaticon manifest icon, which production CSP correctly blocked, with the user-selected **Nursing Clinical Hub** artwork packaged under `assets/icons/`; CSP remains unchanged and strict. The original 1024x1024 source is preserved unchanged under `brand/`, alongside a transparent reusable 1024x1024 icon master with the outer light presentation background removed for the future client app.
- Added deterministic offline SAE and SUS-policy bundles (`assets/offline/sae.json`, `assets/offline/policies.json`) generated from the packaged database.
- Added frontend fallback for SAE search and policy rendering when the API is unreachable/offline. Online API responses remain authoritative; rate-limit and normal online HTTP errors do not silently fall back.
- Added explicit `Modo Offline · dados locais` status and offline-result notices.
- Marked intentionally English technical provenance text as `(EN)` and translated confidence/verification status labels shown in the Portuguese UI.
- Bumped the service-worker cache to `clinical-reference-v6-pass61-brand` and precached the local Nursing Clinical Hub icons/favicons plus both offline bundles.
- Runtime API version is now **1.4.1**; Alembic revision remains **0005**.
- Added regression coverage for Portuguese leakage, offline bundle completeness, local manifest icons, service-worker precache, and executable offline SAE/policy fallback behavior.

## Pass 6.1.1 browser-offline hotfix

- Replaced the brittle service-worker-503 → frontend-second-fetch offline path with service-worker-generated API-compatible offline responses for SAE search and policy detail routes.
- Added `X-Clinical-Offline: 1` signaling so the frontend can render an explicit offline-source banner while preserving the online API as authoritative.
- Added direct Cache Storage lookup in frontend offline bundle loaders as a secondary fallback.
- Forced fresh service-worker precache fetches with `cache: 'reload'` and bumped the cache namespace to `clinical-reference-v6-pass611`.
- Versioned the manifest link as `/manifest.json?v=611` to invalidate stale browser manifest metadata, including the superseded Flaticon icon reference from Pass 6.
- Added `tests/service_worker_offline_qc.js` to exercise the service-worker-controlled offline path directly.
- Runtime API version bumped to 1.4.2; schema revision remains 0005.
