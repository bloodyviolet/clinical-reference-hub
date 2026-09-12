# Brazil 2026 PNI — VIP child routine/transition rule verification

Review date: 2026-09-11

## Current routine authority

The current professional DPNI technical child calendar is the engine
authority for this tranche.

It specifies:

- D1 at 2 months;
- D2 at 4 months;
- D3 at 6 months;
- 60 days recommended between primary doses;
- 30 days minimum in exceptional situations;
- one VIP booster at 15 months;
- 9 calendar months recommended between D3 and the booster;
- 6 calendar months minimum between D3 and the booster;
- routine child scope through 4 years, 11 months and 29 days.

This implementation does not create a second routine VIP booster at
4 years.

## Normalized history input

The decision engine consumes the output of
`normalize_polio_history()`.

It does not attempt to reconstruct raw cross-product vaccination history.

Supported routine-safe IPV-equivalent products are preserved by the
normalizer. RIE hexavalent exposure remains visibly special-pathway and
routes this routine evaluator to review.

## Primary-series role assignment

The first three routine-safe chronological IPV-equivalent exposures are
primary-series candidates.

D1 before the routine starting age of 2 months is not automatically
validated.

Historical primary intervals:

- under 30 days -> review;
- 30–59 days -> review when historical exceptional authorization is
  not explicitly modeled;
- 60 days or more -> accepted for this rule.

For a prospective next primary dose, a 30–59-day interval may be used
only when `exceptional_minimum_interval_authorized=True`.

A historical VOPb booster is never converted into a missing primary VIP
dose.

## Current booster

After three valid primary exposures:

- booster age = at least 15 months;
- minimum D3→booster interval = 6 calendar months;
- recommended interval = 9 calendar months.

The evaluator uses calendar arithmetic, not fixed-day approximations.

A fourth IPV-equivalent exposure is classified as the booster only when
its age and D3 interval satisfy the booster contract.

## Legacy VOPb reconciliation

The exclusive-VIP schedule began on 4 November 2024.

If a child's 15-month birthday occurred before that date, absence of a
legacy-VOP history object is not interpreted as documented zero VOPb.

The transition states remain distinct:

- 3 valid primary IPV-equivalent doses + documented zero VOPb:
  evaluate the current single VIP booster;
- 3 valid primary doses + 1 historical VOPb booster:
  a VIP booster is still required, with a transition-specific minimum
  of 30 days after the VOPb booster;
- 3 valid primary doses + 2 historical VOPb boosters:
  the transition guidance considers the schedule complete.

A VOPb record before completion of the primary series is not silently
reclassified.

## Safety boundaries

This evaluator does not infer:

- CRIE eligibility;
- travel vaccination;
- outbreak/blocking conduct;
- a second current VIP booster.

Unknown, partial, unmapped, ambiguous, or unreconciled relevant history
fails closed.

## Localization

Every result contains PT-BR and EN-GB interpretations with one
language-neutral decision.

No synthetic vaccination score is produced.
