# Brazil PNI 2026 — pneumococcal VPC10/VPC20 history model gap

Review date: 2026-09-11

## Scope

This tranche normalizes routine-child pneumococcal conjugate history
during the 2026 VPC10 → VPC20 transition.

It does not decide which dose is due.

## Why product identity must remain visible

The 2026 transition intentionally uses different products in different
positions of the routine schedule.

The Ministry's transition guide specifies VPC20 and VPC10 separately
and permits mixed-product completion.

Therefore a generic "pneumococcal conjugate dose count" would lose
clinically relevant information.

The normalizer preserves separate histories for:

- `pneumococcal_10` — VPC10;
- `pneumococcal_20` — VPC20.

It merges chronology without erasing source product identity.

## History-state safety

Unknown or partial VPC10/VPC20 history is not converted to zero-dose
history.

Undated prior-dose evidence prevents safe role assignment.

A possible duplicate VPC10/VPC20 exposure on the same date fails closed.

A dose stored under one product history but cross-labelled with the
other product key is rejected.

## No schema mutation

`PniVaccineHistory` already supports distinct VPC10 and VPC20 keys.

`PniAssessmentRequest` already prevents duplicate history objects for
the same vaccine key.

No `schemas.py` mutation is required by this tranche.

## Exact 11-month source hold

The June 2026 DPNI VPC20 transition guide contains an internal
inconsistency for a child exactly 11 months old with no pneumococcal
vaccination history.

The branch explicitly says to administer D1 with VPC20.

The continuation then says the VPC20 booster should observe 60 days
after D2, although that no-history sub-branch has not supplied D2.

The pre-transition 2026 normative VPC10 wording has a comparable
structural ambiguity: it says to administer one dose at 11 months but
then describes the booster relative to the second basic-series dose.

This tranche therefore does not invent:

- a missing D2;
- a synthetic dose role;
- a booster date;
- a completed schedule.

The exact 11-month/no-history decision branch remains blocked pending a
clear authoritative resolution.

## RIE boundary

This routine normalizer consumes only VPC10 and VPC20 routine history.

It does not map or infer:

- VPC13 RIE history;
- VPP23 history;
- special-condition VPC20 schedules;
- adult pneumococcal schedules.

Any future special-pathway interoperability requires its own
authoritative contract.

## Deferred

- routine decision engine;
- D1/D2 role assignment;
- 5–10 month catch-up;
- exact 11-month catch-up;
- 12–59 month catch-up;
- booster logic;
- RIE and special-condition pathways.

## Current-state source-hold refinement — 2026-09-11

The original source ambiguity remains visible in the DPNI guide: the
11-month/no-history row says to administer D1 VPC20 while the
continuation discusses a booster interval after D2.

That ambiguity does not require inventing D2.

For current-state evaluation, the source provides two independently
usable age states:

- at 11 months with no history: administer D1 VPC20 now;
- from 12 months through 4 years, 11 months and 29 days with only D1
  documented: administer one VPC20 booster, observing at least 60 days
  after D1.

The engine therefore evaluates only the current state and reassesses
the child under the later age branch at a later encounter.

The remaining unresolved state is narrower:

- exact 11-month age band;
- exactly one prior VPC20 exposure;
- no VPC10 exposure.

The 11-month source row explicitly describes prior D1 VPC10 and zero
history, but does not explicitly describe this one-prior-VPC20 state.
That branch must return source-hold review rather than infer D2.

No VPC13, VPP23, RIE, adult or special-condition schedule is introduced
by this refinement.
