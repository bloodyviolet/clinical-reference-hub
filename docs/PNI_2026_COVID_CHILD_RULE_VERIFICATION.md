# PNI 2026 - COVID-19 healthy-child under-5 rule

Review date: 2026-09-11

## Scope

This Python rule covers only the healthy routine-child COVID-19
basic-series pathway from the exact 6-month birthday until the exact
fifth birthday.

Special-condition periodic pathways remain outside this rule.

## History dependency

The evaluator consumes only the qualified output of:

`normalize_covid_child_history(...)`

It does not reconstruct product chronology independently.

The historical sequence-validity table and the current
next-product table are intentionally separate.

A historically valid `CoronaVac -> CoronaVac` prefix does not authorize
another current CoronaVac dose.

## Current products

For a child with no documented COVID-19 history:

- Pfizer/Comirnaty pediatric under-5 is the current first option;
- Moderna/Spikevax is an authorized alternative when Pfizer is
  unavailable;
- CoronaVac is not a current initiation product.

## Continuation

Homologous completion is prioritized where the federal source supports
that preference.

Pure Pfizer history:

- Pfizer preferred;
- Moderna remains source-authorized.

Pure Moderna history:

- Moderna preferred;
- Pfizer remains source-authorized.

Mixed Pfizer/Moderna histories and legacy CoronaVac-derived histories
retain only source-supported product options. No deterministic
Pfizer-versus-Moderna preference is invented where the source does not
provide one.

## Product consequences

Product choice is not merely presentation metadata.

For a one-dose Moderna prefix:

- Moderna next produces `M-M`, a complete two-exposure basic series;
- Pfizer next produces `M-P`, an incomplete mixed prefix that requires
  a third exposure after at least 56 days.

Therefore the evaluator returns structured per-option consequences.

## Timing

For an incomplete authorized prefix:

- exposure 1 -> exposure 2: 28 elapsed days;
- exposure 2 -> exposure 3: 56 elapsed days.

Day 27 and day 55 remain not due.

No shorter exceptional interval is inferred.

## Age boundaries

The routine-child scope is `[DOB+6m, DOB+60m)`.

Before 6 months:

- no routine-child COVID dose is due.

At or after the exact fifth birthday:

- the under-5 core no longer recommends pending D2/D3;
- at least one supported documented under-5 exposure applies the
  federal age-out closure;
- zero documented under-5 exposure with complete history is outside
  this under-5 core.

If a 28-day or 56-day threshold would occur on or after the fifth
birthday, the age-out boundary wins. The rule does not schedule a
post-age-5 continuation.

## Healthy-child context gate

The caller must explicitly provide one of:

- `screened_none`;
- `screened_special_condition_present`;
- `not_screened`.

Absence of special-condition data is not interpreted as evidence that
the child belongs to the healthy-child pathway.

## Administration safety

When a dose is otherwise due:

- `screened_no_concern` allows `recommend_now`;
- `not_screened` returns `context_required`;
- `screened_concern` routes to `special_pathway_review`.

## Result type

The evaluator returns a `PniCovidChildRuleResult`, which extends the
existing `PniRuleResult` without changing the base model.

Structured product evidence includes:

- `allowed_next_product_keys`;
- `preferred_next_product_key`;
- `preferred_product_basis`;
- `product_choice_condition`;
- `next_product_options`;
- `age_out_closure_applied`.

Each next-product option preserves:

- current product key;
- option role;
- source condition, if any;
- resulting historical product sequence;
- resulting sequence state;
- subsequent minimum interval if the resulting sequence remains
  incomplete.

CoronaVac can appear in historical resulting sequences, but never as a
current next-product option.

## Complete healthy-child series

A source-authorized complete basic series produces no routine periodic
COVID-19 recommendation in this healthy-child rule.

Special periodic pathways are not inferred.

## Deferred

This rule does not implement:

- immunocompromised periodic vaccination;
- comorbidity periodic vaccination;
- indigenous, quilombola or riverine periodic pathways;
- pregnancy/postpartum;
- age 60 years and older;
- the age >=12 NT91 product transition;
- API/browser/UI support.

No synthetic vaccination score is produced.
