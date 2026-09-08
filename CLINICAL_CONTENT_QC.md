# Clinical Content QC — Pass 2

**Review date:** 2026-09-07  
**Scope:** first systematic stale-content/safety/provenance sweep of the public-health policy dataset.

This review distinguishes two levels of confidence:

1. **Row-specific current override source** — the row was specifically checked against a current implementation/guideline/legal source.
2. **Policy-level provenance** — the row is linked to the governing/base policy and screened for obvious stale or unsafe wording, but exact page/article-level verification remains pending.

The database records that distinction in `review_notes`.

## Row-specific current-source corrections

| Area | Correction | Current source |
|---|---|---|
| PNAISH — prostate | Explicitly states that population screening with PSA/DRE in asymptomatic men is not recommended; diagnosis of symptomatic disease and shared decision-making are distinguished from screening. | INCA/MS: https://www.gov.br/inca/pt-br/assuntos/cancer/tipos/prostata/versao-para-profissionais-de-saude |
| PNAB — multiprofessional APS | Replaced current-use `NASF` wording with `eMulti`. | Portaria GM/MS nº 635/2023: https://bvsms.saude.gov.br/bvs/saudelegis/gm/2023/prt0635_22_05_2023.html |
| PNAISC — breastfeeding | Updated to exclusive breastfeeding through 6 months and continued breastfeeding to 2 years or more with complementary feeding from 6 months. | MS: https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/a/aleitamento-materno |
| PNAISC — neonatal screening | Corrected screening timing instead of using one blanket “before discharge/first week” rule. | MS: https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-crianca/cuidado-neonatal |
| PNSPI — IVCF-20 | Tied the tool to current multidimensional-assessment implementation/e-SUS APS rather than presenting it as if it were in the original 2006 policy text. | MS: https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-pessoa-idosa |
| PNAISM — Rede Alyne | Current Rede Alyne terminology and prenatal organization retained; old Rede Cegonha/RAMI wording removed. | Consolidated regulation/current amendments: https://bvsms.saude.gov.br/bvs/saudelegis/gm/2026/prt10273_27_02_2026.html |
| PNAISM — breast screening | 50–74 years, biennial population screening. | INCA: https://www.gov.br/inca/pt-br/assuntos/gestor-e-profissional-de-saude/controle-do-cancer-de-mama/acoes/deteccao-precoce |
| PNAISM — cervical screening | Primary oncogenic DNA-HPV screening, 25–64 years, 5-year interval after a negative result; cytology alternative where DNA-HPV is unavailable. | MS 2025 guideline: https://www.gov.br/saude/pt-br/assuntos/pcdt/r/rastreamento-cancer-do-colo-do-utero/view |
| PNAISM — incarcerated women | Replaced overbroad restraint wording with federal childbirth/immediate-puerperium protections. | Lei nº 13.434/2017: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13434.htm |

## Broad wording corrections

- `DST` terminology replaced by `IST`.
- PNAISM climacteric hormone therapy changed from blanket availability/treatment language to individualized indication with risk/benefit/contraindication assessment.
- PNAISM sickle-cell wording no longer implies universal electrophoresis based on race.
- PNAISM lesbian/bisexual care avoids assuming sexual practices based on orientation.
- PNSTT mental-health rows no longer infer occupational causality solely from exposure history.
- PNSTT reporting/CAT language no longer hard-codes a single legal/administrative pathway.
- PNSIPN removed old 2012 percentages and reframed rows around inequity monitoring, access and appropriate clinical diagnosis rather than race as a diagnostic proxy.

## Automated stale-content checks

The seeded dataset is automatically rejected/flagged for several known defects. Current scan has zero hits for:

- `[cite:` raw placeholders
- `Rede Cegonha`
- `RAMI`
- `NASF`
- `DST` / `DSTs`
- old cervical `25 a 59`
- stale `77%` homicide statistic
- stale `6,3` external-cause ratio
- stale `60% das mortes maternas` statistic
- old `Programa de Anemia Falciforme` wording

## What this pass does *not* certify

At the end of **Pass 2**, this review did **not** claim that every sentence in every policy row had a pinpoint locator; 45 rows still carried policy-level provenance at that stage. **Pass 3 supersedes that state** by adding evidence tiers and locators to all 54 rows, while preserving a `policy_context` tier for summaries that are not explicit standalone directives.

The policy provenance work still does not transform summarized guidance into verbatim regulatory text or replace reading the complete source. The 277 NANDA/NIC/NOC mappings also remain a separate semantic/licensing workstream.


---

## Pass 3 provenance update

Pass 3 replaces the earlier two-level confidence model with four machine-readable evidence tiers:

- `current_override`: current implementation/guideline/legal source specifically checked for that row.
- `pinpoint_policy`: a supporting article/page/section has been identified in the base policy.
- `policy_context`: clinically useful equity/context interpretation, but not an explicit standalone directive in the base policy.
- `policy_level`: generic policy provenance only.

Current distribution across 54 policy rows is **10 current_override / 40 pinpoint_policy / 4 policy_context / 0 policy_level**. See `POLICY_PROVENANCE_QC.md` for the row-by-row locator index.

The legal-interruption row was also rewritten during this pass: it now describes humanized care and access to interruption in the situations provided by law, and states the current Ministry rule that access to sexual-violence health services does not depend on presentation of a police report. It no longer names AMIU/curettage as though one technique were universally required.

The NANDA/NIC/NOC workstream remains separately tracked. Pass 4 reconciles all 277 diagnosis identifiers against NANDA-I 2024–2026, sources the Portuguese diagnosis labels from the current detailed records, and rebuilds a primary NIC 8th / NOC 7th mapping with per-row confidence, rationale and reference. These are **curated current-edition mappings, not an official INKA/Iowa crosswalk**. See `SAE_MAPPING_QC.md` and `LICENSING_REVIEW.md` for the exact validation boundary.
