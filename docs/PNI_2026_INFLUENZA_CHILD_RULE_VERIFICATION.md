# PNI 2026 — rotina infantil de influenza INF3

Review date: 2026-09-11

## Authority

The rule is based on the 2026 Ministry of Health / DPNI national
vaccination instruction and the current national vaccination calendar.

## Scope

This first influenza decision core is deliberately restricted to the
standing routine-child INF3 pathway:

- age at least 6 months;
- age younger than the exact sixth birthday.

It does not implement campaign/special-strategy eligibility.

## Cycle-aware history

The evaluator consumes `normalize_influenza_history()` output.

Influenza-cycle identity is:

- explicit;
- source supplied;
- opaque to the clinical core.

The evaluator never derives influenza-cycle identity from the calendar
year and never parses geography from the cycle key.

## First influenza vaccination

When reliable history establishes no vaccination in a prior cycle:

- no routine current-cycle dose -> D1 INF3;
- one routine current-cycle D1 -> D2 after 30 days;
- two routine current-cycle doses at least 30 days apart -> current
  cycle complete.

A historical D1/D2 interval under 30 days is reviewed rather than
silently accepted.

No exceptional interval shorter than 30 days is inferred.

## Previously vaccinated child

When at least one qualifying prior-cycle influenza vaccination is
explicitly established:

- no routine dose in the current cycle -> one annual INF3 dose;
- one routine current-cycle dose -> current cycle complete;
- more than one routine current-cycle dose -> review.

## Exact age boundaries

Routine-child scope is:

`[DOB + 6 calendar months, DOB + 72 calendar months)`

An influenza routine event before 6 months or on/after the sixth
birthday is not automatically validated by this rule.

## Sixth-birthday source hold

A narrow unresolved state is deliberately preserved:

- the child has documented no prior-cycle influenza vaccination;
- first-ever D1 was administered while the child was still younger
  than 6 years;
- the 30-day D2 threshold falls on or after the exact sixth birthday.

The reviewed routine source defines both:

- the routine age ceiling before age 6; and
- the 30-day two-dose primovaccination schedule.

It does not explicitly state whether an in-scope D1 authorizes D2 after
the child ages out of the routine-child indication.

The evaluator therefore returns review and does not infer D2 beyond
the age ceiling.

## Fail-closed boundaries

The evaluator fails closed for:

- unknown priming state;
- unknown/partial relevant history;
- special-strategy evidence;
- unsupported/private product identity;
- ambiguous chronology;
- influenza events before 6 months;
- influenza events on/after age 6;
- invalid historical first-series interval;
- the sixth-birthday crossover state.

## Deferred

Not implemented here:

- pregnancy;
- postpartum;
- age 60 years and older;
- special annual strategy;
- indigenous/comorbidity extension to under 9 years;
- North strategy timing;
- private INF4 interoperability;
- API/browser/UI.

Every result is bilingual PT-BR / EN-GB and uses a language-neutral
decision code.

No synthetic vaccination score is produced.
