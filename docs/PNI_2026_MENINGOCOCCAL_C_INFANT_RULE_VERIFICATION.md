# Brazil 2026 PNI — meningococcal C infant rule verification

Review date: 2026-09-11

## Implemented scope

BH8E9A1 implements only the meningococcal-C infant primary and catch-up
layer before 12 months.

The routine primary agenda is:

- D1 at 3 months;
- D2 at 5 months;
- recommended interval 60 days;
- exceptional minimum 30 days.

Use of the 30-day minimum prospectively requires explicit authorization.

## Catch-up

For children aged 6 through 10 months with incomplete primary MenC:

- one documented dose -> one additional MenC dose;
- no documented doses -> two-dose MenC catch-up.

For children aged 11 months with incomplete MenC:

- one documented dose -> one additional MenC dose when interval permits;
- no documented doses -> one MenC dose.

The evaluator therefore changes behavior at the 11-month boundary.

## MenACWY transition

The 12-month booster is preferentially MenACWY.

That is a separate normalized vaccine key and a separate rule family.

BH8E9A1 stops before the first birthday and does not consume MenACWY
history or implement its booster/catch-up logic.

At or after 12 months the MenC infant evaluator returns `not_applicable`
and explicitly hands the decision to the future MenACWY layer.

This controlled split means no cross-key history normalizer is required
for BH8E9A1.

## Historical intervals

Two documented MenC doses are treated as:

- interval <30 days -> review;
- interval 30–59 days -> review because historical exceptional
  authorization is not represented in the dose record;
- interval >=60 days -> infant MenC primary series complete.

This does not invent past exceptional circumstances.

## History uncertainty

`unknown`, `partial_record`, missing dates, and missing history are not
converted into documented zero doses.

A MenC dose documented before 3 months is routed for review.

## Safety and special-condition boundary

The 2026 normalized matrix does not mark the ordinary MenC family as a
special-condition-sensitive routine layer.

The calendar engine therefore does not infer CRIE indications or
contraindications.

Administration safety remains a separate gate:

- not screened -> `context_required`;
- screened concern -> `special_pathway_review`.

## PT-BR / EN-GB

Every result contains PT-BR and EN-GB interpretations with one shared
language-neutral clinical decision.
