# PNI 2026 — Varicella child-history model

## Purpose

This history layer normalizes general-child varicella-component evidence
before implementation of the VZ routine decision engine.

It does not decide whether vaccination is due today.

## Physical evidence

Two physical product sources can contribute a varicella component:

1. `varicella`
   - monovalent varicella vaccine;
   - supplied through `PniVaccineHistory(vaccine_key="varicella")`.

2. `mmrv_scrv`
   - tetraviral SCRV/MMRV;
   - supplied only through the already locked normalized MMR history;
   - remains one physical administration.

The VZ layer does not reparse raw MMR history and does not clone SCRV
events.

## Independent series validity

A physical SCRV administration can have consequences in both the MMR and
varicella families.

That does not make series validity interchangeable.

The VZ model derives its own component chronology and its own
three-calendar-month child interval. MMR `general_series_counted` and
`occupational_series_counted` flags are preserved only as provenance.

## Routine child age scope

Automatic ordinary VZ-component counting is limited to events:

- on or after exact 15 months; and
- before exact 7 years.

The timely schedule is D1 at 15 months and D2 at 4 years.

The history normalizer itself does not make the current due/not-due
decision.

## Three-calendar-month interval

For this general-child tranche, two counted VZ components must be
separated by at least three calendar months.

No fixed-day approximation is used.

Extra documented events are retained. A short-interval extra event does
not automatically erase a later chronologically valid two-event
subsequence.

## Pre-15 evidence

A varicella-containing administration before exact 15 months is retained
but blocks automatic ordinary-series interpretation.

This preserves the boundary with separate federal post-exposure rules,
including D0 and anticipated vaccination. The normalizer does not infer
contact, outbreak, D0, or anticipated-dose roles from age alone.

## Disease history

Prior varicella disease is not vaccination history.

The history normalizer therefore does not infer or classify disease
history. Disease-history context belongs to the future decision engine.

## Completeness and ambiguity

Automatic interpretation fails closed when:

- either relevant source history is partial, unknown, or contains undated
  evidence;
- monovalent product identity is unsupported;
- locked MMR history contains unsupported product evidence relevant to
  completeness;
- SCRV product/component provenance is internally inconsistent;
- more than one VZ-containing physical event occurs on the same date;
- pre-15 VZ-component evidence is present without an explicit pathway
  model.

## Boundaries

This history layer does not infer:

- prior disease status;
- outbreak or contact exposure;
- pregnancy;
- immunodepression or CRIE eligibility;
- current product substitution;
- a due/not-due recommendation;
- any synthetic vaccination score.
