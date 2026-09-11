# Falls / function — Brazilian source verification

Clinical review: 2026-09-11

## Disposition

Item 7 is a Brazil-first feature.

The current national framework is broader than the originally planned
set of STEADI functional tests.

The primary Brazilian layer is:

1. Caderneta Brasileira da Pessoa Idosa 2026;
2. IVCF-20 in the national older-person multidimensional assessment;
3. IVCF-20 integration in e-SUS APS PEC and e-SUS Território.

CDC STEADI TUG, 30-Second Chair Stand, 4-Stage Balance and orthostatic
blood-pressure assessment remain useful complementary assessments, but
must not be presented as national SUS instruments.

## 1. Caderneta Brasileira da Pessoa Idosa 2026

The current Ministry Caderneta was published in June 2026.

It is the current national older-person Caderneta for people aged
60 years or more.

The falls section contains a 12-item yes/no check-up covering domains
such as:

- previous falls;
- walking-aid recommendation;
- gait instability;
- using furniture for support;
- fear/concern about falls;
- use of the hands to rise from a chair;
- curb difficulty;
- urinary urgency;
- reduced foot sensation;
- medication-associated dizziness/fatigue;
- sleep/mood medication;
- depressed mood.

The current Caderneta directs the person to seek assessment when any
item is answered **yes**.

Although the Caderneta identifies this check-up as translated/adapted
from CDC/NCOA material, the current Brazilian presentation does not
provide a weighted score.

Therefore BH7 must not reconstruct a weighted STEADI/NCOA score and
apply it to the Brazilian Caderneta instrument.

## 2. IVCF-20 is the national APS functional framework

IVCF-20 is integrated into e-SUS APS PEC and e-SUS Território.

Current Ministry guidance applies it to people aged 60 years or more
followed by APS.

Current risk strata are:

- 0–6: low clinical-functional vulnerability;
- 7–14: moderate;
- 15–40: high.

Minimum reassessment frequency:

- score 0–6: at least every 12 months;
- score >6: at least every 6 months;
- any score: repeat after an important sentinel event.

Falls are explicitly considered sentinel events.

## 3. IVCF-20 mobility content

Relevant mobility/falls findings include:

- 4-m gait time >5 seconds as one condition within the
  aerobic/muscular-capacity dimension;
- walking difficulty that can prevent an everyday activity;
- two or more falls in the previous year.

These items are not equivalent to a Timed Up and Go test.

No synthetic score combining IVCF-20 with STEADI should be created.

## 4. Current Brazilian blood-pressure context

The 2026 Caderneta provides fields for blood pressure in:

- lying;
- sitting;
- standing positions.

This supports orthostatic assessment in older-person care.

However, the current Caderneta itself does not specify the full STEADI
procedure of five minutes supine followed by standing measurements at
one and three minutes.

BH7 must therefore distinguish:

- current Brazilian older-person BP recording context; from
- the complementary STEADI orthostatic measurement protocol.

## 5. Complementary STEADI assessments

The current CDC STEADI clinical resource set retains:

### Timed Up and Go

- 3-m / 10-ft course;
- regular footwear;
- usual walking aid may be used;
- >=12 seconds indicates increased fall risk in the STEADI tool.

### 30-Second Chair Stand

The test assesses lower-limb strength/endurance.

Below-average cutoffs remain age- and sex-specific.

The current CDC table spans ages 60–94.

If arms are required to stand, the STEADI assessment instructs the
examiner to stop and record zero.

### 4-Stage Balance

Positions progressively increase in difficulty.

A position is progressed after 10 seconds.

Failure to maintain tandem stance for at least 10 seconds indicates
increased fall risk in STEADI.

### Orthostatic blood pressure

STEADI uses:

- 5 minutes lying;
- baseline BP and pulse;
- standing measurements after 1 and 3 minutes.

Abnormal findings are:

- systolic drop >=20 mmHg; or
- diastolic drop >=10 mmHg; or
- lightheadedness/dizziness.

These thresholds must be labelled STEADI/complementary unless a current
Brazilian national source explicitly adopts the same protocol.

## 6. National negative finding

No current generic Brazilian federal cutoff was identified in the
audited corpus for:

- TUG;
- 30-Second Chair Stand;
- 4-Stage Balance.

This is a bounded source-review finding, not a claim that Brazilian
research or local protocols do not exist.

## 7. Durable source boundaries

### FALLS-CHECKLIST-SCORE-01

The Brazilian Caderneta falls check-up is yes/no with an any-yes
assessment rule.

Do not silently import a weighted STEADI/NCOA score.

### FALLS-IVCF-TUG-02

IVCF-20 4-m gait assessment is not TUG.

Keep the instruments independent.

### FALLS-BP-PROTOCOL-03

The 2026 Caderneta records lying/sitting/standing BP but does not itself
define the complete STEADI timing protocol.

Do not relabel STEADI as a current Caderneta rule.

### FALLS-STEADI-NATIONAL-04

TUG, Chair Stand and 4-Stage thresholds were not identified as generic
national SUS cutoffs in the authoritative corpus reviewed.

Label them as complementary international guidance.

## 8. BH7 implementation architecture

BH7B should implement the Brazilian layer first:

- Caderneta 2026 falls check-up;
- IVCF-20;
- functional/falls interpretation and reassessment guidance.

Then add separate complementary STEADI modules:

- TUG;
- 30-Second Chair Stand;
- 4-Stage Balance;
- orthostatic blood pressure.

The application must never merge these instruments into a synthetic
fall-risk score.

PT-BR is primary for Brazilian content.

EN-GB must be complete but identified as an informative translation.

Final Brazilian and CDC source freshness must be rechecked at the
v2.0.0 release freeze.
