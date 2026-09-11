# Oxygenation — Brazilian source verification

Clinical review: 2026-09-11

## Disposition

No general Brazilian replacement formula was identified for:

- P/F = PaO2 / FiO2 fraction; or
- S/F = SpO2 / FiO2 fraction.

BH4 therefore does **not** require a numerical change to the oxygenation
engine.

The Brazilian remediation is source/provenance related.

## 1. International reference

The current application references the Global ARDS Definition.

Its oxygenation framework includes:

- P/F <=300 mmHg; and
- S/F <=315 when SpO2 <=97%.

Those are components of an ARDS definition, not a stand-alone ARDS
diagnosis.

The existing application therefore correctly keeps:

`ards_classification_applied = false`

The existing S/F caution above SpO2 97% must also remain.

## 2. Current Brazilian national respiratory-surveillance source

The current reviewed Ministry source is:

**Nota Técnica nº 11/2026-CGCOVID/DEDT/SVSA/MS**

Published: 2026-08-19.

This document states that it updates national surveillance guidance and
supersedes recommendations previously published in the 2024 integrated
Covid-19, influenza and other respiratory-virus surveillance guide and
other previously applicable surveillance documents.

The current national SRAG surveillance case definition includes, in a
hospitalised patient meeting the syndrome definition, at least one
deterioration sign such as:

- dyspnoea;
- tachypnoea; and/or
- room-air SpO2 <=94%.

This is an **epidemiological surveillance case definition**.

It is not:

- a new P/F formula;
- a new S/F formula;
- an ARDS severity classification; or
- evidence that P/F or S/F should be replaced by SpO2 <=94%.

## 3. CONITEC / national protocol review

The current official CONITEC PCDT catalog was reviewed on 2026-09-11
after its September 2026 update.

Within the authoritative Brazilian corpus reviewed for this audit, no
general national replacement calculation was identified for P/F or S/F.

The audit also did not identify an explicit national SUS statement
formally adopting the 2023 Global ARDS Definition as the national
generic ARDS definition.

This is a bounded negative finding:

`no_national_variant_identified`

means that no such variant was identified in the authoritative source
corpus reviewed on the stated date.

It does not claim that no Brazilian publication on P/F, S/F or ARDS can
exist.

## 4. Disease-specific use does not create a generic variant

Brazilian disease-specific or institutional protocols may use P/F
thresholds for management decisions.

That does not alter:

`P/F = PaO2 / FiO2 fraction`

and does not establish a new generic Brazilian oxygenation formula.

Institutional implementation evidence must not be promoted to a
national standard.

## 5. BH4 implementation rule

The oxygenation engine should retain:

- P/F mathematics unchanged;
- S/F mathematics unchanged;
- explicit FiO2 input;
- no estimation of FiO2 from flow or device labels;
- `ards_classification_applied = false`;
- the SpO2 >97% S/F caution;
- the Global ARDS S/F applicability gate.

BH4B should add only:

- current Brazilian applicability metadata;
- Ministry 2026 respiratory-surveillance provenance;
- explicit separation between Brazilian SRAG surveillance and the
  international Global ARDS reference;
- explicit wording that formal SUS adoption of Global ARDS was not
  identified in this audit.

## 6. Release requirement

BH4 cannot be marked PASS until:

- all existing P/F and S/F vectors remain unchanged;
- browser/API/offline numerical parity remains unchanged;
- no ARDS diagnosis or severity is automatically generated;
- SpO2 >97% behavior remains unchanged;
- Brazil metadata is exposed in PT-BR and EN-GB;
- the 2026 Ministry source replaces the older surveillance source in the
  Brazil audit;
- final source freshness is rechecked at v2.0 release freeze.

## 7. BH4 implementation result

BH4 retains the oxygenation engine unchanged and completes the
Brazilian remediation through provenance and applicability metadata.

### Numerical engine

- P/F mathematics are unchanged.
- S/F mathematics are unchanged.
- FiO2 must still be entered explicitly.
- `ards_classification_applied` remains `false`.
- the SpO2 >97% S/F caution remains unchanged.

### Brazilian context

The current Brazilian surveillance provenance is Nota Técnica
nº 11/2026-CGCOVID/DEDT/SVSA/MS.

Its room-air SpO2 <=94% SRAG criterion is treated only as an
epidemiological-surveillance criterion.

It is not injected into P/F or S/F calculation and is not treated as an
ARDS diagnostic or severity threshold.

### International reference

Global ARDS 2023 remains the international reference used to explain
the S/F applicability gate.

This audit did not identify an explicit national SUS adoption statement
establishing Global ARDS 2023 as the generic national Brazilian ARDS
definition.

Brazil oxygenation harmonization status: **PASS**.
