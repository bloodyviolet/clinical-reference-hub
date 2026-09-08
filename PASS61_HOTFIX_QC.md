# Pass 6.1 UAT Hotfix — QC Record

## Scope

Pass 6.1 is a data/frontend/PWA hotfix produced after browser UAT of the successfully deployed Pass 6 release. It does not alter the production architecture, dependency lock, database schema, nginx strategy, systemd hardening model, or licensing profile.

- Runtime API: **1.4.1**
- Alembic head: **0005** (unchanged)
- SAE diagnoses: **277**
- contextual NANDA/NIC/NOC links: **627**
- public-health policy directives: **54** across **7** policy groups

## UAT defects addressed

### PT-BR SAE intervention contamination

Root cause: `scripts/rebuild_sae_mappings.py::local_activity_text()` accepted only the English diagnosis and reused it while constructing both English and Portuguese intervention text. The result was systematic English NANDA diagnosis leakage inside all 277 Portuguese intervention sentences.

Fix: the builder now accepts `desc_en` and `desc_pt` separately. `intervention_en` uses `desc_en`; `intervention_pt` uses `desc_pt`. The CSV and packaged SQLite database were regenerated.

Regression invariant:

- every `intervention_pt` contains its corresponding `description_pt`;
- no `intervention_pt` contains its corresponding full `description_en`;
- NANDA 00068 specifically renders `prontidão para um maior bem-estar espiritual`, not `readiness for enhanced spiritual well-being`.

### PWA icon blocked by CSP

Root cause: `manifest.json` referenced a Flaticon CDN image while production CSP intentionally permits `img-src 'self' data:` only.

Fix: replaced the external icon with packaged local 192x192 and 512x512 PNGs. No CSP relaxation was made.

### SAE and policies unavailable offline

Previous behavior: API requests were deliberately network-only; calculators/scales worked offline because they are client-side, but SAE search and policy data did not.

Fix:

- generated complete versioned static SAE and policy bundles from the packaged database;
- service worker precaches those bundles;
- frontend uses the API when available and falls back locally only for network failure / offline 503;
- normal online errors and rate-limit responses are not silently bypassed;
- offline mode is explicitly identified in the status badge and result panels.

Policy PDFs/external source links are not guaranteed offline unless the browser already cached them; the offline dataset itself is complete.

## Additional UI language clarification

Technical mapping provenance remains source-language English where no reviewed PT-BR equivalent exists. The UI now labels this material explicitly as `(EN)` and presents confidence/verification status labels in Portuguese so English technical provenance is not mistaken for accidental PT-BR contamination.

## Build/QC commands

```bash
python scripts/rebuild_sae_mappings.py
python seed_sae.py
python scripts/build_offline_data.py
python -m pytest -q
node tests/frontend_qc.js
node tests/offline_qc.js
```

`preflight.py` now additionally verifies local PWA icons, offline bundle presence, bundle/database revision/count agreement, and the NANDA 00068 Portuguese leakage regression sample.

## Deployment rule

Do not modify the deployed Pass 6 release tree in place. Install Pass 6.1 as a new immutable release, create a separate runtime database from its packaged `medical.db`, stage it on a new loopback port, verify it independently, and only then perform the same one-line reversible nginx upstream cutover used for Pass 6. Keep the current Pass 6 backend and the older pre-Pass-6 backend available until Pass 6.1 UAT is accepted.

## Nursing Clinical Hub brand icon

The Pass 6.1 PWA/favicon assets now use the user-selected **Nursing Clinical Hub** artwork as the canonical brand mark. The original supplied 1024x1024 PNG is preserved unchanged at `brand/nursing-clinical-hub-original.png` for reuse by the planned future app. A transparent 1024x1024 master containing only the rounded app mark is stored at `brand/nursing-clinical-hub-icon-master.png`; the original light presentation background outside the mark has been removed. Runtime PWA, Apple touch, PNG favicon, and multi-size ICO assets are deterministic resizes of that transparent master.

- supplied original SHA-256: `38a7b88a554ab34c4134fe2cb999931c7b1b2dcbfef1bf8107080309a8df140e`
- transparent icon master SHA-256: `92c2959ce96e7f46fb493517587ed4bb2d16a64086406183e35aad27bcfd9bf8`
- transparent master and PNG derivatives are RGBA with fully transparent corner pixels (alpha=0)
- no external icon/CDN dependency
- CSP remains unchanged (`img-src 'self' data:`)
- canonical browser favicon is `/favicon.ico`
- PWA icons remain same-origin under `/assets/icons/`

## Current artifact QC result

QC was rerun after integrating the final Nursing Clinical Hub brand assets.

- Python test suite: **36 passed**
- `frontend_qc.js`: **passed**
- `offline_qc.js`: **passed**
- production-mode preflight against the packaged database: **passed** (`revision=0005`, SAE=277, links=627, policies=54)
- local HTTP smoke: root, `/favicon.ico`, 512px icon, both offline bundles, readiness, and NANDA 00068 all returned successfully
- NANDA 00068 Portuguese intervention now contains `prontidão para um maior bem-estar espiritual` with no English diagnosis leakage
- requirements lock SHA-256 remains identical to Pass 6: `521664793fb9e08c497afb556dad4a13e5f282bd3013d32eeb523d46be47545f`
- migration tree/schema head remains unchanged at `0005`

The local QC container does not have the exact Pass 6 pinned runtime packages available offline, so dependency-lock enforcement was disabled only for the local preflight. Deployment must create a fresh Python 3.13 release venv from the unchanged `requirements.lock` and run `check_dependencies.py`/production preflight with lock enforcement enabled before any cutover.
