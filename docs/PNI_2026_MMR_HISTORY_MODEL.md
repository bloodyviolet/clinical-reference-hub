# PNI 2026 — SCR/MMR history model

Review date: 2026-09-12

## Purpose

This layer normalizes SCR/MMR vaccination history for later use by the
routine PNI decision core.

It does not decide whether an SCR/MMR dose is currently due.

## Canonical history

The family history uses:

`PniVaccineHistory(vaccine_key="mmr")`

Supported dose-level products are:

- `mmr_scr`;
- `mmrv_scrv`.

A generic dose-level `product_key="mmr"` is insufficient.

Legacy MR/SR and other incomplete or unknown combinations are not
silently treated as equivalent to current SCR/MMR.

## Product components

`mmr_scr` contains measles, mumps and rubella.

`mmrv_scrv` contains measles, mumps, rubella and varicella.

A physical SCRV/MMRV administration remains one historical event.
The SCR normalizer derives its MMR-component consequence while retaining
the varicella component for future VZ-family work.

The event is never duplicated into artificial MMR and varicella
administrations.

## Dose zero

A documented `mmr_scr` administration from the exact 6-month birthday
until the day before the exact 12-month birthday is classified as
`dose_zero_history`.

D0:

- is preserved chronologically;
- does not count toward routine SCR completion;
- is relevant to the minimum interval before the first routine dose.

The first routine dose cannot be counted safely until at least 30 days
after the latest D0 and not before the exact 12-month birthday.

This history classification does not reconstruct whether the D0 was
authorized under the manufacturer-specific or epidemiologic rules in
force when it was administered.

`mmrv_scrv` before exact 12 months is not silently accepted as D0.

## Routine component doses

Supported MMR-containing doses from exact 12 months onward are preserved
as routine component events.

Age at administration remains available because exact age 30 changes
the general-population completion target and exact age 60 ends the first
ordinary routine engine scope.

## General versus occupational series validity

The model deliberately derives two counts:

- `general_valid_component_dose_count`;
- `occupational_valid_component_dose_count`.

The ordinary interval is 30 days.

For the general-population series, a 15–29 day interval may count only
when an exact historical source-authorization record is supplied.

For the health-worker series, the minimum remains 30 days. The same
15–29 day interval therefore does not count as a second occupational
dose even when it is source-authorized for the general series.

This distinction prevents accelerated general-population history from
being misclassified as a completed health-worker series.

## Historical short-interval authorization

The optional `historical_interval_exception_events` input identifies an
exact dated pair and uses the language-neutral authorization key:

`source_authorized_general_15_day_exception`

The authorization:

- never applies to D0 -> routine D1 spacing;
- never lowers the health-worker 30-day minimum;
- must reconcile to two dated routine-component events;
- is never inferred by the normalizer.

## Extra documented doses

More than two documented MMR-containing administrations is not, by
itself, an unsafe history state.

All dated events are retained.

General and occupational counts are derived from their respective
interval rules instead of applying a blanket maximum-dose rejection.

## Source registration role

Optional source registration labels are provenance only.

They do not determine:

- D0 versus routine role;
- series ordinal;
- general-series validity;
- occupational-series validity.

Clinical role derives from exact product, age, chronology and interval
evidence.

## Fail-closed behavior

Automatic routine interpretation is unsafe when there is:

- an event before the date of birth or in the future;
- measles-containing evidence before exact 6 months;
- missing, generic or unsupported product identity;
- `mmrv_scrv` before exact 12 months;
- unknown, partial or undated history;
- same-day duplicate/conflicting MMR-containing events;
- unreconciled registration metadata;
- duplicate, reversed or unreconciled interval-exception metadata;
- a routine-component interval under 15 days;
- a 15–29 day routine-component interval without exact source
  authorization;
- a D0-to-first-routine interval under 30 days.

A source-authorized 15–29 day general interval remains an interpretable
history: it may count for the general series while remaining
non-counting for the health-worker series.

## Boundary

The normalizer does not infer:

- occupation;
- pregnancy;
- immune or CRIE eligibility;
- epidemiologic emergency;
- outbreak/travel eligibility;
- current administration safety;
- current due/not-due state.

No synthetic vaccination score is produced.

External interactions with yellow fever, varicella and dengue belong to
a later dedicated SCR administration context, not this lifetime-history
normalizer.
