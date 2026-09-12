# Brazil 2026 PNI — authoritative rule-family matrix

Review date: 2026-09-11

Baseline checkpoint:
`433f89d04cc23ead88f1fd71bf35f13f97a73b4f`

## Purpose

This tranche maps the 21 vaccine families in the 2026 national
normative calendar to the context that a future recommendation engine
must consume.

It is not yet the recommendation engine.

It deliberately does not pretend that one age table is sufficient.

## Twenty-one baseline vaccine families

The national 2026 normative document lists:

1. dTpa
2. maternal RSV vaccine — VVSR
3. hepatitis B — HB
4. BCG
5. pentavalent
6. inactivated poliovirus — VIP
7. rotavirus — VRH
8. pneumococcal 20-valent — VPC20
9. pneumococcal 10-valent — VPC10
10. meningococcal C — menC
11. influenza trivalent — INF3
12. covid-19 RNAm
13. yellow fever — VFA
14. meningococcal ACWY — menACWY
15. MMR / tríplice viral — SCR
16. DTP
17. varicella — VZ
18. hepatitis A — HA
19. HPV4
20. dengue — DNG4
21. adult diphtheria/tetanus — dT

Each family receives a stable baseline rule-family ID. Granular
dose-history branches remain pending.

## Why engine implementation remains blocked

Authoritative extraction identified data that the BH8B normalized model
does not yet represent explicitly enough for safe automation.

### Current-pregnancy episode

dTpa and maternal RSV are recommended in each pregnancy.

A historical vaccine dose date alone must not be assumed to prove that
the dose belongs to the current pregnancy episode.

### Maternal HBsAg status

The hepatitis-B neonatal pathway contains specific recommendations when
the mother is HBsAg positive or when maternal status is unavailable.

This is maternal context, not the newborn's own special-condition code.

### Birth weight

BCG guidance includes a neonatal weight-dependent delay.

The engine therefore needs structured birth-weight context rather than
trying to infer it.

### BCG non-dose evidence

The official guidance accepts certain scar/nodule findings as evidence
relevant to prior BCG vaccination.

That is not represented by a conventional administration record.

### Disease history and event dates

Varicella and dengue demonstrate why disease history and dates matter.

Dengue recommendations can depend on the time since a dengue infection.

Varicella outbreak/post-exposure recommendations can depend on the time
since exposure.

### Breastfeeding context

Dengue contains a lactation-specific contraindication pathway.

Pregnancy status alone does not represent breastfeeding.

### Travel / area-risk context

Yellow-fever recommendations include branches based on residence or
travel to an area with confirmed virus circulation and, for travel,
timing before departure.

The present recommendation-layer enum also lacks a clean
`travel_or_area_risk` layer.

## 2026 overlays

The matrix keeps later 2026 changes separate from the January baseline.

Locked overlays include:

- VPC20 national transition beginning in June 2026, without inventing an
  exact day when the reviewed source states only the month;
- later VPC20/RIE technical guidance;
- HPV 15–19 rescue strategy, distinct from routine HPV 9–14;
- 2026 influenza strategy for Northeast, Central-West, South and
  Southeast, distinct from routine eligibility;
- September 2026 Comirnaty LP.8.1 operational/product guidance without
  asserting an eligibility change;
- municipality-specific measles dose-zero rules that must not be
  universalized;
- RIE hexa/dTpa guidance;
- dengue product-interchangeability guidance.

## Safety rule

No Python recommendation engine should be started until the model gaps
identified by this matrix are either:

1. represented explicitly in the normalized schema; or
2. intentionally classified as manual/special-pathway review with a
   documented reason that automation is unsafe.

The matrix is therefore a gate, not merely documentation.
