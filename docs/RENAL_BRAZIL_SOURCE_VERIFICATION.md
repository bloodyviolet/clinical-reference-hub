# Renal suite — Brazilian source verification

Clinical review: 2026-09-11

## Disposition

BH2 implementation is deliberately blocked until the Brazilian source
conflicts documented here have been acknowledged in the software
contract.

No renal calculation is changed by this document.

## 1. National SUS source

Current national source:

**PCDT das Estratégias para Atenuar a Progressão da Doença Renal
Crônica**

- Portaria Conjunta SAES/SECTICS nº 11/2024
- published 26 September 2024
- current annex updated 7 February 2025
- Ministry of Health / CONITEC
- expressly national in scope

The Portaria states that the PCDT is national and is to be used by
state, Federal District and municipal SUS health departments for the
corresponding regulation/access processes.

The current PCDT recommends a serum-creatinine CKD-EPI equation.

## 2. Current Brazilian specialty-society position

The 2024 consensus position of:

- Sociedade Brasileira de Nefrologia (SBN); and
- Sociedade Brasileira de Patologia Clínica/Medicina Laboratorial
  (SBPC/ML)

recommends for adults, preferentially:

1. CKD-EPI 2021 with serum creatinine;
2. CKD-EPI 2021 with creatinine and cystatin C;
3. CKD-EPI 2012 with cystatin C.

The consensus specifically supports removal of race correction.

Therefore the existing Clinical Reference Hub CKD-EPI 2021 race-free
engine is not merely an international implementation: it is also
aligned with the current Brazilian nephrology/laboratory consensus.

### 2025 erratum to the Brazilian consensus

The Brazilian Journal of Nephrology published an erratum in 2025
correcting the CKD-EPI 2021 creatinine equation printed in the
SBN/SBPC-ML consensus.

The incorrect rendering showed the high-ratio exponent as `+1.200`.

The corrected equation uses:

`max(creatinine/k, 1)^-1.200`

Clinical Reference Hub already implements `-1.200`, so no numerical
change is required for this erratum.

## 3. PCDT equation transcription

The current Ministry PCDT identifies its formula as CKD-EPI and cites:

Levey AS et al. Ann Intern Med. 2009;150:604–612.

The Ministry table renders constants corresponding to the 2009
race-containing equation:

- A, Black:
  - female 166
  - male 163
- A, non-Black:
  - female 144
  - male 141
- B:
  - female 0.7
  - male 0.9
- high-creatinine exponent:
  - -1.209
- low-creatinine exponent:
  - female -0.329
  - male -0.411

However, the displayed table cannot safely be transcribed literally.

### Conflict PCDT-EQ-AGE-01

The current PCDT is rendered as approximately:

`TFG = A × (Creatinina/B)^C × Idade^0,993`

The actual cited 2009 CKD-EPI equation uses:

`... × 0.993^Age`

These expressions are not mathematically equivalent.

### Conflict PCDT-EQ-CREAT-02

The PCDT table renders the high-creatinine condition as:

`Creatinina > 0,7 = -1,209`

while simultaneously specifying:

- B female = 0.7
- B male = 0.9

The cited 2009 CKD-EPI equation changes branch at:

- 0.7 mg/dL in females;
- 0.9 mg/dL in males.

A software implementation must not use a universal 0.7 mg/dL branch.

## 4. Race coefficient conflict

The national PCDT table still encodes race-specific constants from the
2009 equation.

The 2024 SBN/SBPC-ML consensus instead recommends the 2021 race-free
equation.

Clinical Reference Hub will therefore not silently replace its current
race-free CKD-EPI 2021 calculation with the race-containing PCDT table.

No algorithm may infer race from appearance, name, address, geography,
ancestry assumptions or other proxies.

## 5. GFR staging

The PCDT classifies:

- Stage 1: eGFR >=90 with evidence of kidney damage;
- Stage 2: eGFR 60–89 with evidence of kidney damage;
- Stage 3A: 45–59;
- Stage 3B: 30–44;
- Stage 4: 15–29;
- Stage 5: <15;
- Stage 5D: <15 on dialysis.

This staging is adapted from KDIGO 2012.

The existing application's international G categories remain useful and
must not be silently relabelled as the SUS PCDT staging system.

## 6. Albuminuria / RAC

The current PCDT renders:

- A1: <30 mg/g;
- A2: 30–299 mg/g;
- A3: >300 mg/g.

This textual representation does not assign exactly 300 mg/g.

The existing application uses the current international rule in which
300 mg/g remains A2 and A3 begins above 300 mg/g.

BH2 must not introduce an artificial discontinuity at exactly
300 mg/g merely to reproduce an apparent table-boundary ambiguity.

## 7. CKD definition

The PCDT requires chronic kidney abnormality for at least three months.

For eGFR >=60 mL/min/1.73 m², a marker of kidney damage is required.

The existing fail-closed chronicity logic is therefore broadly aligned
with the national diagnostic framework.

## 8. Acute kidney injury

The current Ministry DRC care pathway explicitly instructs clinicians
to apply KDIGO 2012 classification when information is available.

The existing AKI engine already uses KDIGO 2012 as its primary
international source.

BH2 therefore requires Brazilian provenance/context metadata for AKI,
not a second numerical AKI algorithm.

## 9. BH2 implementation decision

BH2B must implement three clearly separated concepts:

### Current clinical calculation

`CKD-EPI 2021 race-free`

- current international calculation;
- also aligned with SBN/SBPC-ML 2024;
- remains the default eGFR calculation.

### SUS national policy context

`PCDT DRC 2024 / annex 2025`

- national SUS provenance;
- SUS staging and policy interpretation available separately;
- PCDT's printed 2009/race-dependent equation must not silently
  replace the default calculation.

### AKI

`KDIGO 2012 + Ministry of Health provenance`

- one numerical engine;
- dual international/Brazil provenance.

## 10. Release rule

BH2 cannot be marked PASS until:

- Brazil/SUS and SBN/SBPC provenance are visible;
- no race is inferred;
- the existing 2021 result remains unchanged;
- SUS staging/context is distinguishable from KDIGO 2024;
- exact boundary behavior is regression tested;
- PT-BR and EN-GB explain the divergence;
- offline behavior matches the API.

## 11. BH2 implementation result

BH2 implements a dual-view renal model:

- **CKD-EPI 2021 race-free** remains the default eGFR calculation and
  is aligned with the SBN/SBPC-ML Brazilian consensus and its 2025
  erratum.
- **KDIGO 2024** remains the international G/A classification layer.
- **SUS PCDT DRC 2024/2025** is presented separately as national policy
  and staging context.
- The printed PCDT race-containing equation is **not executed** because
  its verified source conflicts remain unresolved.
- No race or ancestry field is accepted, derived or inferred.
- Exactly 300 mg/g remains A2 internationally while the PCDT context
  explicitly reports its textual boundary ambiguity without inventing
  a national A category.
- The existing KDIGO-2012 AKI algorithm is retained unchanged and now
  exposes Ministry of Health provenance.

Brazil renal harmonization status: **PASS**.
