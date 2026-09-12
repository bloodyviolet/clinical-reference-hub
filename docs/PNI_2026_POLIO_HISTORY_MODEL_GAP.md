# Brazil PNI — poliomyelitis history model-gap remediation

Review date: 2026-09-11

## Why a history normalizer is required

The current national routine uses inactivated poliovirus vaccine
(VIP/IPV), but product identity remains clinically relevant when
reconstructing older vaccination histories.

The 2024 transition from VOPb to an exclusive VIP schedule explicitly
distinguishes historical VOP boosters from VIP.

Therefore an `ipv`-only dose counter is insufficient.

## Normalized history keys

BH8E12A1-M1 recognizes these distinct history families:

- `ipv` — current standalone VIP;
- `opv_bivalent_legacy` — historical VOPb;
- `penta_acellular_ipv` — DTPa/VIP/Hib;
- `tetra_acellular_ipv` — DTPa/VIP;
- `hexa_acellular_ipv` — DTPa/HepB/VIP/Hib;
- `hexa_acellular_rie` — existing RIE/CRIE hexavalent representation.

The schema already permits these keys, so no `schemas.py` mutation is
required.

## Why histories remain separate

A legacy VOPb event must not be hidden in an `ipv` history because
transition conduct depends on product identity.

Likewise, a combination vaccine remains identifiable as a combination
product even when its IPV component is a valid poliovirus exposure.

The normalizer therefore rejects a cross-labelled `product_key`.

## Transition-sensitive VOP history

The Ministry's exclusive-VIP transition guidance states that:

- after D1-D3 of VIP plus one historical VOPb booster, a VIP booster is
  still required;
- the exceptional minimum interval from that VOPb booster to the VIP
  booster is 30 days;
- D1-D3 plus both historical oral boosters was considered complete by
  the transition guidance.

BH8E12A1-M1 preserves these exposures but does not yet make the due
decision.

## Combination products

Federal interoperability guidance recognizes IPV-containing:

- DTPa/VIP/Hib;
- DTPa/HepB/VIP/Hib;
- DTPa/VIP.

BH8E12A1-M1 records those as IPV-equivalent poliovirus exposures.

This normalization does not by itself infer the eventual dose number,
booster status, or due decision.

## Cross-domain toxoid boundary

The acellular combination products contain components beyond IPV, but
the authoritative evidence used by this polio tranche establishes their
role here only as IPV-containing poliovirus exposures.

BH8E12A1-M1 therefore does **not** add:

- `penta_acellular_ipv`;
- `tetra_acellular_ipv`;
- `hexa_acellular_ipv`

to the canonical D/T toxoid component map.

If one of those new keys is supplied to the D/T history normalizer, it
remains unmapped and causes that separate domain to fail closed until
authoritative D/T-domain evidence independently supports the mapping.

This avoids allowing a polio-source decision to silently broaden the
maternal dT/dTpa history contract.

`opv_bivalent_legacy` is different: it is explicitly registered as a
known non-toxoid product so that oral polio history is ignored, rather
than misclassified, by the D/T normalizer.

## Completeness and ambiguity

The normalizer fails closed when:

- a relevant history is unknown or partial;
- a relevant record contains undated prior-dose evidence;
- an unknown vaccine key cannot be mapped;
- more than one polio exposure occurs on the same date across distinct
  histories and duplicate identity cannot be excluded.

It exposes which history keys were actually supplied.

That is important because a future VIP evaluator must not interpret
absence of a legacy-VOP history object as documented zero VOP history
when the patient's age/history makes the pre-2024 transition relevant.

## RIE / CRIE boundary

`hexa_acellular_rie` is retained as a polio exposure but marked as a
special-pathway product.

A routine VIP evaluator must not infer a CRIE indication from its
presence.

## Deferred

This tranche does not implement:

- routine VIP due decisions;
- D1/D2/D3 scheduling;
- 15-month or 4-year booster decisions;
- the VOP-to-VIP transition decision;
- CRIE eligibility;
- outbreak/blocking recommendations;
- international-travel recommendations.

## Provenance warning

The 2026 normative instruction contains a cross-reference to
Nota Técnica nº 64/2026 in the poliomyelitis section.

Current Ministry indexing identifies NT 64/2026 with the VPC20
transition. It is therefore not used here as substantive polio
authority unless independently corrected or resolved.
