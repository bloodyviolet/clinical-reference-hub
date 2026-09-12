# Brazil 2026 PNI — normalized data model

Baseline checkpoint: `433f89d04cc23ead88f1fd71bf35f13f97a73b4f`

Model stage: locked before vaccine-specific rule implementation.

## Purpose

The Item-8 engine cannot safely operate as an age-only vaccine lookup.

The normalized model must preserve enough information for later
vaccine-specific rules to distinguish:

- documented history from unknown history;
- exact dated doses from reported prior doses without exact dates;
- vaccine/product transitions;
- assessment date and rule effective date;
- routine recommendations from seasonal, rescue, outbreak/blocking and
  special-condition pathways;
- recommended intervals from exceptional minimum intervals;
- explicit clinical, pregnancy, occupational and epidemiological
  context.

This tranche defines representation only. It does not decide whether any
specific vaccine is due.

## Assessment context

`PniAssessmentContext` contains:

- assessment date;
- date of birth;
- pregnancy status;
- optional gestational age;
- optional postpartum context;
- explicit occupational groups;
- explicit special-condition codes;
- explicit epidemiologic context codes;
- optional state and municipality.

Assessment date cannot precede date of birth.

Gestational age may only be supplied when pregnancy status is explicitly
`pregnant`.

Pregnancy and postpartum context cannot coexist.

## Vaccination history states

Each vaccine history uses one of four explicit states.

### `documented_zero_dose`

There is positive documentation that no prior dose is recorded.

It is not the same as unknown history.

No dose record may coexist with this state.

### `documented_doses`

At least one exact dated dose is available.

The state does not claim that the series is complete or current; that
judgment belongs to vaccine-specific rules.

### `partial_record`

Some history exists, but the available record is incomplete.

It may include exact dated doses and/or a count of reported prior doses
whose exact dates are unavailable.

### `unknown`

No usable prior-dose information is available.

Unknown must never be silently converted into documented zero-dose
history.

## Dose record

An exact dose record preserves:

- administration date;
- product key when known;
- product name when known;
- dose number/label when known;
- documentation source.

The product fields are intentionally retained because the 2026
pneumococcal transition demonstrates that vaccine product history can be
clinically relevant.

## Requested recommendation layers

The request explicitly identifies which recommendation layers are being
evaluated:

- `routine`;
- `seasonal_strategy`;
- `rescue_strategy`;
- `outbreak_or_blocking`;
- `special_condition`.

The default request is routine only.

Layers must never be silently merged.

## Rule provenance

Every future vaccine-specific result must identify:

- rule ID;
- authority;
- authority precedence rank;
- source title;
- source URL;
- source snapshot date;
- effective-from date when available;
- effective-until date when available.

This makes midyear changes auditable.

## Rule-result decisions

The normalized result supports:

- `recommend_now`;
- `not_due_now`;
- `future_recommendation`;
- `history_required`;
- `context_required`;
- `special_pathway_review`;
- `not_applicable`.

`future_recommendation` requires an explicit future date.

`history_required` must explicitly set the history-required flag.

`context_required` must identify the missing context.

## Interval model

Recommended and minimum intervals have separate fields.

If an exceptional minimum interval is applied, the result must explicitly
say so.

A minimum interval cannot exceed the recommended interval in the
normalized contract.

## Safety/governance flags

Every aggregate PNI response carries:

- `routine_strategy_layers_merged = false`;
- `special_condition_inference_applied = false`;
- `synthetic_score_applied = false`.

A special clinical condition is an explicit input. It is not inferred
from an unrelated result.

No numerical vaccination-completeness score is created.

## Implementation boundary

This model intentionally contains no individual vaccine schedule rules.

The next rule tranche must consume these contracts rather than inventing
parallel ad-hoc input formats.

## BH8D model-gap remediation

The authoritative 21-vaccine rule-family extraction identified additional
context that must be represented before vaccine-specific automation.

### Pregnancy episode identity

`pregnancy_episode_key` is an application-local, non-clinical identifier
that can be carried both on the current assessment and on historical dose
records.

Its purpose is narrow: it allows later rules to determine whether a dose
documented as being administered during pregnancy belongs to the current
pregnancy episode.

It is not itself a clinical criterion.

### Maternal HBsAg status

`maternal_hbsag_status` preserves:

- positive;
- negative;
- unknown/unavailable.

Unknown/unavailable must never be converted to negative.

### Birth weight

`birth_weight_grams` is retained as structured historical neonatal
context.

No arbitrary upper age or weight range is introduced by this model.

### BCG evidence

BCG evidence can separately preserve whether the following were actually
assessed:

- vaccination record;
- vaccination scar;
- palpable nodule.

`None` means not assessed/unknown. `False` means assessed and absent.

The evidence object cannot be completely empty.

### Breastfeeding

Breastfeeding is represented independently from pregnancy.

When relevant, the date of birth of the youngest breastfed child can be
preserved so future rules can evaluate source-defined infant-age
boundaries without guessing.

### Disease history

Disease events preserve:

- disease key;
- event date when known;
- documented versus patient/caregiver-reported evidence.

A missing event date remains missing; it is not fabricated.

### Exposure history

Exposure events preserve:

- exposure key;
- event date;
- documented versus reported evidence.

Future-dated exposure events are rejected.

### Travel

Travel context preserves:

- destination country;
- destination state when applicable;
- destination municipality when applicable;
- departure date;
- return date when known.

The schema does not infer that a destination is an official risk area.
That requires an authoritative geographic/epidemiologic rule source.

### Travel / area-risk recommendation layer

`travel_or_area_risk` is now a distinct recommendation layer.

It must not be silently merged with routine, outbreak, campaign or
special-condition results.

## Remaining automation boundary

The normalized schema now represents every gap identified by BH8C.

This does not mean every branch should be automatically classified.

High-context branches may still return `context_required` or
`special_pathway_review` when an authoritative rule cannot be safely
resolved from the supplied inputs.

## BH8E2 cross-vaccine D/T toxoid history

Maternal dTpa requires history across vaccine products rather than one
vaccine key.

The normalized contract therefore includes:

- `PniAntigenExposureRecord`;
- `PniAntigenHistorySummary`;
- explicit D/T/pertussis component labels;
- explicit cross-vaccine history scope;
- same-day ambiguity detection;
- unmapped-product detection;
- separate safety flags for interval evaluation and basic-series count.

A `complete` history scope is an explicit assertion by the caller or
trusted reconciliation process. It is never inferred from the mere
presence of records.

The normalizer does not determine whether dTpa is due and does not apply
the source-defined 60-day recommended or 30-day exceptional minimum
interval.

## BH8E3A maternal dTpa implementation prerequisites

Granular source verification for maternal dTpa requires two additional
pieces of provenance.

### Gestational age at administration

`PniDoseRecord.gestational_age_weeks_at_administration` preserves the
gestational week at which a pregnancy-associated dose was administered,
when that fact is documented.

The field is optional because historical records may not contain this
information.

The D/T antigen-history normalizer carries this value into
`PniAntigenExposureRecord`.

No gestational age is reconstructed from calendar dates when the source
record does not provide it.

### Postpartum pregnancy identity

`PniAssessmentContext.postpartum_pregnancy_episode_key` identifies the
pregnancy that immediately preceded a postpartum assessment.

It requires a postpartum-day context and cannot coexist with an active
pregnancy context.

This allows a future maternal dTpa evaluator to determine whether the
dose missed in pregnancy was actually administered in the pregnancy that
just ended.

### Rule-level safety gate

The future dTpa evaluator must distinguish schedule eligibility from
administration safety.

Calendar-due status does not replace screening for contraindications or
precautions.

## BH8E6A2 — current weight for BCG assessment

BCG source review exposed a distinction that the earlier normalized model
did not yet represent.

`birth_weight_grams` remains historical neonatal context. It describes
weight at birth and must not be used as a substitute for the child's
current weight at a later vaccination encounter.

`current_weight_grams` records current assessment weight in grams when
that value is available.

The fields deliberately remain separate because a child may:

- have been born below 2,000 g and subsequently reach or exceed 2,000 g;
- have a documented birth weight that does not establish current weight;
- have current weight available while birth weight is unknown.

No conversion, extrapolation, growth estimate or age-based inference is
permitted between the two fields.

For the BCG rule, the national 2026 source states that vaccination is
deferred for a term or preterm newborn weighing below 2,000 g until the
infant reaches 2,000 g.

Therefore a future BCG evaluator must consume current weight for that
live threshold and must never substitute historical birth weight.
