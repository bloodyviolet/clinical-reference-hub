# Metabolic / acid-base — Brazilian source verification

Clinical review: 2026-09-11

## Disposition

The current general acid-base/metabolic calculator remains clinically
valid and must **not** be replaced by the Ministry methanol formulas.

Brazilian federal guidance defines a separate, toxicology-specific
workflow for suspected methanol poisoning.

BH5 therefore requires a **context layer**, not replacement of the
generic engine.

## 1. Current generic application

The existing generic application uses:

- anion gap:
  `Na - (Cl + HCO3)` — potassium excluded;
- albumin correction:
  `AG + 2.5 * (4 - albumin)`;
- calculated osmolality:
  `2*Na + glucose/18 + BUN/2.8`;
- corrected sodium factor 1.6;
- Winter:
  `1.5*HCO3 + 8 ±2`;
- delta ratio only after explicit metabolic-acidosis confirmation.

The application does not automatically infer the primary acid-base
disorder.

All of these properties must remain unchanged.

## 2. Current federal methanol clinical guidance

### Nota Técnica Conjunta nº 376/2025

The current reviewed Ministry joint note is:

**Nota Técnica Conjunta nº 376/2025-SVSA/SAES/SECTICS/MS**

It explicitly replaces Ministry Notes 360 and 365.

It directs assessment with:

- arterial blood gas;
- serum electrolytes;
- measured serum osmolality;
- osmolar-gap calculation;
- anion-gap calculation;
- methanol concentration when available.

The note treats the Ministry methanol flowchart as a complementary
clinical instrument.

### Ministry / SAES methanol flowchart

The Ministry flowchart:

**Manejo da intoxicação por metanol pelo consumo de bebidas alcoólicas
adulteradas**

contains toxicology-specific formulae and thresholds.

These apply only to suspected methanol poisoning.

## 3. Toxicology anion-gap formula

The Ministry toxicology table uses:

`AG = (Na + K) - (HCO3 + Cl)`

with the formula expressed in mmol/L.

This differs deliberately from the generic application formula:

`AG = Na - (Cl + HCO3)`

The generic formula must not be changed.

The Ministry potassium-inclusive formula may only be calculated in an
explicitly selected methanol/toxicology context.

## 4. Osmolar gap and calculated osmolality

The Ministry workflow defines:

`osmolar gap = measured osmolality - calculated osmolality`

Therefore measured osmolality is mandatory for an osmolar-gap result.

The Ministry flowchart's calculated-osmolality table uses the
toxicology-specific mmol/L convention:

`(glucose + urea + (1.86 × sodium)) / 0.93`

This must remain isolated from the generic application formula:

`2*Na + glucose/18 + BUN/2.8`

The two input models must never be silently mixed.

In particular:

- **urea is not BUN**;
- mmol/L glucose must not be treated as mg/dL glucose;
- mg/dL BUN must not be passed into a formula expecting mmol/L urea.

## 5. Contextual methanol thresholds

The Ministry flowchart includes context-specific guidance such as:

- anion gap >12 mEq/L in its presumptive diagnostic workflow;
- osmolar gap >10 mOsm/kg as suspicious;
- osmolar gap >25 mOsm/kg as strongly suggestive;
- normal osmolar gap does not exclude a later presentation;
- severe acid-base abnormalities are also used in escalation and
  haemodialysis criteria.

These are **toxicology workflow thresholds**.

They are not universal acid-base reference ranges and must never be
applied automatically by the general metabolic calculator.

## 6. Diagnosis safety rule

The software must not diagnose or infer methanol poisoning from a gap
calculation alone.

A future BH5 implementation must require explicit selection of the
methanol/toxicology context.

Its output must state that history, clinical findings, timing,
laboratory data, direct methanol measurement when available, and CIATox
support remain relevant to management.

## 7. Durable implementation conflicts

### MET-AG-K-01 — critical

Generic AG excludes potassium.

Ministry methanol AG includes potassium.

Neither formula may silently overwrite the other.

### MET-OSM-UNIT-02 — critical

Generic osmolality uses glucose and BUN in mg/dL.

The Ministry toxicology table uses mmol/L variables and urea.

No silent unit or urea/BUN substitution is permitted.

### MET-GO-MEASURED-03 — critical

Osmolar gap requires measured osmolality.

The calculation must fail closed without it.

### MET-DX-CONTEXT-04 — critical

Methanol thresholds are contextual clinical guidance.

The software must not infer poisoning solely from numerical gaps.

## 8. BH5 implementation requirement

BH5B may add a separately identified Brazilian methanol/toxicology
context while preserving every generic metabolic formula unchanged.

BH5 cannot be marked PASS until:

- generic AG remains potassium-free;
- generic osmolality remains unchanged;
- Winter/delta/corrected-sodium/albumin correction remain unchanged;
- toxicology mode is explicit rather than inferred;
- potassium is explicit where required;
- measured osmolality is required for osmolar gap;
- urea and BUN are never silently conflated;
- unit handling is explicit;
- methanol thresholds remain contextual;
- no automatic methanol diagnosis occurs;
- Python/API/browser/offline parity passes in PT-BR and EN-GB.

## 9. BH5 implementation result

BH5 preserves the general metabolic toolkit and implements the
Brazilian Ministry methanol workflow as a separate, explicitly selected
toxicology context.

### General toolkit

The following remain unchanged:

- potassium-free anion gap;
- albumin correction;
- generic calculated osmolality using glucose and BUN in mg/dL;
- corrected sodium;
- Winter compensation;
- delta ratio and its explicit metabolic-acidosis gate.

### Methanol context

The separate Ministry context requires explicit user confirmation.

Its formula domain is isolated:

- sodium, potassium, chloride and bicarbonate in mmol/L;
- glucose in mmol/L;
- urea in mmol/L;
- measured osmolality in mOsm/kg.

Urea is not BUN.

Measured osmolality is mandatory before an osmolar gap is produced.

The Ministry >10 and >25 osmolar-gap thresholds are displayed only as
contextual toxicology guidance.

Exactly 10 or 25 does not satisfy those strict operators.

No numerical gap result diagnoses methanol poisoning and no toxicology
context is inferred automatically.

Brazil metabolic harmonization status: **PASS**.
