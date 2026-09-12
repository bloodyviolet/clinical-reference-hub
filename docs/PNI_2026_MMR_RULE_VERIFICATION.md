# PNI 2026 — SCR/MMR routine rule

Review date: 2026-09-12

## Scope

This rule covers the ordinary SCR/MMR routine from the exact 12-month
birthday through age 59 and the health-worker overlay where the source
allows automatic interpretation.

It consumes the qualified output of `normalize_mmr_history(...)`.

It does not implement D0 administration eligibility, outbreak/blocking
selection, age-60-or-older risk-benefit decisions, manufacturer/APLV
selection, severe immunodeficiency/CRIE eligibility, or varicella-family
completion.

## General-population targets

From exact 12 months until the exact 30th birthday, the completion
target is two valid SCR/MMR-component doses.

From the exact 30th birthday until the exact 60th birthday, the ordinary
general-population target is one valid component dose.

Age 30 is therefore a requirement crossover, not an age-out event.

## Child timing

The timely schedule is:

- D1 at 12 months;
- D2 at 15 months.

A prior D0 does not count as D1 and may postpone the first routine dose
until at least 30 days after the D0.

A delayed D1 may postpone D2.

The ordinary interval is 30 days.

For the general-population 12m–29y series, the 2026 source permits a
15-day minimum exceptionally when that acceleration is explicitly
authorized.

The evaluator never infers that authorization.

## Health-worker overlay

Health workers require two occupational-valid SCR/MMR-component doses.

The minimum interval is 30 days.

A general-population 15–29 day exception does not satisfy the
health-worker minimum.

Occupation is requested only when it can change the decision.

Examples:

- zero doses at age 30–59: at least one dose is required regardless of
  occupation, so occupation need not block the first-dose decision;
- one valid dose at age 30–59: occupation changes whether the series is
  complete, so occupation must be known;
- two occupational-valid doses: completion is known regardless of
  occupation.

At age 60 or older, an incomplete health-worker schedule requires
service-level risk-benefit assessment and is outside this ordinary
routine core.

## Pregnancy

SCR/MMR is a live attenuated vaccine and is contraindicated during
pregnancy.

Pregnancy status is requested only when a dose is otherwise due.

No pregnancy status is inferred from age, sex, gender or missing data.

Inadvertent vaccination during pregnancy is not modeled as an
indication for pregnancy termination.

## Special conditions

When a dose is otherwise due, the caller must explicitly report whether
a special live-vaccine condition is present.

A special condition routes out of this ordinary routine core.

Severe immunodeficiency and CRIE eligibility remain deferred.

## External live-vaccine interaction context

The rule uses the dedicated `PniMmrInteractionContext`.

This context is consulted only when an SCR/MMR dose is otherwise due.

### Yellow fever

Under age 2, routine same-day administration with yellow fever is not
automatically recommended.

Explicit concomitant epidemiologic emergency may permit same-day
administration.

If administered on different days, the routine interval is 30 days;
an explicitly authorized 15-day exceptional minimum may apply.

From age 2 onward, same-day administration is allowed.

### Varicella

Same-day SCR/MMR and monovalent varicella administration is allowed.

When separated, use 30 days; an explicitly authorized 15-day exception
may apply.

### Dengue

From age 2, the supported framework is same-day administration or a
30-day interval.

The 15-day SCR/other-live-vaccine exception is not extended to dengue
without an explicit federal source.

Under age 2, dengue interaction is routed out rather than inferred.

## Decision order

The evaluator applies:

1. normalized history integrity;
2. age scope;
3. general versus occupational target;
4. child schedule / internal SCR timing;
5. occupation only when decision-relevant;
6. pregnancy only when administration is otherwise due;
7. special-condition screen only when administration is otherwise due;
8. external live-vaccine interaction only when administration is
   otherwise due;
9. administration-safety screen;
10. bilingual interpretation with language-neutral decision fields.

## Boundary

The rule does not infer:

- occupation;
- pregnancy;
- immunodeficiency;
- outbreak/blocking eligibility;
- epidemiologic emergency;
- exceptional 15-day authorization;
- MMR versus MMRV product selection.

No synthetic vaccination score is produced.
