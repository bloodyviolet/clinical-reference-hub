# Brazil 2026 PNI — hepatitis A child routine rule verification

Review date: 2026-09-11

## Implemented scope

BH8E4A implements only the routine childhood hepatitis A layer.

The national 2026 agenda defines:

- one routine dose at 15 months;
- missed-opportunity vaccination as soon as possible;
- routine availability through 4 years, 11 months and 29 days.

The current Ministry hepatitis A guidance also states that the childhood
vaccine may be used from 12 months until before 5 years of age.

Accordingly, a documented childhood dose given from 12 months and before
the fifth birthday satisfies this one-dose routine evaluator.

## Dose before 12 months

The 2026 normative source lists age below 12 months as a
contraindication.

BH8E4A does not invent a repeat rule for a dose documented before
12 months.

Such a record returns `special_pathway_review`.

## History

During the routine due/catch-up window:

- documented valid dose -> `not_due_now`;
- documented zero-dose history -> continue to safety gate;
- unknown history -> `history_required`;
- partial history without a valid documented dose ->
  `history_required`.

Unknown history is never converted into documented zero-dose history.

## Fifth-birthday boundary

The routine childhood catch-up layer ends before the fifth birthday.

A child at or beyond the fifth birthday without a valid routine dose
returns `not_applicable` for this routine layer.

That result does not mean that every hepatitis A indication is absent.

Special-condition RIE/CRIE pathways are separate.

## RIE/CRIE boundary

Current Ministry guidance describes a separate two-dose hepatitis A
scheme, with a minimum six-month interval, for defined special
conditions.

That special-condition pathway is not implemented by BH8E4A and must
remain under the `special_condition` recommendation layer.

No special condition is inferred by this routine evaluator.

## Administration safety

Calendar eligibility is not equivalent to administration clearance.

A due routine dose requires an explicit safety-screen state:

- `not_screened` -> `context_required`;
- `screened_concern` -> `special_pathway_review`;
- `screened_no_concern` -> `recommend_now`.

The evaluator does not diagnose hypersensitivity or other clinical
contraindications.

## Simultaneous administration

The 2026 normative source states that hepatitis A may be administered
simultaneously with the other vaccines in the current national
calendar, without a required interval.

BH8E4A therefore does not invent a spacing interval.

## PT-BR / EN-GB

Every result contains both:

- canonical `interpretation_pt`;
- complete secondary `interpretation_en`.

The decision field remains language-neutral.
