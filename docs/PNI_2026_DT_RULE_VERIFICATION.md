# PNI 2026 — dT routine rule verification

## Scope

This Python-only rule implements normative position 21 for the adult-type
diphtheria-tetanus vaccine (`dT`) from exact age 7 onward.

It reuses the already locked cross-vaccine D/T toxoid normalizer. No
duplicate dT history model is created.

## Cross-vaccine history

The schedule considers documented physical administrations containing
both diphtheria and tetanus toxoids, including supported dT, dTpa, DTP,
pentavalent, and other products already mapped by the locked toxoid
normalizer.

The rule layer does not parse raw vaccine histories.

## Historical primary-series interpretation

The federal 2026 schedule recommends 60 days between doses and permits a
30-day minimum in justified special situations.

Historical records do not encode proof that a 30–59-day interval was
authorised as an exceptional acceleration.

The rule therefore derives two chronological subsequences:

- ordinary: at least 60 days between counted events;
- minimum-possible: at least 30 days between counted events.

If the ordinary subsequence itself contains at least three doses, basic
series completion is independently proven.

If the series remains incomplete and the two counts disagree, automatic
interpretation fails closed to review.

An event less than 30 days after the previous counted event never becomes
the next primary-series position.

## Prospective incomplete-series timing

The routine next dose is based on:

- the latest counted primary-series event + 60 days; and
- an absolute 30-day floor after the latest physical D/T exposure.

The later date is used.

When an exceptional minimum is explicitly authorised, the next dose uses
the later of:

- latest counted primary-series event + 30 days; and
- latest physical D/T exposure + 30 days.

The software never infers exceptional authorisation.

The basic series is not restarted because of delay.

## Booster anchor

Once a three-dose ordinary-spaced basic series is proven, the booster
clock is anchored to the latest documented physical administration
containing both D and T toxoids—not merely to the third primary-series
dose and not merely to the latest product labelled `dT`.

This naturally yields the age-14 agenda when the previous DTP booster was
given at age 4.

## Booster timing

The ordinary booster threshold is 10 calendar years after the latest
physical D/T-containing administration.

A relevant diphtheria/tetanus exposure may activate a 5-calendar-year
booster threshold.

Exposure risk is explicit and is never inferred.

Before 5 years the exposure-risk state is irrelevant.

From 5 years through the day before 10 years, exposure-risk status is
decision-relevant.

At 10 years or later, ordinary booster timing applies without requiring
exposure-risk screening.

## Pregnancy

Pregnancy is not represented as a contraindication to dT.

The 2026 pregnancy schedule may use dT to complete an incomplete D/T
series while also requiring pregnancy-specific dTpa.

Because sequencing depends on pregnancy-specific information, an
otherwise-due dT dose in a pregnant person routes to special review. The
general dT core does not duplicate the already-qualified maternal dTpa
engine.

## dTpa-priority occupational groups

Source-defined healthcare workers, traditional midwives, and specified
health trainees have separate dTpa recommendations.

When dT is otherwise due, a documented priority occupation routes to
special review because the occupational dTpa evaluator remains deferred.

This does not claim that dT can never be used to complete an incomplete
D/T series in such people.

## Arthus and administration safety

The federal 10-year precaution after a severe Arthus-type reaction is
preserved as a safety boundary.

The existing history model cannot reliably bind an Arthus episode to a
specific vaccine administration, so the first dT core does not invent an
automatic reaction-date calculator.

Documented Arthus or another relevant safety concern routes to
`special_pathway_review`.

## Coadministration

No interval is required between dT and other current CNV vaccines.

No dT interaction schema is introduced.

## Deferred

This rule does not implement:

- maternal dT/dTpa joint sequencing;
- occupational dTpa scheduling;
- wound prophylaxis or tetanus immunoglobulin;
- diphtheria contact management;
- automatic Arthus reaction-date calculations;
- API/browser/UI exposure.

No diagnosis, exposure risk, occupation, pregnancy, exceptional interval,
or synthetic vaccination score is inferred.
