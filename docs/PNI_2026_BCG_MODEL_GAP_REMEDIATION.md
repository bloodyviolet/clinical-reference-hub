# Brazil 2026 PNI — BCG current-weight model-gap remediation

Review date: 2026-09-11

## Why another model field is required

The normalized PNI model already retained `birth_weight_grams`.

That is not sufficient for the 2026 BCG administration rule.

The national source states that a term or preterm newborn weighing below
2,000 g should have BCG deferred until the infant reaches 2,000 g.

This is a current-weight threshold, not a permanent classification based
on birth weight.

## Unsafe shortcut explicitly prohibited

The future BCG evaluator must never reason as follows:

- birth weight below 2,000 g -> still below 2,000 g now;
- birth weight at or above 2,000 g -> current weight threshold cleared.

Neither inference is valid without current assessment weight.

## Remediation

BH8E6A2 adds:

`PniAssessmentContext.current_weight_grams`

The value:

- uses grams;
- is optional when unknown;
- must be positive when supplied;
- is independent from `birth_weight_grams`;
- is never generated from age or a growth assumption;
- is never converted automatically from unrelated application fields.

## BCG evidence remains separate

Existing BCG vaccination evidence remains:

- vaccination record;
- vaccination scar;
- palpable nodule.

Unassessed evidence remains different from assessed-and-absent evidence.

Absence of scar alone must not trigger revaccination.

## Scope boundaries

This tranche does not implement BCG.

A future routine evaluator must keep separate:

- routine tuberculosis-protection vaccination;
- BCG immunoprophylaxis for contacts of people with hanseniasis;
- HIV exposure/infection pathways;
- primary or acquired immunodeficiency;
- immunosuppressive-treatment pathways;
- exceptional invalid-dose/revaccination situations.

No special condition may be inferred.
