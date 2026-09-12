# Brazil 2026 PNI — normalized-model gap remediation

Review date: 2026-09-11

BH8C identified eleven model gaps before any vaccine-specific engine was
allowed to start.

BH8D resolves those representation gaps without implementing vaccine
recommendations.

## Resolved representation gaps

The normalized model now represents:

- current pregnancy episode identity;
- maternal HBsAg status;
- birth weight;
- BCG vaccination record/scar/nodule evidence;
- disease history and disease-event dates;
- exposure-event dates;
- breastfeeding context;
- travel destination and dates;
- a separate travel/area-risk recommendation layer.

## Fail-closed semantics

### Maternal HBsAg

Positive, negative and unknown/unavailable are separate values.

Unknown/unavailable is not negative.

### BCG evidence

Each evidence channel is tri-state:

- true — assessed/present;
- false — assessed/absent;
- null — not assessed/unknown.

No empty BCG evidence object is valid.

### Pregnancy episodes

An opaque local pregnancy episode key may be attached to the current
pregnancy and to a historical dose.

The key exists only to associate a historical pregnancy dose with the
current pregnancy episode. It is not itself a clinical criterion.

### Disease and exposure dates

Disease event dates may remain unknown.

A future rule that requires an unknown date must return a context-needed
or manual-review result instead of estimating the date.

Recorded disease/exposure events may not occur after the assessment
date.

### Breastfeeding

Breastfeeding is not merged with pregnancy.

The youngest breastfed child's date of birth may be supplied where a
source uses the infant's age in a vaccination rule.

### Travel

A travel record stores destination and dates.

The application must not infer that the destination is an official
yellow-fever or other risk area merely because a destination was entered.

Risk-area status must come from an authoritative applicable source.

### Recommendation layers

`travel_or_area_risk` is distinct from:

- routine;
- seasonal strategy;
- rescue strategy;
- outbreak/blocking;
- special condition.

## Engine gate

After BH8D, granular vaccine-rule implementation may begin.

That permission does not require every clinical branch to be automated.

Where the authoritative source requires case-by-case assessment,
unavailable context, RIE/CRIE evaluation, geographic confirmation or
clinical risk-benefit judgment, the engine should fail closed using
`context_required` or `special_pathway_review`.

## Post-lock remediation — BCG current weight

The BH8E6 BCG preflight identified one additional model gap after the
initial BH8D lock.

The earlier model contained `birth_weight_grams`, but the national BCG
rule is expressed against the newborn's weight at the vaccination
encounter: vaccination is deferred below 2,000 g until the infant reaches
2,000 g.

Historical birth weight cannot safely answer that question.

BH8E6A2 therefore adds:

`PniAssessmentContext.current_weight_grams`

with an explicit gram unit and no automatic inference from birth weight,
age, growth trajectory or any unrelated weight field elsewhere in the
application.

The original `birth_weight_grams` field is retained unchanged.

This remediation does not itself implement a BCG recommendation rule.
