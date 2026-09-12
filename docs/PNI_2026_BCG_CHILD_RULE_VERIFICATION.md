# Brazil 2026 PNI — BCG child routine rule verification

Review date: 2026-09-11

## Implemented scope

BH8E6A3 implements only the routine BCG branch for prevention of severe
and disseminated tuberculosis in children.

The 2026 national schedule defines:

- one dose at birth, preferably in the maternity setting;
- if missed at birth, administration as soon as possible;
- routine availability through 4 years, 11 months and 29 days.

## Neonatal weight gate

The PNI states that a term or preterm newborn weighing below 2,000 g
should have BCG deferred until reaching 2,000 g.

Ministry of Health material defines the neonatal period as the first
28 days of life. BH8E6A3 therefore applies the automatic source-defined
newborn weight gate at ages 0–27 completed days.

For an unvaccinated newborn:

- current weight unknown -> `context_required`;
- current weight <2,000 g -> `not_due_now`;
- current weight >=2,000 g -> routine evaluation may proceed.

The evaluator uses `current_weight_grams`.

It never substitutes `birth_weight_grams`, estimates current weight from
age, or extrapolates a growth trajectory.

A reported current weight below 2,000 g outside the neonatal period is
sent to `special_pathway_review` instead of extrapolating the newborn
rule.

## Evidence of prior BCG

The national source accepts the following as evidence of vaccination:

- vaccination record;
- BCG scar;
- palpable nodule in the expected vaccination site.

Any positive evidence can satisfy the routine one-dose rule.

Evidence assessed as absent does not by itself prove that the child was
never vaccinated.

In particular, absence of a BCG scar alone must never be converted into
a routine revaccination indication.

## Conflicting evidence

A normalized `documented_zero_dose` history conflicting with positive
record/scar/nodule evidence returns `history_required`.

The evaluator does not silently choose one contradictory source.

## Routine revaccination boundary

Children vaccinated at the recommended age who do not develop a scar do
not routinely receive another BCG dose.

The 2026 source describes exceptional revaccination only after a known
invalid administration event and subsequent monitoring.

That exceptional pathway is outside BH8E6A3.

## Special pathways kept separate

BH8E6A3 does not implement:

- hanseniasis-contact BCG immunoprophylaxis;
- HIV exposure or infection pathways;
- primary or acquired immunodeficiency;
- immunosuppressive treatment;
- newborn tuberculosis-contact management;
- malignancy-related contraindications;
- pregnancy;
- exceptional invalid-dose revaccination.

When explicit `special_condition_codes` or
`epidemiologic_context_codes` are supplied, the routine evaluator
returns `special_pathway_review`.

No special condition is inferred.

## Administration safety

Calendar eligibility is not administration clearance.

For an otherwise due routine dose:

- `not_screened` -> `context_required`;
- `screened_concern` -> `special_pathway_review`;
- `screened_no_concern` -> routine logic may return `recommend_now`.

## Simultaneous administration

The 2026 national source permits BCG administration simultaneously with
the other vaccines in the current national calendar without a required
interval.

No inter-vaccine spacing interval is invented.

## PT-BR / EN-GB

Every result contains both:

- canonical PT-BR `interpretation_pt`;
- complete secondary EN-GB `interpretation_en`.

The clinical decision is shared and language-neutral.
