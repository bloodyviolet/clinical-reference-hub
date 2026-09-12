# PNI 2026 — influenza history and cycle model gap

Review date: 2026-09-11

## Why generic dated history is insufficient

The 2026 national influenza rule is both history-sensitive and
season-sensitive.

For children, first influenza vaccination requires two doses separated
by 30 days. A child with qualifying vaccination in previous
years/cycles receives one annual dose in subsequent cycles.

A dose date alone cannot safely identify its influenza cycle.

Federal 2026 registration material still refers to the
"Região Norte – 2025" influenza strategy while those registrations
occur in calendar year 2026. Therefore the clinical core must never
derive influenza-cycle identity from `administration_date.year`.

## Selected model

Generic `PniVaccineHistory` remains the lifetime history.

Influenza receives a dedicated cycle-evidence overlay containing:

- an opaque, source-supplied `current_cycle_key`;
- an explicit current-cycle history state;
- explicit dated current-cycle events;
- a `routine` or `special` strategy layer for each cycle event;
- an explicit prior-cycle vaccination state.

The clinical layer does not parse the cycle key, infer geography from
it, or assume that its text contains a year.

## Prior-cycle state

Allowed states are:

- `documented_prior`;
- `documented_none`;
- `unknown`.

The normalizer does not manufacture prior-cycle status from the
calendar year of historical doses.

`unknown` fails closed for the first routine-child engine because
priming status changes the dose sequence.

## Reconciliation

Every explicit current-cycle event must reconcile to exactly one dated
influenza event in the generic lifetime history.

The normalizer rejects:

- future cycle events;
- duplicate current-cycle dates;
- unreconciled cycle events;
- inconsistent documented-zero states.

Same-day ambiguity in lifetime history fails closed.

## Strategy boundary

`routine` and `special` are preserved as distinct strategy layers.

The first routine-child engine will not silently consume
special-strategy evidence. Strategy interoperability remains deferred
until a separate source contract authorizes it.

## Product boundary

The first public routine layer recognizes the public INF3 history key
`influenza`.

Private or otherwise unsupported formulation identities are retained
as unsupported product keys and fail closed. No INF4 equivalence is
inferred.

## Role boundary

This normalizer assigns no D1, D2 or DU roles.

Those decisions belong to a later current-state evaluator after the
history layer is qualified.

## Deferred

This tranche does not implement:

- an influenza decision engine;
- pregnancy or postpartum rules;
- the >=60-year rule;
- special-strategy eligibility;
- the indigenous/comorbidity child extension to <9 years;
- North strategy timing logic;
- private INF4 interoperability;
- API/browser/UI support.

No generic PNI schema is modified.
