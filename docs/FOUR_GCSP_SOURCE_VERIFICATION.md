# FOUR Score + GCS-P — source verification

Clinical review: 2026-09-12

## Disposition

Roadmap Item 10 consists of two independent neurologic assessment
models:

1. Glasgow Coma Scale with Pupil Reactivity Score (GCS-P);
2. Full Outline of UnResponsiveness (FOUR) Score.

They must not be combined into a synthetic neurologic score.

The numerical model remains authoritative in the Python clinical core.
The browser must not become a second independent source of scoring
truth.

## 1. Existing Glasgow browser surface

The repository already contains a legacy client-side Glasgow calculator.

It:

- records eye, verbal and motor components separately;
- supports `NT`;
- does not report a numeric total if any component is `NT`.

This existing surface is not yet the qualified Item 10 clinical core.

Item 10 must migrate scoring authority into Python rather than preserve
parallel browser-only arithmetic.

## 2. Glasgow untestable-component boundary

The Glasgow structured approach explicitly distinguishes a response that
cannot be tested from a true lowest response.

For Item 10:

- `NT` remains an explicit state;
- `NT` is not zero;
- `NT` is not one;
- individual available components remain visible;
- no numeric GCS total is emitted when any component is `NT`.

This protects intubation, local injury and other examination-interference
states from being silently converted into a falsely low score.

## 3. GCS-P numerical contract

The canonical GCS-P model is:

`GCS-P = numeric GCS total - Pupil Reactivity Score`

Pupil Reactivity Score:

- zero unreactive pupils: 0;
- one unreactive pupil: 1;
- two unreactive pupils: 2.

When calculable, GCS-P therefore ranges from 1 through 15.

A numeric GCS-P requires:

- a legitimately calculable numeric GCS total; and
- a known pupil-reactivity category.

Unknown or unassessable pupil status does not produce a numeric GCS-P.

The pupil examination remains separately visible and is not replaced by
the adjusted total.

The prognostic work underlying GCS-P is traumatic-brain-injury specific.
Item 10 does not import outcome-probability tables or extrapolate them to
unqualified populations.

## 4. Brazilian GCS-P context

Brazilian Ministry material uses the Glasgow examination with explicit
handling of responses that cannot legitimately be obtained and includes
pupillary-response subtraction.

This provides official Brazilian clinical context for the model.

It does not establish a separate Brazilian numerical GCS-P formula.

## 5. FOUR numerical contract

The canonical FOUR Score contains four independent domains:

- eye;
- motor;
- brainstem reflexes;
- respiration.

Each domain ranges from 0 through 4.

The numeric total therefore ranges from 0 through 16.

All four required domain findings must be available before a numeric
total is emitted.

FOUR is not mathematically derived from GCS and must remain independent
from GCS and GCS-P.

The respiratory domain explicitly represents intubation/ventilator
context.

Brainstem and respiratory findings remain visible rather than being
hidden behind the total.

## 6. Brazilian FOUR validation

A peer-reviewed Brazilian Portuguese translation, cultural adaptation
and validation was published in 2022.

The Brazilian study included 188 adults and retained the four domains
and 20 items from the original FOUR instrument.

This supports use of a Brazilian Portuguese rendering while preserving
the canonical 0–16 numerical model.

The validation does not justify creating a universal treatment or
mortality threshold in this application.

## 7. Safety boundaries

### NEURO-NT-01

Do not convert a non-testable GCS component to a numeric minimum.

### NEURO-GCSP-02

Do not calculate GCS-P unless the underlying GCS total and pupil
reactivity category are both legitimately calculable.

### NEURO-COMPONENTS-03

Retain the individual GCS, pupil and FOUR domain findings.

Do not present the total as a replacement for the neurologic
examination.

### NEURO-SYNTHETIC-04

Do not combine GCS, GCS-P and FOUR into a synthetic cross-instrument
score.

### NEURO-PROGNOSIS-05

Do not invent mortality, treatment or disposition cutoffs from a raw
FOUR or GCS-P value.

### NEURO-PEDIATRIC-06

Pediatric extensions are outside this adult Item 10 contract unless
separately source-qualified.

## 8. Implementation boundary

This source tranche does not create:

- a Python scoring implementation;
- schemas;
- API routes;
- browser changes;
- UI changes;
- PWA changes;
- database changes.

After this provenance tranche is persisted, the next implementation
layer is the canonical Python clinical core with deterministic reference
vectors and explicit invalid/incomplete states.

## Sources

Canonical and Brazilian source identities, DOI/PMID metadata, numerical
contracts and deterministic reference vectors are persisted in:

`data/clinical-sources/four_gcsp.json`

Source freshness and Brazilian applicability must be rechecked at the
v2.0.0 release freeze.
