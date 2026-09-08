# Pass 6.1.1 Browser Offline Hotfix — QC Record

Pass 6.1.1 follows browser UAT of Pass 6.1. Pass 6.1 correctly fixed the PT-BR clinical text and local branding, but real Chromium offline UAT showed that SAE search and SUS policies still surfaced service-worker 503 responses instead of remaining usable offline.

## Root cause

Pass 6.1 relied on a two-stage fallback: the service worker returned a synthetic 503 for API requests, then `app.js` attempted a second fetch of the static offline bundle. Unit tests covered the frontend fallback in isolation, but not the service-worker-controlled browser path. In real browser offline mode this arrangement proved brittle.

A separate stale-client observation also showed the old Flaticon manifest icon can remain visible in browser manifest/application metadata despite the deployed Pass 6.1 files containing no Flaticon URL.

## Fix

- API remains authoritative whenever network fetch succeeds.
- When genuinely offline, `sw.js` now synthesizes API-compatible responses directly from the precached complete SAE and policy bundles for:
  - `/api/v1/sae/search`
  - `/api/v1/policies/{policy}`
- Synthetic responses carry `X-Clinical-Offline: 1`; `app.js` uses that marker to show the offline source banner.
- `app.js` retains a secondary fallback and now prefers Cache Storage directly before attempting a network fetch for offline bundles.
- Service-worker precaching explicitly fetches shell resources with `cache: 'reload'` so a new worker cannot seed itself from an old HTTP cache.
- The manifest link is cache-busted as `/manifest.json?v=611` to force refresh of browser PWA manifest metadata.
- Service-worker cache namespace bumped to `clinical-reference-v6-pass611`.
- API runtime version bumped to **1.4.2**; Alembic revision remains **0005**.

## QC

- Python test suite: 36 passed.
- `frontend_qc.js`: passed.
- `offline_qc.js`: passed.
- `service_worker_offline_qc.js`: passed, including offline SAE search by NIC/NOC code, offline PNAB policy response, offline health 503 semantics, and cold offline navigation shell fallback.
- Database schema and content counts unchanged: revision 0005, SAE 277, NNN links 627, policies 54.
- Branding and PT-BR fixes from Pass 6.1 remain unchanged.

## Deployment

Do not modify the running Pass 6.1 release tree in place. Deploy Pass 6.1.1 as a new immutable release, stage it on a new loopback port, verify privately, then perform a one-line reversible nginx upstream cutover. Keep Pass 6.1 available for rollback until browser UAT passes.
