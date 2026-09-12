# PNI 2026 — Varicella general-child routine rule verification

## Scope

Python-only general-population childhood varicella evaluator.

The evaluator consumes only the locked normalized VZ history model
`PNI26-VARICELLA-CHILD-HISTORY-001`.

It does not reparse raw monovalent or MMR/SCRV history.

## Timely schedule

The timely routine schedule is:

- D1 at exact 15 months;
- D2 at exact 4 years.

A timely D1 at exact 15 months preserves the age-4 D2 agenda.

## Catch-up schedule

The federal 2026 instruction separately directs children who missed
vaccination at the recommended age to have vaccination status updated as
soon as possible through 6 years, 11 months and 29 days, according to
vaccination history and respecting the interval between doses.

For children 1–12 years, the varicella interval is three calendar months.

Therefore a genuinely delayed D1 does not automatically wait until age
4 for D2. D2 becomes eligible after three calendar months, provided the
general-child opportunity remains open before exact age 7.

No fixed-day approximation is used.

## Age-7 closure

The three-calendar-month interval is never compressed to force a second
dose before age 7.

This routine core does not synthesize age-7-plus rescue.

## Disease-history context

Disease history is explicit evaluator context.

- no prior varicella: ordinary logic may continue;
- prior disease uncertain: ordinary logic may continue;
- confirmed prior disease: general-population routine vaccination is not
  indicated by this layer;
- unscreened disease history: requested only when vaccination would
  otherwise be due.

Disease status is never inferred from vaccine history.

## Pregnancy, special conditions, and safety

These gates are consulted only when a dose would otherwise be due.

Pregnancy or a relevant special condition routes to clinical/special
pathway review rather than automatic administration.

## Live-vaccine interaction

The dedicated VZ model contains only:

- MMR;
- yellow fever.

Same-day administration is permitted.

If administered on different days, ordinary spacing is 30 days.

An explicitly authorized exceptional minimum of 15 days may be used.

The special under-2 MMR/yellow-fever simultaneous-administration rule is
not inherited by monovalent VZ.

## Product

The ordinary product recommendation is monovalent varicella.

SCRV/MMRV is a source-authorized alternative when monovalent varicella
is unavailable. Product availability does not determine whether the
dose itself is due.

## Deferred pathways

The evaluator does not automate:

- outbreak/contact/post-exposure vaccination;
- D0;
- anticipated pre-15-month vaccination;
- occupational varicella schedules;
- Indigenous rescue schedules;
- age-7-plus general rescue;
- age-60-plus risk-benefit decisions;
- CRIE-specific schedules.

## Localization and safety

PT-BR is primary and EN-GB is complete secondary output.

Decision logic is language-neutral.

No special condition, disease history, pregnancy status, or
epidemiologic context is inferred.

No synthetic vaccination score is produced.
