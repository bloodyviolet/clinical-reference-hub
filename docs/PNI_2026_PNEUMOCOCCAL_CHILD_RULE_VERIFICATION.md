# Brazil PNI 2026 — routine child VPC10/VPC20 transition

Review date: 2026-09-11

## Authority

The engine uses the Ministry of Health / DPNI 2026 technical guide for
introduction of VPC20.

The rule is deliberately product-sensitive.

## Required history

Both histories must be supplied explicitly:

- `pneumococcal_10`;
- `pneumococcal_20`.

Absence of one product-history object is not interpreted as documented
zero.

The evaluator consumes `normalize_pneumococcal_history()` output and
does not reconstruct raw history itself.

## Timely routine

- D1 at 2 months: VPC20;
- D2 at 4 months: VPC10;
- routine primary interval: 60 days;
- booster from 12 months: VPC20;
- booster interval: at least 60 days after D2.

## Catch-up before 11 months

For ages 5–10 months:

- zero history -> D1 VPC20;
- prior D1 VPC20 -> D2 VPC10;
- prior D1 VPC10 -> D2 VPC20.

The recommended primary interval is 60 days.

A 30-day minimum is used only prospectively with explicit exceptional
authorization. Historical 30–59-day primary intervals without
structured exceptional evidence are routed to review.

## Exact 11-month age band

The current-state rules are:

- zero history -> D1 VPC20 now;
- prior D1 VPC10 -> D2 VPC20;
- two valid primary doses -> wait for the >=12-month booster branch;
- exactly one prior D1 VPC20 -> source-hold review.

For zero history, the evaluator does not invent a future D2.

At a later encounter, the child is evaluated from the actual later age
and history state.

## Ages 12 months through 4y11m29d

- zero history -> one VPC20 dose;
- one D1 documented before 12 months -> one VPC20 booster after at
  least 60 days;
- two valid primary doses before 12 months -> VPC20 booster after at
  least 60 days from D2.

A first and only VPC20 exposure administered at or after 12 months is
recognized as the single-dose catch-up state and does not automatically
generate another dose.

## Historical product patterns

Explicitly accepted pre-12-month D1/D2 patterns are:

- VPC20 -> VPC10;
- VPC10 -> VPC20;
- historical VPC10 -> VPC10.

Other product patterns are reviewed rather than inferred.

## Safety boundaries

This routine evaluator does not infer:

- VPC13 interoperability;
- VPP23 interoperability;
- RIE eligibility;
- adult schedules;
- special-condition VPC20 schedules.

Partial, unknown, ambiguous, unmapped or incompletely supplied
product history fails closed.

## Localization

Every result contains PT-BR and EN-GB interpretations with one
language-neutral decision.

No synthetic vaccination score is produced.
