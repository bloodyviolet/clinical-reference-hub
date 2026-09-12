# PNI 2026 — COVID-19 product-sensitive child history model

Review date: 2026-09-11

## Purpose

This layer normalizes product-sensitive COVID-19 vaccination history
for the healthy routine-child basic series.

It does not decide whether a dose is due.

## Generic lifetime history

The generic family history remains:

`PniVaccineHistory(vaccine_key="covid_19")`

Each dated `PniDoseRecord` must preserve the exact product family.

No generic schema mutation is required.

## Product keys

The normalization contract recognizes:

- `covid_pfizer_comirnaty_pediatric_under5`;
- `covid_moderna_spikevax`;
- `covid_coronavac_legacy`.

A dose-level `product_key="covid_19"` is insufficient because the
federal pediatric series is product sensitive.

## Product-local registration role

Federal interoperability examples demonstrate that manufacturer-local
registration labels do not always match the global clinical exposure
ordinal.

For example, a clinical sequence can contain:

1. Pfizer — source registration D1;
2. Moderna — source registration D1;
3. Moderna — source registration D2.

Therefore optional `source_registration_role` metadata is retained for
provenance only.

Clinical exposure ordinal is derived from dated chronology.

## Product sequences

The normalizer classifies the exact under-5 product sequence as:

- `documented_zero_exposure`;
- `source_authorized_incomplete_prefix`;
- `source_authorized_complete`;
- `unsupported_sequence`.

Only explicitly source-locked Pfizer, Moderna and legacy CoronaVac
paths are considered source-authorized.

No additional interchangeability is invented.

## Intervals

Historical clinical exposure intervals are validated as:

- exposure 1 -> 2: at least 28 elapsed days;
- exposure 2 -> 3: at least 56 elapsed days where a third exposure is
  present.

Manufacturer-local registration labels are never used to calculate
these intervals.

No shorter exceptional interval is inferred.

## Historical age

Every dated event is classified relative to the child's date of birth:

- before the exact 6-month birthday;
- age at least 6 months and younger than 5 years;
- on or after the exact fifth birthday.

Only events in `[6m,5y)` form the under-5 product sequence.

Events outside that range remain visible and are not silently folded
into the under-5 series.

## Fifth-birthday closure

Federal guidance resolves the age-out boundary.

The future decision engine will use `valid_under5_exposure_count`:

- at age 5 or older with at least one valid under-5 exposure, the
  under-5 scheme is closed;
- with zero valid under-5 exposures, the person is outside this
  under-5 core.

The history normalizer itself does not make that current-state
decision.

## Fail-closed behavior

Automatic under-5 series evaluation is unsafe when there is:

- unknown or partial product-sensitive history;
- undated prior-dose evidence;
- unsupported or missing product identity;
- a generic dose-level `covid_19` product key;
- same-day duplicate/conflicting events;
- unreconciled registration-role metadata;
- an unsupported product sequence;
- a historical 1->2 interval under 28 days;
- a historical 2->3 interval under 56 days;
- a COVID event before the exact 6-month birthday.

Later-age events are retained separately and do not become under-5
exposures.

## Deferred

This layer does not implement:

- the healthy-child due-decision engine;
- vaccine recommendation;
- immunocompromised periodic dosing;
- comorbidity periodic dosing;
- indigenous, quilombola or riverine periodic pathways;
- pregnancy/postpartum;
- age 60 years and older;
- age >=12 NT91 product-transition logic;
- API/browser/UI support.

No synthetic vaccination score is produced.
