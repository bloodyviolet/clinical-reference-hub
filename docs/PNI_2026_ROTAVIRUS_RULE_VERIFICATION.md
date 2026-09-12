# Brazil 2026 PNI — rotavirus routine rule verification

Review date: 2026-09-11

## Implemented scope

BH8E8A1 implements the routine two-dose rotavirus schedule.

The national 2026 calendar specifies:

- D1 routine age: 2 months;
- D1 permitted window: 1 month and 15 days through 11 months and 29 days;
- D2 routine age: 4 months;
- D2 permitted window: 3 months and 15 days through 23 months and 29 days;
- recommended interval: 60 days;
- exceptional minimum interval: 30 days.

The 30-day minimum is not treated as the routine interval.

It is used prospectively only when
`exceptional_minimum_interval_authorized=True`.

## Missed D1

If D1 was not administered within its permitted age window, the national
calendar states that the child loses the opportunity for D2.

BH8E8A1 therefore does not start the rotavirus series after the D1
maximum-age boundary.

## History

`unknown` and `partial_record` are never converted to documented zero
dose.

For one completely documented dose, that dose must be inside the
permitted D1 age window before the engine considers D2 eligibility.

For two documented doses:

- both age windows are checked;
- an interval below 30 days routes to review;
- an interval from 30 through 59 days routes to review because historical
  authorization for the exceptional minimum is not represented in the
  dose record;
- an interval of at least 60 days inside both age windows completes the
  routine series.

This avoids inventing a past exceptional circumstance.

## Product handling

The normalized 2026 rule matrix marks the rotavirus family as not
product-history-sensitive.

BH8E8A1 therefore evaluates the normalized `rotavirus` history without
inventing product-specific branching.

## Administration safety

The rule matrix does not identify rotavirus as a separate
special-condition recommendation layer.

Known contraindications and precautions belong to administration-safety
assessment rather than being inferred by the schedule engine.

Accordingly:

- `not_screened` -> `context_required`;
- `screened_concern` -> `special_pathway_review`;
- `screened_no_concern` permits schedule evaluation to recommend a dose.

The engine does not infer intussusception, immunodeficiency or other
contraindications from unrelated data.

## Repeat doses

BH8E8A1 does not contain an administration-event model for regurgitation,
spitting or vomiting and therefore does not invent an automatic repeat
dose from such events.

## PT-BR / EN-GB

Every result contains canonical PT-BR and complete EN-GB interpretations.

Clinical decisions remain language-neutral.
