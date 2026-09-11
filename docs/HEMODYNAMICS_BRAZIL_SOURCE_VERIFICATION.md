# Hemodynamics — Brazilian source verification

Clinical review: 2026-09-11

## Disposition

The generic hemodynamic calculator remains numerically neutral.

No Brazilian universal adult cutoff was identified for:

- mean arterial pressure (MAP/PAM);
- Shock Index;
- Modified Shock Index; or
- pulse pressure.

Brazilian authoritative material does contain clinically important
**context-specific** thresholds.

These must not be converted into universal classifications.

## 1. Existing generic calculations

The current application calculates:

- pulse pressure = SBP - DBP;
- approximate MAP = DBP + 1/3(SBP - DBP);
- Shock Index = HR / SBP;
- Modified Shock Index = HR / MAP.

BH3 does not change these formulae.

The current application also explicitly reports:

`threshold_classification_applied = false`

That safety property must remain true for the generic calculation.

## 2. Septic-shock MAP context

Brazilian federal guidance uses a MAP around 65 mmHg in the specific
clinical context of septic shock.

The Ministry of Health **Manual de Gestação de Alto Risco** presents
septic shock after adequate volume resuscitation as requiring
vasopressors to maintain:

`PAM >= 65 mmHg`

with lactate above 2 mmol/L.

Federal supplementary-health sepsis guidance from ANS also uses the
approximately 65 mmHg MAP threshold in septic-shock management.

### Software interpretation

This supports a **septic-shock context note**.

It does not support labelling MAP below 65 mmHg as universally
"abnormal" in every patient or clinical scenario.

## 3. Obstetric-haemorrhage Shock Index context

The Ministry of Health publication:

**Linha de Cuidados para Doença Trofoblástica Gestacional**

defines Shock Index as:

`heart rate / systolic blood pressure`

and states that values **above 0.9** should trigger the obstetric
haemorrhage protocol in its bleeding context.

Current EBSERH postpartum-haemorrhage protocols independently use a
Shock Index around/at 0.9 as an escalation marker.

EBSERH evidence is treated as implementation corroboration, not as a
national standard.

### Software interpretation

The obstetric threshold may be exposed only when the clinical context
is explicitly identified as obstetric haemorrhage.

It must not become the generic adult Shock Index cutoff.

## 4. Modified Shock Index

No authoritative Brazilian universal MSI threshold was identified in
the reviewed national/federal source set.

BH3 must not invent one.

## 5. Pulse pressure

No authoritative Brazilian universal pulse-pressure threshold suitable
for this generic calculator was identified.

BH3 must not invent one.

## 6. BH3 implementation rule

BH3 may provide optional context-specific Brazilian guidance while
preserving the generic result.

The intended model is:

### Generic haemodynamics

- MAP / pulse pressure / SI / MSI mathematics unchanged;
- no universal threshold classification.

### Septic-shock context

- informational Brazilian MAP target around 65 mmHg;
- explicitly labelled as septic-shock guidance.

### Obstetric-haemorrhage context

- informational Brazilian Shock Index >0.9 escalation signal;
- explicitly labelled as obstetric-haemorrhage guidance.

The contextual guidance must never be silently applied to patients for
whom that clinical context was not selected.

## 7. Release requirement

BH3 cannot be marked PASS until:

- base numerical vectors remain unchanged;
- generic `threshold_classification_applied` remains false;
- Brazilian contexts are visibly separated from generic results;
- MAP 65 is not promoted to a universal threshold;
- SI 0.9 is not promoted to a universal threshold;
- no MSI cutoff is invented;
- no pulse-pressure cutoff is invented;
- PT-BR and EN-GB are complete;
- browser/API/offline behavior is concordant.

## 8. BH3 implementation result

BH3 preserves the generic haemodynamic calculator and adds optional,
explicitly selected Brazilian clinical contexts.

### Generic calculation

- MAP, pulse pressure, Shock Index and Modified Shock Index mathematics
  are unchanged.
- `threshold_classification_applied` remains `false`.
- no clinical context is inferred automatically.

### Septic shock

When and only when `septic_shock` is explicitly selected, the result
displays the Brazilian contextual MAP reference of >=65 mmHg.

This does not create a universal MAP classification.

### Obstetric haemorrhage

When and only when `obstetric_hemorrhage` is explicitly selected, the
result displays the Ministry Shock Index trigger of >0.9.

Exactly 0.9 does not satisfy this strict Ministry trigger.

This does not create a universal Shock Index classification.

### Other indices

No Brazilian universal threshold is introduced for Modified Shock
Index or pulse pressure.

Brazil hemodynamics harmonization status: **PASS**.
