# PNI 2026 — DTP child-history model

## Scope

This model normalizes the ordinary childhood DTP booster history required
before implementing the DTP due-decision engine.

It does **not** decide whether DTP should be administered today.

## Architecture

DTP routine completion is not derived from a generic count of
diphtheria/tetanus/pertussis antigen exposures.

The ordinary history model keeps two roles separate:

1. **Pentavalent basic series**
   - three qualifying pentavalent doses;
   - exact chronology retained;
   - qualifying D3 retained explicitly.

2. **DTP boosters**
   - DTP R1;
   - DTP R2;
   - physical DTP identity retained.

The existing cross-vaccine toxoid normalizer remains useful antigen-level
provenance, but is not the authority for DTP booster completion.

## Pentavalent prerequisite

Automatic ordinary interpretation requires an unambiguous three-dose
pentavalent basic series.

The first DTP-history model fails closed on pentavalent evidence requiring
unrepresented historical exception authorization, including:

- D1 before the ordinary 2-month point;
- 30–59 day historical intervals without explicit exception evidence;
- intervals below 30 days;
- D1→D3 shorter than four calendar months;
- D3 before six months;
- more than three pentavalent events.

This does not declare every such historical schedule clinically invalid.
It means the ordinary DTP model lacks enough structured evidence to
auto-classify it.

## DTP booster chronology

A historical R1 requires:

- qualifying pentavalent basic series;
- DTP product identity;
- age at least 15 months;
- at least six calendar months after qualifying penta D3;
- administration before the exact seventh birthday.

A historical R2 requires:

- valid R1;
- age at least four years;
- at least six calendar months after R1;
- administration before the exact seventh birthday.

The six-month minimum is never compressed.

## Age-7 closure

If a late valid R1 makes the earliest possible R2 date fall on or after
the exact seventh birthday, the normalized model records that the DTP R2
opportunity has closed.

It does not synthesize a dT recommendation. dT remains a separate family.

## Product boundaries

- `pentavalent` may establish the ordinary primary series.
- `dtp` may establish ordinary childhood R1/R2.
- `dtpa` is not silently converted into childhood DTP.
- `dt` cannot satisfy a pertussis-containing booster.
- `hexa_acellular_rie` remains special-pathway evidence.
- a later pentavalent exposure is not silently promoted to DTP booster
  status.

## Fail-closed conditions

The normalizer fails closed for ordinary automatic interpretation when
history is incomplete, unknown, undated, product identity is unsupported,
chronology is ambiguous, or required historical timing is invalid or
insufficiently evidenced.

## Boundary

The history layer does not infer:

- neurologic or serious pertussis-component AEFI status;
- CRIE eligibility;
- outbreak/contact-control applicability;
- pentavalent substitution for unavailable DTP;
- future dT scheduling;
- administration safety;
- any synthetic vaccination score.
