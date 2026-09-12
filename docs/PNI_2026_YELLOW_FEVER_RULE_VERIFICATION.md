# PNI 2026 — Yellow-fever routine rule

Review date: 2026-09-12

## Scope

This rule covers the nonexceptional routine VFA pathway from the exact
9-month birthday until the exact 60-year birthday.

It consumes the qualified output of
`normalize_yellow_fever_history(...)`.

It does not implement the exceptional 6–8 month administration
decision, age-60-or-older risk-based vaccination, pregnancy/lactation,
immune/CRIE pathways, or travel/outbreak eligibility.

## Routine schedule

The routine schedule uses:

- first standard dose nominally at 9 months;
- child booster nominally at 4 years;
- at least 30 days between D0/standard or standard/standard doses where
  that internal VFA spacing rule applies.

A late D0 may delay the first standard routine dose beyond the exact
9-month birthday.

A delayed first standard dose may move the booster beyond the exact
4-year birthday.

## Age-5 crossover

Age 5 is not an age-out boundary.

For a person aged 5–59:

- no standard dose -> one standard dose;
- exactly one valid standard dose before age 5 -> one booster;
- two valid standard doses before age 5 -> complete;
- one standard dose at or after age 5 -> complete.

A booster obligation created by one pre-5 standard dose may cross the
fifth birthday.

## Fractional-2018 overlay

An unresolved fractional-2018 regularization requirement takes
precedence over an ordinary complete-state interpretation.

The required regularization product is a standard VFA dose.

No ordinary 30-day interval is invented between the 2018 fractional
event and the later standard regularization dose.

A source registration role `REF` remains provenance and does not turn
the regularization dose into a clinical booster.

## Routine-context gate

A VFA administration is never recommended from absence of information
about special conditions.

When VFA is otherwise due, the caller must explicitly provide:

- `screened_routine_no_special_condition`;
- `screened_special_condition_present`; or
- `not_screened`.

Special-condition presence routes out of this ordinary routine core.

## Live-vaccine interaction context

The routine engine uses the dedicated
`PniYellowFeverInteractionContext`.

The interaction context is consulted only after VFA is otherwise due.

Supported groups are:

- MMR / SCR;
- MMRV / SCRV;
- monovalent varicella;
- dengue.

### MMR/MMRV under age 2

Routine same-day VFA + MMR/MMRV is not recommended.

If they are not given simultaneously, use a 30-day interval.

A 15-day minimum is an explicitly authorized exception.

Same-day administration under age 2 is accepted only when explicit
concomitant epidemiologic-emergency context is present.

### Age 2 or older

VFA and the relevant attenuated live-vaccine groups may be given on the
same day.

If given on different days, use 30 days.

### Varicella

VFA and monovalent varicella may be administered on the same day at an
otherwise recommended age.

If separated, use 30 days; an explicitly authorized exceptional
15-day minimum may be used.

### Dengue

The current dengue/live-vaccine source supports same-day administration
or a 30-day/one-month interval.

This implementation does **not** extend the 15-day VFA exception to
dengue without a specific federal source authorizing that shorter
interval.

## Order of gates

The evaluator applies:

1. age scope;
2. qualified VFA history;
3. fractional regularization precedence;
4. ordinary VFA schedule/history state;
5. VFA internal timing;
6. routine/special-condition context;
7. live-vaccine interaction context;
8. administration-safety screen.

Cross-vaccine data never rewrites lifetime VFA history.

## Complete state

A complete ordinary VFA history produces no additional routine dose.

## Deferred

The rule does not infer:

- outbreak/circulation risk;
- traveler status;
- pregnancy or lactation eligibility;
- age >=60 eligibility;
- immune/CRIE eligibility.

No synthetic vaccination score is produced.
