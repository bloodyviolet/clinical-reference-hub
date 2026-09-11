# v2 Brazil Retrospective Clinical Audit — Items 1–6

Review date: 2026-09-11

## Executive disposition

| Item | Feature | Brazil status | Remediation |
|---|---|---|---|
| 1 | NEWS2 | Validated Brazilian adaptation | PASS |
| 2 | Renal | National SUS variant | Critical |
| 3 | Hemodynamics | Context-specific Brazilian guidance | Required |
| 4 | Oxygenation | No national generic variant identified | Metadata/source update |
| 5 | Acid-base/metabolic | Context-specific national toxicology guidance | Required |
| 6 | WHO/SISVAN growth | National standard integrated | PASS |

## Item 1 — NEWS2

The Brazilian Portuguese NEWS2 should no longer be described merely as
a local translation.

A peer-reviewed Brazilian transcultural adaptation:

- was authorised by the Royal College of Physicians before adaptation;
- was reviewed by Brazilian physicians and nurses;
- obtained a mean content-validity index of 0.98;
- was returned to the RCP;
- received RCP approval and publication authorisation.

Disposition — BH1 completed:

- original NEWS2 numerical model retained unchanged;
- PT-BR metadata upgraded to `validated_translation`;
- core PT-BR interface terminology harmonized with the validated
  Brazilian adaptation;
- Brazil-specific provenance is exposed separately from the canonical
  RCP source;
- no national SUS mandate is claimed;
- the current RCP translated-material requirement remains a separate
  final-release compliance gate.

Status: PASS.

## Item 2 — Renal

This is the largest retrospective divergence.

The national PCDT approved by Portaria Conjunta SAES/SECTICS nº 11/2024
states that it is national and must be used by SUS managers.

The PCDT:

- recommends CKD-EPI;
- presents an equation adapted from Levey et al. 2009;
- uses CKD staging and albuminuria categories adapted from KDIGO 2012.

The current application instead uses:

- race-free CKD-EPI 2021;
- KDIGO CKD 2024.

These must coexist rather than one silently replacing the other.

The Ministry's DRC line of care also explicitly applies KDIGO 2012 to
acute kidney injury, supporting the current AKI numerical basis.

Disposition:

- international_current = retain existing implementation;
- brazil_sus = add current PCDT view;
- do not silently infer demographic coefficients;
- independently QC the official PCDT formula before coding.

## Item 3 — Hemodynamics

No universal Brazilian cutoffs should be attached to generic MAP, pulse
pressure, Shock Index or Modified Shock Index.

Brazilian official guidance contains context-specific uses:

- septic shock uses a MAP target around 65 mmHg;
- Ministry obstetric material uses Shock Index >0.9 as an obstetric
  haemorrhage escalation signal.

Disposition:

- preserve neutral base calculations;
- add context-specific Brazilian interpretation;
- never convert obstetric/sepsis thresholds into universal ranges;
- no Brazilian universal MSI cutoff has been established by this audit.

## Item 4 — Oxygenation

The audit identified current Ministry respiratory-severity guidance,
including SpO2-based severity criteria, but did not identify a current
national general-purpose Brazilian replacement for P/F or S/F
calculation.

Disposition:

- retain current P/F and S/F formulas;
- retain prohibition on automatic ARDS diagnosis/staging;
- record Brazil audit metadata;
- do not state that the Global ARDS Definition 2023 is formally adopted
  by SUS unless a national source explicitly establishes that;
- repeat the search at final release freeze.

## Item 5 — Acid-base / metabolic

The Ministry's 2025 methanol pathway is clinically important but
context-specific.

It defines a toxicology workflow with:

- anion gap including potassium;
- protocol-specific calculated osmolality;
- osmolar gap;
- methanol-specific diagnostic/prognostic thresholds.

Those formulas must not silently replace the general metabolic
calculator.

Disposition:

- preserve the existing general acid-base toolkit;
- add a separately identified Ministry methanol/toxic-alcohol context;
- require measured osmolality for osmolar-gap calculation;
- preserve source/version provenance;
- do not infer methanol poisoning from a calculated gap alone.

## Item 6 — WHO/SISVAN growth

PASS.

The existing implementation already separates:

- WHO 2006/2007 numerical references;
- Brazilian Ministry/SISVAN interpretation;
- prematurity/corrected-age guidance;
- Brazilian head-circumference monitoring context;
- source and redistribution provenance.

Only final pre-release source-freshness recheck remains.

## Item 7 block

Item 7 must not begin from STEADI alone.

Before implementation, review the current Brazilian Ministry framework
for older adults, including IVCF-20 and current e-SUS APS guidance, and
determine how STEADI functional tests should coexist as complementary
assessments.

## v2 release gate

Items 1–5 remain clinically accepted as development checkpoints but are
not Brazil-harmonization-complete.

v2.0.0 cannot proceed to final qualification until each remediation
listed above is completed and independently QC'd.
