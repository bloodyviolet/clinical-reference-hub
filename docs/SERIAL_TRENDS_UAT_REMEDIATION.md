# Serial Trends — Phase 7 UAT persistence/export remediation

Review date: 2026-09-13

## Status

This document records a Phase 7 human-UAT remediation to the already
qualified Item 11 browser implementation.

It does not create a new score, threshold, prognosis or clinical
interpretation.

## Superseded persistence boundary

The original Item 11 architecture deliberately used current-page memory
only. Human UAT identified accidental-refresh data loss as
release-blocking.

For the v2 release candidate, the browser runtime therefore uses
`sessionStorage` only.

The following remain prohibited:

- server-side serial-observation persistence;
- SQLite serial-observation storage;
- `localStorage`;
- IndexedDB;
- service-worker clinical-record storage;
- patient/person/encounter identifiers;
- free-text patient identifiers;
- free-text clinical notes.

The session payload may survive reload within the same browser tab/session.
Closing the tab or browser session may destroy it.

Clear-series actions also clear or rewrite the corresponding
session-scoped payload.

## Restore semantics

A restored observation preserves:

- instrument identity;
- explicit offset-aware `observed_at`;
- original `captured_at`;
- complete request snapshot;
- complete canonical result snapshot;
- execution source.

Runtime keys remain non-clinical and are regenerated after restoration.

No clinical ordering is inferred from runtime keys or capture order.

## Export

Human UAT also requires client-side completed-session export.

The v2 candidate provides:

- PDF export;
- DOCX export.

Both files are generated locally in the browser.

No export payload is posted to the application server.

Exports preserve chronological observations, instrument identity,
observation/capture times, execution source, summary/component/context
fields and complete qualified request/result snapshots.

The existing prohibition on interpolation, smoothing, regression,
forecasting and automatic improvement/deterioration interpretation
remains unchanged.

## Historical artifacts

`data/clinical-sources/serial_trends.json` and
`docs/SERIAL_TRENDS_ARCHITECTURE_VERIFICATION.md` record the earlier
architecture tranche and are retained as historical qualification
artifacts.

The current browser runtime persistence contract is represented by
`data/clinical-sources/serial_trends_runtime_contract.json`, as amended
by this Phase 7 remediation.
