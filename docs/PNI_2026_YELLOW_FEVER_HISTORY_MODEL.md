# PNI 2026 — Yellow-fever history model

Review date: 2026-09-11

## Purpose

This layer normalizes yellow-fever vaccination history for later use by
the routine PNI decision core.

It does not decide whether VFA is due.

## Generic lifetime history

The generic family history remains:

`PniVaccineHistory(vaccine_key="yellow_fever")`

Each dated record preserves an exact normalized dose-level product key.

No generic PNI history schema mutation is required.

## Dose-level product keys

The model recognizes:

- `yellow_fever_standard`;
- `yellow_fever_fractional_2018`.

A dose-level `product_key="yellow_fever"` is not sufficiently precise.

## Clinical role versus registration role

Clinical role is derived from product identity, age at administration
and chronology.

Optional `source_registration_role` is provenance only.

A source registration label such as `REF` must not independently define
a clinical booster.

This is critical for the 2026 fractional-dose regularization overlay:
the standard regularization dose may be registered as `REF`, while the
federal source does not characterize that dose clinically as a booster.

## Dose zero

A standard VFA administration from the exact 6-month birthday until the
day before the exact 9-month birthday is classified as an exceptional
dose zero.

D0:

- is preserved as a real historical administration;
- does not count as a routine standard-series dose;
- remains relevant to the 30-day VFA spacing rule.

A VFA event before the exact 6-month birthday makes automatic routine
interpretation unsafe.

## Standard doses

A standard VFA administration:

- from exact 9 months to before age 5 is a standard pre-5 series dose;
- from exact age 5 through the routine age range is a standard
  age-5-or-later dose.

The history model deliberately preserves the age at each dose because
age 5 changes the later decision semantics.

## Age-5 crossover

Age 5 is not an age-out boundary.

One standard dose before age 5 may still require a booster after the
fifth birthday.

Two valid standard doses before age 5 represent a complete standard
series.

One standard dose at or after age 5 is sufficient for the ordinary
age-5-to-59 history state.

The due-decision engine will apply those rules later.

## Fractional 2018 evidence

`yellow_fever_fractional_2018` represents the exceptional 2018
fractional strategy.

The normalizer requires this exact product key to carry a 2018
administration date.

Fractional evidence:

- does not count as a standard routine-series dose;
- does not count as D0;
- is retained separately.

If fractional history exists and there is no later standard VFA dose,
`fractional_regularization_required` is true.

The first later standard VFA event is marked as the event that resolves
that overlay.

A standard dose only before the latest fractional event does not resolve
the 2026 regularization requirement.

## Internal VFA intervals

The normalizer checks a 30-day minimum for:

- D0 -> subsequent standard dose;
- standard dose -> subsequent standard dose.

It does not invent an ordinary 30-day gate from the 2018 fractional
dose to its later standard regularization dose.

## Fail-closed behavior

Automatic routine interpretation is unsafe with:

- unknown or partial history;
- undated prior evidence;
- unsupported or missing product identity;
- generic dose-level `yellow_fever`;
- VFA evidence before exact 6 months;
- same-day duplicate/conflicting VFA evidence;
- applicable VFA intervals under 30 days;
- excessive standard-dose evidence;
- excessive D0 evidence;
- unreconciled registration-role metadata.

A fractional-2018 product outside calendar year 2018 is rejected as an
inconsistent source/product record.

## Cross-vaccine interactions

MMR/SCR, MMRV/SCRV, monovalent varicella and dengue interaction context
is intentionally not embedded in this lifetime history normalizer.

Those data belong to a separate live-vaccine administration context
consumed later by the VFA decision engine.

## Deferred

This history layer does not implement:

- VFA due/not-due decisions;
- the 6–8 month administration decision;
- age-60-or-older risk-based vaccination;
- pregnancy or lactation pathways;
- immune/CRIE pathways;
- travel/outbreak eligibility;
- live-vaccine coadministration decisions;
- API/browser/UI support.

No synthetic vaccination score is produced.

## Fractional regularization edge reconciliation

The 2026 fractional-dose overlay applies even when standard-dose
evidence predates the exceptional 2018 fractional administration.

Accordingly, the history model distinguishes routine-countable standard
doses before and after the latest fractional event.

A later event resolves the fractional overlay only when it is itself a
routine-countable standard dose. A standard-product administration that
is clinically classified as D0 does not resolve the fractional
regularization requirement.

The ordinary VFA series usually contains no more than two standard
doses. One explicit exception must nevertheless remain automatically
interpretable:

- two valid routine-countable standard doses occurred before the latest
  fractional-2018 event; and
- exactly one later routine-countable standard dose was administered to
  regularize that fractional history.

That produces three lifetime standard-dose events but is not treated as
excess evidence, because the third dose is source-required by the 2026
fractional regularization overlay.

Other histories containing more than two standard doses remain
fail-closed unless a future source/model tranche explicitly authorizes
their interpretation.
