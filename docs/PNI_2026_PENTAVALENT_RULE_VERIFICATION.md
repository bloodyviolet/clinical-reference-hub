# Brazil 2026 PNI — pentavalent basic-series rule verification

Review date: 2026-09-11

## Implemented scope

BH8E11A1 implements the routine homologous pentavalent basic series and
catch-up while the vaccine remains age-eligible.

Agenda:

- D1 at 2 months;
- D2 at 4 months;
- D3 at 6 months.

The routine interval is 60 days.

The minimum 30-day interval is an exceptional acceleration mechanism and
requires explicit prospective authorization.

## Exceptional early start

The Ministry permits initiation from 1 month and 15 days only in an
exceptional circumstance.

The evaluator therefore distinguishes:

- before 1m15d -> never eligible;
- 1m15d to before 2m -> eligible only with explicit
  `exceptional_early_start_authorized=True`;
- from 2m -> routine age eligibility.

A previously documented D1 in that early window is not silently treated
as routine. Explicit confirmation of the exceptional early start is
required.

## D3 independent constraints

D3 must satisfy all applicable requirements:

1. interval from D2:
   - 60 days routinely;
   - 30 days only with explicit exceptional acceleration;
2. at least 4 calendar months from D1;
3. age at least 6 months.

The 4-calendar-month D1→D3 requirement is independent and reflects the
hepatitis-B component of pentavalent vaccine.

## Historical exceptional intervals

For already documented dose histories, intervals of 30–59 days route to
review.

A present-time request to accelerate a future dose is not treated as
proof that a past shortened interval had an authorized exceptional
context.

## Vaccine-key counting boundary

Only `PniVaccineHistory(vaccine_key="pentavalent")` is counted as the
pentavalent series in BH8E11A1.

The following are not silently converted into pentavalent doses:

- monovalent hepatitis B;
- DTP;
- RIE hexavalent/acellular products;
- hypothetical standalone Hib history.

There is no standalone normalized Hib vaccine key in the current PNI
matrix/model.

Pentavalent still contributes diphtheria, tetanus and pertussis antigen
exposure to the independent toxoid-history normalizer. That antigen
interoperability does not change pentavalent product-series counting.

## Age boundary

Pentavalent catch-up remains available through the child age range
defined by the 2026 instruction.

After this layer closes, older-age diphtheria/tetanus and hepatitis-B
catch-up belong to separate vaccine rules.

## DTP booster boundary

The 15-month and 4-year boosters use DTP and are not implemented by this
pentavalent basic-series evaluator.

Use of pentavalent as a substitute booster in specific control contexts
when DTP is unavailable is also outside this routine tranche.

## CRIE / severe AEFI

RIE/CRIE alternatives and severe adverse-event pathways involving the
whole-cell pertussis component remain separate.

The routine schedule engine does not infer these conditions.

## Localization

Every output contains complete PT-BR and EN-GB interpretations sharing
one language-neutral decision.
