# Falls / function — complementary CDC STEADI source verification

Clinical review: 2026-09-11

## Disposition

The Brazil-primary Item 7 implementation is already qualified and
checkpointed separately.

Its national layer remains:

1. Caderneta Brasileira da Pessoa Idosa 2026;
2. IVCF-20.

CDC STEADI assessments may be implemented only as a visibly separate
**complementary international layer**.

They must not replace, alter, or be numerically merged with the
Brazilian national instruments.

## Current CDC resource status

The current CDC STEADI clinical-resources page continues to distribute:

- Timed Up and Go;
- 30-Second Chair Stand;
- 4-Stage Balance;
- Measuring Orthostatic Blood Pressure.

The individual assessment handouts remain the numerical/procedural
source contract used below.

## 1. Timed Up and Go

CDC STEADI TUG:

- assesses mobility;
- uses a 3-m / 10-ft course;
- permits regular footwear;
- permits the person's usual walking aid if needed;
- times stand, walk, turn, return and sit;
- classifies a completion time of **12 seconds or greater** as
  increased fall risk in the STEADI instrument.

TUG must remain distinct from the IVCF-20 4-m gait item.

The IVCF-20 >5-second 4-m gait finding must never be substituted for
the STEADI TUG >=12-second threshold.

## 2. 30-Second Chair Stand

CDC STEADI Chair Stand assesses lower-limb strength and endurance.

The person:

- sits in the middle of a chair without armrests;
- crosses the arms at the wrists against the chest;
- repeatedly rises fully and sits during 30 seconds.

If the arms are required to stand, the assessment instructs the
examiner to stop and record zero.

A repetition that is more than halfway to full standing when time ends
is counted.

The STEADI below-average reference table is:

| Age | Men | Women |
| --- | ---: | ---: |
| 60–64 | <14 | <12 |
| 65–69 | <12 | <11 |
| 70–74 | <12 | <10 |
| 75–79 | <11 | <10 |
| 80–84 | <10 | <9 |
| 85–89 | <8 | <8 |
| 90–94 | <7 | <4 |

The comparison is **strictly less than** the displayed threshold.

A result exactly equal to a threshold is therefore not below average.

The published STEADI table stops at age 94.

The software must not invent or extrapolate a reference cutoff for
people older than 94. For such patients, the raw test result can be
recorded, but a STEADI age/sex below-average classification must not be
generated from this table.

## 3. 4-Stage Balance

CDC STEADI 4-Stage Balance assesses static balance.

The four positions are:

1. feet side-by-side;
2. instep of one foot touching the other foot's big toe;
3. tandem heel-to-toe;
4. one-leg stand.

Each position is targeted for 10 seconds.

The examiner progresses only when the current position can be held for
10 seconds without moving the feet or requiring support.

If a position cannot be held, the test stops.

The CDC handout states that an assistive device is not used during this
test and the eyes remain open.

Failure to hold tandem stance for at least 10 seconds indicates
increased fall risk in the STEADI assessment.

The TUG walking-aid rule must not be copied into this test.

## 4. Orthostatic blood pressure

CDC STEADI specifies:

1. lie down for 5 minutes;
2. measure blood pressure and pulse;
3. stand;
4. repeat blood pressure and pulse after 1 minute;
5. repeat after 3 minutes.

STEADI considers the assessment abnormal when any of the following is
present:

- systolic blood-pressure drop >=20 mmHg;
- diastolic blood-pressure drop >=10 mmHg;
- lightheadedness or dizziness.

This is a complementary STEADI protocol.

The Brazilian 2026 Caderneta records lying, sitting and standing blood
pressure but does not itself establish this full STEADI timing and
20/10-mmHg interpretation as a national numeric protocol.

## 5. Brazil boundary

No current generic Brazilian federal cutoff was identified in the
authoritative source review for:

- TUG;
- 30-Second Chair Stand;
- 4-Stage Balance.

This remains a bounded negative source finding.

It does not mean that no Brazilian study, local service protocol or
institution-specific implementation exists.

It means these CDC thresholds must not be represented in this
application as a national SUS standard without a new authoritative
federal source.

## 6. Instrument independence

The application must preserve all of the following as separate
assessments:

- Caderneta 2026 falls check-up;
- IVCF-20;
- STEADI TUG;
- STEADI 30-Second Chair Stand;
- STEADI 4-Stage Balance;
- STEADI orthostatic blood pressure.

No synthetic total may combine them.

No result from one instrument may automatically populate or classify
another.

## 7. Durable boundaries

### STEADI-BRAZIL-LAYER-01

STEADI is complementary international guidance.

Do not promote it above or replace the Brazilian national layer.

### STEADI-SYNTHETIC-SCORE-02

Do not sum or merge independent instruments into a synthetic falls
score.

### STEADI-TUG-IVCF-03

IVCF-20 4-m gait is not TUG.

### STEADI-CHAIR-AGE-04

Do not extrapolate Chair Stand reference cutoffs beyond age 94.

### STEADI-CHAIR-STRICT-05

Chair Stand below-average classification is strictly `<` the published
age/sex threshold.

### STEADI-BALANCE-DEVICE-06

Do not allow a walking aid during 4-Stage Balance simply because TUG
allows the usual aid.

### STEADI-BP-BRAZIL-07

Do not label the complete STEADI orthostatic timing/cutoff protocol as
a current Brazilian Caderneta/SUS rule.

## Implementation gate

This tranche approves source/governance only.

No STEADI calculation engine, API endpoint, schema, UI form or PWA
change is authorised until this source contract passes automated
qualification.

CDC and Brazilian source freshness must be rechecked again at the
v2.0.0 release freeze.
