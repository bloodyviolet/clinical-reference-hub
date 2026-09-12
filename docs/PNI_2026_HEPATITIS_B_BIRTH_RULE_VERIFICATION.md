# Brazil 2026 PNI — hepatitis-B birth-dose rule verification

Review date: 2026-09-11

## Implemented scope

BH8E7A1 implements only the monovalent hepatitis-B dose-at-birth layer.

The 2026 national instruction defines one monovalent dose:

- immediately after birth;
- preferably in the delivery room or within the first 12 hours;
- only through 1 month of life when that early opportunity was missed.

This evaluator does not implement the complete hepatitis-B family.

## Twelve-hour agenda

The normalized PNI context currently records calendar dates, not exact
birth and assessment timestamps.

Therefore BH8E7A1 records the first-12-hours recommendation as agenda
provenance but does not fabricate an hour-level classification.

That limitation does not change the current action: an eligible child
inside the active birth-dose window should receive the dose as soon as
possible.

## One-month boundary

The monovalent birth-dose opportunity remains active through age 1 month.

After that opportunity has passed, this evaluator returns
`not_applicable`.

It must not create a late monovalent dose and label it as the birth dose.

The 2026 PNI states that an infant who missed the birth-dose opportunity
should proceed with the pentavalent schedule at ages 2, 4 and 6 months.

That later schedule is separate from BH8E7A1.

## Pentavalent separation

`hepatitis_b` and `pentavalent` are separate normalized vaccine keys.

BH8E7A1 consumes only `PniVaccineHistory(vaccine_key="hepatitis_b")`.

It does not infer that a pentavalent dose retroactively satisfies the
monovalent birth-dose opportunity.

Likewise, this evaluator does not calculate the 2/4/6-month pentavalent
series.

## Maternal HBsAg

The normalized states remain distinct:

- `negative`;
- `positive`;
- `unknown_or_unavailable`.

`positive` routes to `special_pathway_review`.

The confirmed-positive pathway includes monovalent hepatitis-B vaccine
plus hepatitis-B immune globulin at separate administration sites and is
not implemented by this routine evaluator.

`unknown_or_unavailable` also routes to `special_pathway_review`, because
the 2026 instruction explicitly directs absence of maternal-status
information toward perinatal immunoprophylaxis assessment.

BH8E7A1 does not infer that immune globulin is automatically required
when maternal status is unknown or unavailable.

Maternal status is never silently converted from unknown to negative.

When maternal HBsAg status has not been supplied at all while the
birth-dose window remains active, the routine evaluator also routes to
review. The interpretation explicitly states that time-sensitive
hepatitis-B vaccination should not be delayed solely while this context
is clarified.

## History

Within the active birth-dose window:

- a documented hepatitis-B dose inside that window -> `not_due_now`;
- documented zero dose -> proceed to safety gates;
- missing history -> `history_required`;
- unknown/partial history -> `history_required`.

A dose administered after the birth-dose window does not retroactively
become a birth dose.

## Special clinical conditions

Explicit special-condition context returns `special_pathway_review`.

The routine evaluator does not infer special conditions or implement
CRIE/post-exposure pathways.

## Administration safety

Calendar eligibility does not itself establish safe administration.

For an otherwise due dose:

- safety not screened -> `context_required`;
- safety concern -> `special_pathway_review`;
- screened with no concern -> `recommend_now`.

## Simultaneous vaccination

The national source permits hepatitis-B vaccine to be administered with
other current CNV vaccines without a required spacing interval.

No inter-vaccine spacing is invented.

## PT-BR / EN-GB

Every result contains:

- canonical PT-BR `interpretation_pt`;
- complete secondary EN-GB `interpretation_en`.

Clinical decisions remain language-neutral.
