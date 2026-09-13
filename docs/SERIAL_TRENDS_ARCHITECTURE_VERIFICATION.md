# Serial trends — architecture and safety verification

Clinical review: 2026-09-13

## Disposition

Roadmap Item 11 does not create a new clinical scoring system.

It adds a representation layer for repeated observations produced by
already-qualified clinical tools.

The underlying clinical tool remains authoritative for every request,
calculation, component, interpretation, warning and Brazilian
applicability field.

The serial layer must not recalculate or reinterpret the observation.

## 1. Persistence boundary

The v2 serial-trend scope is deliberately ephemeral.

Observations exist only in JavaScript memory for the current page
runtime.

Item 11 does not create:

- a patient database;
- an encounter database;
- a longitudinal health record;
- SQLite clinical-observation tables;
- browser localStorage persistence;
- browser sessionStorage persistence;
- IndexedDB persistence;
- service-worker clinical-record persistence;
- a server-side serial-observation API.

Reloading or leaving the page may destroy the series.

This is intentional.

## 2. Identity and privacy boundary

Item 11 does not introduce patient, encounter or person identifiers.

The serial layer must not provide a free-text subject-identifier field
or a free-text clinical-note field.

An optional ephemeral runtime key may exist only for browser rendering.
It is not a clinical identifier, is never persisted and must not define
clinical chronology.

## 3. Observation envelope

Every serial observation must preserve:

1. the instrument identity;
2. an explicit clinical observation time;
3. browser capture metadata;
4. the complete request snapshot;
5. the complete canonical result snapshot;
6. whether execution came from the API or qualified offline fallback.

Request and result snapshots are deep copies.

They must not alias mutable current-form or last-result objects.

The trend layer must not reconstruct the original request from the
derived result.

## 4. Observation time

`observed_at` represents the clinical observation time.

For v2 it must be explicitly supplied and offset-aware.

The application must not silently invent a timezone.

Browser capture time is separate metadata and does not replace the
clinical observation time.

Entry order and capture order must not be presented as clinical
chronology.

If two observations carry the same clinical timestamp, the application
must not invent a clinical ordering between them.

## 5. Component preservation

The complete underlying request/result contract remains attached to each
observation.

This is especially important where the result contains clinically
meaningful components or contextual fields, including examples such as:

- NEWS2 component scores;
- GCS eye, verbal and motor responses;
- GCS-P pupil findings;
- FOUR domains;
- oxygenation input values and ratios;
- haemodynamic measurements and indices;
- metabolic input values and calculated outputs;
- renal criteria and categories;
- STEADI test measurements;
- growth measurements, indicators, warnings and provenance;
- Brazilian contextual/applicability fields.

The serial layer must not reduce such an observation to one scalar and
discard the components.

## 6. Instrument independence

One series represents one qualified instrument.

Different instruments are not merged into one trend score or one common
clinical axis.

In particular:

- GCS, GCS-P and FOUR remain separate;
- Caderneta falls and IVCF-20 remain separate;
- renal calculations are not collapsed into one synthetic renal score;
- STEADI instruments remain separate.

No cross-instrument weighted, averaged or synthetic score is permitted.

## 7. Incomplete observations

A clinically incomplete observation is still an observation.

Examples include:

- GCS with an `NT` component;
- GCS-P with unknown pupil reactivity;
- FOUR with an unavailable domain;
- any qualified tool returning a legitimate null or non-evaluable
  result.

Such records remain visible in the chronological table.

`NT`, null, unavailable or non-evaluable states are not converted to
zero and are not silently removed.

## 8. Visualisation boundary

A chronological table is required.

It is the primary complete representation because it can preserve
components, context and non-numeric observations.

Discrete numeric points may be visualised only for fields explicitly
qualified in an instrument/display-field registry.

The application must not discover arbitrary numeric response properties
and plot them automatically.

Item 11 does not create:

- interpolation;
- fitted curves;
- smoothing;
- regression;
- forecasting;
- automatic slope interpretation;
- automatic improvement/deterioration labels;
- new clinical thresholds;
- new prognostic interpretation.

Non-numeric observations remain visible even when no plot point exists.

## 9. Brazilian applicability

The serial layer does not create a new Brazilian numerical model.

It preserves the Brazilian/international authority and context already
qualified for the underlying tool.

Brazilian contextual rules must not be promoted to universal rules by
the trend representation.

Source freshness and applicability remain subject to the project-wide
v2.0.0 release recheck.

## 10. Implementation boundary

This architecture tranche creates no clinical arithmetic, schema, API,
browser, UI, PWA, database or migration implementation.

The next required qualification is an explicit instrument and
display-field registry.

That registry must identify which existing clinical tools participate
in serial trends and exactly which fields may be displayed or plotted.

No browser implementation should precede that registry qualification.

## Durable contract

The machine-readable Item 11 architecture and safety contract is:

`data/clinical-sources/serial_trends.json`
