# Brazil 2026 PNI — maternal dTpa Python rule verification

Review date: 2026-09-11

## Implemented scope

BH8E3B implements only the maternal routine dTpa branch:

- pregnancy from gestational week 20;
- one maternal dTpa dose for each pregnancy;
- postpartum through day 45 when the pregnancy dose was missed;
- cross-vaccine D/T-toxoid history;
- 60-day recommended interval;
- explicitly authorised 30-day exceptional minimum;
- basic-series context;
- administration-safety gating.

Occupational dTpa rules for healthcare workers, traditional midwives and
eligible healthcare students remain outside this implementation.

The dTpa vaccine family must therefore remain marked as partially
implemented.

## PT-BR / EN-GB localisation contract

Every maternal dTpa result contains:

- `interpretation_pt` — canonical PT-BR clinical interpretation;
- `interpretation_en` — complete EN-GB informational interpretation.

The clinical decision itself is language-neutral and shared by both
interpretations.

No rule branch may return only one language.

This requirement applies equally to:

- recommend-now results;
- not-due results;
- future recommendations;
- history-required results;
- context-required results;
- special-pathway-review results;
- not-applicable results.

## Pregnancy repeat suppression

A documented dTpa associated with the current pregnancy automatically
suppresses another maternal dose only when the record establishes
administration at or after gestational week 20.

If gestational timing is unavailable, the evaluator returns
`context_required`.

If the documented current-pregnancy dose occurred before week 20, the
evaluator returns `special_pathway_review`; it does not invent a repeat
rule.

## Postpartum

The postpartum maternal branch applies through day 45.

A dTpa administered after the current delivery suppresses another
postpartum maternal dose.

A qualifying dTpa from the pregnancy that just ended also suppresses the
postpartum missed-dose indication.

If a calculated D/T interval cannot fit within the remaining 45-day
maternal postpartum window, the evaluator fails closed to
`special_pathway_review`.

## D/T intervals

Sixty days is the standard recommended interval.

Thirty days is an exceptional minimum and can affect the calculation
only when the caller supplies explicit authorisation following the
required risk-benefit assessment.

The software never infers this authorisation.

## Administration safety

Calendar eligibility is not administration clearance.

If a dose is calendar-due:

- `not_screened` -> `context_required`;
- `screened_concern` -> `special_pathway_review`;
- `screened_no_concern` -> schedule logic may return `recommend_now`.

The evaluator does not diagnose vaccine contraindications.

## Basic-series context

A maternal dTpa dose may form part of an incomplete three-dose
D/T-containing basic series.

The interpretation explains remaining series context but does not
pretend that dTpa alone completes a series when additional dT doses are
still required.
