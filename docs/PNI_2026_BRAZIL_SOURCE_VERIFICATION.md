# Brazil 2026 PNI vaccination — source verification

Review date: 2026-09-11

Implementation state: source review complete; implementation pending.

## Authority

The Brazil-primary authority for Item 8 is the Ministério da Saúde,
Secretaria de Vigilância em Saúde e Ambiente, Departamento do Programa
Nacional de Imunizações (DPNI).

The 2026 Instrução Normativa do Calendário Nacional de Vacinação is the
national baseline. The baseline contains 21 vaccines and covers the life
course from pregnancy through older age.

The engine must also review later 2026 DPNI technical notes,
rectifications and implementation guides because vaccine-specific rules
can change during the year.

## Required engine architecture

This feature must be a history-aware and effective-date-aware rule
engine.

It must NOT be implemented as a simple age-to-vaccine lookup.

A definitive due/not-due recommendation may require:

- assessment date;
- chronological age;
- prior vaccine doses and dates;
- vaccine/product history where transition rules require it;
- pregnancy and gestational week;
- occupational context;
- explicitly supplied special clinical conditions;
- geography or epidemiologic context when the recommendation is
  location/outbreak specific.

Routine, campaign/rescue, outbreak/blocking, and RIE/CRIE special
recommendations must remain separate.

## 2026 change-control examples

### Pneumococcal VPC20 transition

The national transition from VPC10 toward VPC20 began during 2026.
Therefore the application must not freeze the January baseline and
pretend it applies unchanged to every date in 2026.

Historical dose/product information must be retained when a transition
rule depends on it.

### HPV

Routine HPV vaccination for the ordinary calendar remains distinct from
the time-limited 2026 rescue strategy for previously unvaccinated
adolescents/young people aged 15–19.

The rescue strategy must not be relabelled as the routine age domain.

### Influenza

The routine national calendar groups must remain separate from the
broader priority groups included in the seasonal 2026 vaccination
strategy.

### Pregnancy

Gestational age is a first-class clinical input where the national rule
depends on gestational week.

Examples include dTpa from the 20th gestational week and maternal RSV
vaccination from the 28th gestational week.

## Durable source boundaries

### PNI-SOURCE-FRESHNESS-01

PNI rules can change during the same calendar year.

Software rule: carry assessment/source dates and repeat an authoritative
freshness review before final v2 qualification.

### PNI-HISTORY-02

Many recommendations depend on documented prior doses.

Software rule: never derive a definitive due/not-due list from age alone
when vaccination history is required.

### PNI-UNKNOWN-HISTORY-03

Unknown history is not automatically equivalent to zero documented
doses.

Software rule: preserve unknown as a distinct state.

### PNI-ROUTINE-STRATEGY-04

Routine calendar, seasonal campaign, rescue strategy and outbreak
actions are different layers.

Software rule: never collapse them into one unlabeled recommendation.

### PNI-SPECIAL-CONDITION-05

RIE/CRIE indications are a separate clinical pathway.

Software rule: require explicit clinical context and identify the source
layer.

### PNI-INTERVALS-06

Recommended intervals and exceptional minimum intervals are not the
same.

Software rule: preserve and label both separately.

### PNI-EFFECTIVE-DATE-07

The 2026 VPC20 transition proves that vaccine rules can change inside
the calendar year.

Software rule: apply effective-date-aware vaccine-specific rules.

### PNI-HPV-RESCUE-08

Routine HPV age eligibility and the 2026 15–19 rescue strategy are
distinct.

Software rule: do not universalize the rescue strategy.

### PNI-INFLUENZA-LAYERS-09

Routine influenza eligibility and broader seasonal priority groups are
distinct.

Software rule: return them as separate recommendation layers.

### PNI-PREGNANCY-CONTEXT-10

Some pregnancy recommendations depend on gestational week and repeat
for each pregnancy.

Software rule: require explicit pregnancy context where applicable.

### PNI-LOCAL-EPIDEMIOLOGY-11

Some vaccination actions are geographically or epidemiologically
restricted.

Software rule: never convert local/outbreak guidance into a generic
national routine recommendation.

### PNI-NO-SYNTHETIC-SCORE-12

The PNI does not define one universal numerical vaccination score for
this application.

Software rule: do not invent a synthetic vaccination-completeness or
risk score.

## Next implementation stage

BH8B should design the normalized vaccine-history and rule-result data
model before implementing individual vaccine rules.
