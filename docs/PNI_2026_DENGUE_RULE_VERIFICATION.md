# PNI 2026 — DNG4/Takeda routine rule verification

## Scope

This Python-only evaluator implements the national position-20 Takeda
dengue layer.

It consumes only the locked product-sensitive history model
`PNI26-DNG4-TAKEDA-HISTORY-001`.

It does not parse raw dengue vaccine history.

## New initiation

A new Takeda series is initiated only from exact age 10 through the day
before the fifteenth birthday.

At exact age 15 or later, this core does not initiate Takeda.

Separate Butantan strategies are not synthesized.

## Existing Takeda series

A valid Takeda D1 administered before age 15 may remain pending after the
fifteenth birthday.

The public completion layer is considered from exact age 10.

The core does not automatically carry completion through age 60 or later.

## Series chronology

The Takeda D1-to-D2 interval is fixed at 90 days.

Calendar-month clamping is not used.

Early-dose correction is inherited from the locked history normalizer.

## Prior dengue before D1

When a new D1 would otherwise be due and prior dengue is documented, the
recommended wait is six calendar months from the latest relevant onset.

No fixed-day conversion is used for this six-month interval.

If that timing reaches or passes the fifteenth birthday, this core does
not initiate Takeda.

## Dengue after D1

Dengue after a valid D1 does not restart the series.

D2 respects both:

- the history-derived Takeda chronology; and
- at least 30 days after relevant dengue onset occurring on or after D1.

A six-month post-D1 dengue delay is not applied.

## Other arboviruses

Yellow fever, chikungunya, and Zika require an explicit recovery date.

Automatic vaccination timing uses recovery date plus 30 days.

Recovery is never inferred.

## Immunoglobulin and blood products

The ordinary interval is three calendar months from treatment end.

An explicitly authorized minimum interval is six weeks, represented as
42 days.

No exposure date or treatment-end date is inferred.

## Live-vaccine interaction

Another live or attenuated vaccine may be administered on the same day.

If administered on a different day, the interval is 30 days.

No 15-day exception is inherited from another PNI vaccine family.

## Pregnancy and breastfeeding

Pregnancy and breastfeeding are distinct contexts.

Either documented state routes an otherwise-due Takeda dose to
contraindication/special review.

Neither state is inferred.

## Special conditions and administration safety

Relevant immunodeficiency or immunosuppression is handled through the
special-condition review gate.

Administration-time safety concerns include severe hypersensitivity,
prior serious reaction, or moderate/severe acute febrile illness.

Mild illness is not automatically inferred as a safety concern.

## Product boundary

Prospective recommendations from this core are Takeda only.

Butantan is not offered as a routine substitute.

The historical Takeda-D1 to accidental Butantan error-management
completion is consumed only as an already-complete history outcome.

## Decision ordering

The evaluator intentionally stops at the earliest decisive layer:

1. history completeness/safety;
2. existing completion;
3. pure vaccine-series timing;
4. disease/exposure timing;
5. other-live-vaccine timing;
6. pregnancy;
7. breastfeeding;
8. special-condition screening;
9. administration-safety screening;
10. recommendation.

Therefore administration-day contexts are not requested for a dose that
is already not due because of an earlier source-supported timing rule.

## Deferred

This evaluator does not automate:

- Butantan strategies;
- occupational Butantan strategies;
- municipality-specific Butantan campaigns;
- Sanofi revaccination;
- special-population schedules;
- API/browser/UI exposure.

No synthetic vaccination score is produced.
