# Brazil 2026 PNI — maternal dTpa rule contract

Review date: 2026-09-11

## Scope

This contract precedes the maternal dTpa Python evaluator.

No dTpa recommendation function is introduced by BH8E3A.

## Pregnancy rule

The 2026 national PNI recommends:

- one dTpa dose in every pregnancy;
- beginning at the 20th gestational week;
- while considering prior vaccines containing diphtheria and tetanus
  toxoids.

The already locked BH8E2 cross-vaccine D/T normalizer is therefore the
history source for the future evaluator.

## Basic series

The national basic series contains at least three D/T-toxoid-containing
doses.

For a pregnant person with an incomplete series, dTpa can compose one of
those three doses.

The remaining series logic depends on the number of prior D/T-containing
exposures.

The future evaluator may classify the dTpa dose itself but must not
pretend that one dTpa recommendation alone completes an incomplete basic
series.

## Recommended versus exceptional interval

The standard recommended interval between D/T-toxoid-containing doses is
60 days.

Thirty days is an exceptional minimum.

The 30-day interval is not a second routine schedule option. The national
source says minimum intervals are exception tools used when protection
must be accelerated and recommends risk-benefit analysis by the
vaccination team.

Therefore the future engine may apply 30 days only when an explicit
exception authorization is supplied.

It must never infer that authorization from age, pregnancy or vaccine
history.

## Current-pregnancy dTpa

Automatically suppressing another dTpa dose requires evidence that:

1. a dTpa administration is documented;
2. it belongs to the same pregnancy episode; and
3. administration occurred at or after gestational week 20.

The reviewed 2026 source establishes administration from week 20 but does
not provide a general automatic repeat/no-repeat instruction for a dTpa
dose inadvertently administered before week 20.

Such a case must therefore route to `special_pathway_review`, rather than
having the software invent a revaccination rule.

If gestational age at the previous dTpa administration is unavailable,
the rule must return `context_required`.

## Postpartum

If dTpa was not administered during pregnancy, the 2026 PNI allows the
dose in the postpartum period through day 45.

Safe automation therefore requires an identifier for the pregnancy that
just ended, so that the application does not confuse a dTpa dose from an
older pregnancy with the immediately preceding pregnancy.

`postpartum_pregnancy_episode_key` provides that identity.

## Calendar recommendation versus administration safety

The future dTpa function is a calendar/schedule evaluator.

A result that a dose is calendar-due is not equivalent to a statement
that administration is clinically safe.

The 2026 source separately lists contraindications and precautions,
including clinically important prior reactions to pertussis-containing
or related vaccines.

BH8E3A therefore requires the future rule to receive an explicit
administration-safety screening state:

- `not_screened`;
- `screened_no_concern`;
- `screened_concern`.

Only `screened_no_concern` permits automatic progression to a
`recommend_now` schedule result.

`not_screened` must return `context_required`.

`screened_concern` must return `special_pathway_review`.

The schedule engine does not diagnose contraindications.

## Simultaneous vaccination

The source allows dTpa to be administered simultaneously with other
vaccines in the current national calendar.

The 60/30-day logic in this contract therefore concerns relevant
D/T-toxoid-containing history, not an invented spacing requirement
between dTpa and unrelated vaccines.
