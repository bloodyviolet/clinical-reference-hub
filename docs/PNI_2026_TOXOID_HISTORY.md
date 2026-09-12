# Brazil 2026 PNI — D/T toxoid history normalization

Review date: 2026-09-11

## Why this contract exists

The maternal dTpa recommendation is not a single-vaccine-history rule.

The 2026 national PNI instructs vaccination teams to consider previous
doses of vaccines containing diphtheria and tetanus toxoids when
determining basic-series completion and interval timing.

Therefore a future dTpa rule must consume cross-vaccine antigen history,
not only a `dtpa` history bucket.

## Canonical component mapping

BH8E2 maps only source-supported canonical vaccine families:

- `dtpa` — diphtheria toxoid + tetanus toxoid + pertussis antigen;
- `dt` — diphtheria toxoid + tetanus toxoid;
- `dtp` — diphtheria toxoid + tetanus toxoid + pertussis antigen;
- `pentavalent` — diphtheria toxoid + tetanus toxoid + pertussis antigen;
- `hexa_acellular_rie` — diphtheria toxoid + tetanus toxoid +
  pertussis antigen.

The special RIE hexavalent product is kept visibly marked as a
special-pathway product.

BH8E2 does not attempt to invent an exhaustive mapping for every
historical or international combination vaccine.

An unknown vaccine key is therefore surfaced as unmapped and makes
automated interval/count evaluation unsafe.

## Explicit history scope

Cross-vaccine completeness cannot be inferred merely because some
vaccination records are present.

The caller must explicitly classify relevant D/T history as:

- `complete`;
- `partial`;
- `unknown`.

Only `complete` scope with no ambiguity can be marked safe for basic
series counting or interval evaluation.

## Same-day ambiguity

More than one D/T-containing dose record on the same administration date
is preserved and flagged.

BH8E2 does not silently deduplicate such records because two entries
might represent:

- duplicate documentation of one administration;
- distinct products;
- a documentation error;
- an unusual clinical event.

The future dTpa rule must fail closed until that ambiguity is resolved.

## Interval boundary

The source defines:

- 60 days as the recommended interval;
- 30 days as the exceptional minimum interval.

BH8E2 records why those intervals matter but does not apply them.

Applying those numbers belongs to the future maternal dTpa rule.

## Basic-series boundary

Likewise, the source defines a three-dose D/T-containing basic series.

BH8E2 exposes a safe cross-vaccine exposure-event count only when the
history scope is explicitly complete and no ambiguity exists.

It does not itself label the basic series complete.

## Engine boundary

After BH8E2 the future maternal dTpa evaluator may use:

- chronological D/T-containing exposures;
- safe exposure-event count;
- last D/T-containing exposure date;
- explicit completeness status.

dTpa itself remains unimplemented in this tranche.
