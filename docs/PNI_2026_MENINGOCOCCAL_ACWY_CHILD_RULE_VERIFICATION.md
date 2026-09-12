# Brazil 2026 PNI — MenACWY child booster/catch-up verification

Review date: 2026-09-11

## Scope

BH8E10A1 implements only the routine MenACWY child layer from
12 months through 4 years, 11 months and 29 days.

The adolescent 11–14-year MenACWY recommendation remains separate.

## Two explicit histories

The evaluator receives separate normalized histories for:

- `meningococcal_c`;
- `meningococcal_acwy`.

No generalized cross-vaccine normalizer is introduced.

This is intentional because the 2026 child update rule recommends one
MenACWY dose whether the prior MenC basic series is complete, incomplete
or absent.

MenC history is therefore consumed only where it materially affects:

- the 60-day handoff from a recent MenC dose;
- recognition of the explicitly accepted legacy state consisting of a
  complete MenC basic series plus a MenC booster.

## Child update

From 12 months through 4 years, 11 months and 29 days:

- complete two-dose MenC basic series without booster -> one MenACWY;
- incomplete one-dose MenC basic series -> one MenACWY;
- no prior documented basic series -> one MenACWY.

A valid documented MenACWY dose within this child age layer suppresses
a duplicate routine child dose.

## Legacy MenC booster

The 2026 instruction explicitly states that a child with a complete
two-dose MenC basic series plus a MenC booster is considered vaccinated.

Automatic suppression is deliberately conservative: exact dates must
show two pre-12-month basic doses plus one MenC booster at/after
12 months, with routine-verifiable 60-day intervals.

Ambiguous legacy histories route to review rather than being silently
classified as complete.

## Recent MenC dose

When MenC history is otherwise documented and the most recent MenC dose
occurred fewer than 60 days before assessment, MenACWY is not yet due.

No exceptional interval shorter than 60 days is invented for this
handoff.

The evaluator does not re-score whether an older MenC series was
complete when that classification is irrelevant to the MenACWY
catch-up recommendation.

## Uncertain histories

A valid documented child MenACWY dose is enough to prevent a duplicate
routine dose even if MenC history is uncertain.

Otherwise, uncertain/partial MenACWY history requires reconciliation.

Uncertain/partial MenC history also requires reconciliation because a
recent MenC dose or an already completed MenC booster cannot safely be
excluded.

## Pregnancy boundary

The global MenACWY family is pregnancy-sensitive because other age
layers exist.

This child evaluator is strictly below 5 years of age and therefore
does not consume pregnancy status or extrapolate adolescent/pregnancy
logic.

## Safety

Calendar eligibility remains separate from administration safety:

- `not_screened` -> `context_required`;
- `screened_concern` -> `special_pathway_review`.

## Localization

Every result carries complete PT-BR and EN-GB interpretations with one
language-neutral clinical decision.
