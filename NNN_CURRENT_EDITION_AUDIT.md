# NANDA-I / NIC / NOC Current-Edition Audit — Pass 5

Review date: **2026-09-07**

## Scope

This pass validates and restructures the project's NANDA-I → NIC → NOC mapping layer against the current classification baseline used by the institution:

- **NANDA-I 2024–2026, 13th edition**
- **NIC, 8th edition**
- **NOC, 7th edition**

The deployed language pair remains **English (UK / en-GB)** plus **Portuguese (Brazil / pt-BR)**. The supplied NIC/NOC source books are Spanish-language licensed reference copies. Canonical classification identifiers are language-independent; short display labels are rendered locally in en-GB and pt-BR.

## Licensed source material used

The audit used the institutionally supplied Spanish NIC 8 and NOC 7 PDFs as licensed source material. Their source hashes and page counts are recorded in `data/nnn_source_manifest.json`; the source books themselves are **not copied into the deployment package**.

- NIC source SHA-256: `03db2ae5ea5e8eec1a442b6279a9b7fe2ea80dd76eeb8d3ff8d717b9c3b633b3`
- NOC source SHA-256: `2098d3bdf335d8e4559460547791ff2fc1b3d256c262b8af5151b853e2bdb46b`

The NIC source's “Cómo encontrar una intervención” section describes several valid ways of finding/selecting interventions rather than defining one universal intervention per diagnosis. The NOC source likewise describes outcome selection as dependent on the diagnosis/problem, the patient or population, preferences, care context and available resources. That source guidance is the reason Pass 5 no longer models every diagnosis as if exactly one NIC and one NOC were universally correct.

For reproducible code/short-label reconciliation, the project also records the current NIC 8 and NOC 7 classification-list references in the source manifest. Those list references supplement the licensed books; they do **not** substitute for the licensed definitions, activities, indicators or measurement scales.

## Data-model correction: primary compatibility pair + contextual alternatives

Pass 4 still had one structural weakness: each NANDA-I diagnosis exposed only one NIC and one NOC pair. Even a clinically sensible pair can become misleading when the appropriate choice changes with:

- antenatal / intrapartum / postpartum phase;
- infant/child/adolescent developmental age;
- substance involved in withdrawal;
- established problem versus prevention/risk state;
- individual versus family/community care context;
- the specific physiologic consequence being monitored.

Migration `0005` adds `sae_classification_links`, a one-to-many classification-link table. The legacy primary NIC/NOC columns remain for backward compatibility, while the new API returns all contextual links.

### Current link counts

- NANDA-I diagnoses: **277**
- Compatibility primary links: **554** (one NIC + one NOC per diagnosis)
- Contextual alternative links: **73**
- Total NNN classification links: **627**
- Diagnoses with at least one contextual alternative: **26**
- Primary mapping confidence: **229 high / 48 moderate**
- Distinct primary NIC codes: **110**
- Distinct primary NOC codes: **115**
- Distinct NIC codes represented across all links: **120**
- Distinct NOC codes represented across all links: **136**

The primary pair is now explicitly a **compatibility primary**, not a declaration that alternatives are clinically inferior or invalid.

## Current-edition corrections made in Pass 5

The source/code review corrected several concrete legacy/current-edition mismatches:

- Legacy NIC `1054` **Breastfeeding Assistance** is no longer used; current mapping uses NIC `5244` **Breastfeeding Counselling** where appropriate.
- Legacy NIC `6780` **Pregnancy Monitoring** is no longer used; pregnancy mappings now use current phase-specific codes such as `6960` **Prenatal Care**, `6800` **High-Risk Pregnancy Care**, `6830` **Intrapartum Care**, `6834` **Intrapartum Care: High-Risk Delivery**, and `6930` **Postpartum Care**.
- NIC `8274` is treated with its current NIC 8 label **Child Care**, rather than the older developmental-enhancement label.
- NOC `1050` **Gastrointestinal Function** was corrected to current NOC `1015`.
- NOC `0414` is **Cardiopulmonary Function**.
- NOC `1613` is **Self-Management of Care**.
- NOC `2509` is **Maternal Status: Antepartum**; `2510` and `2511` are exposed as intrapartum/postpartum contextual alternatives where relevant.
- NOC `2700` is **Social Competence**, not a community-coping outcome; community coping/resilience now primarily uses `2704` **Community Resilience**, with `2701` **Community Health Status** as a contextual alternative where appropriate.
- Thrombosis risk uses NOC `1932` **Risk Control: Thrombus** rather than generic risk control as the primary outcome.
- Autonomic dysreflexia uses NOC `0910` **Neurological Function: Autonomic**.
- Ineffective impulse control uses NOC `1405` **Self-Control of Impulses**.
- Acute drug withdrawal uses NIC `4514` **Substance Use Treatment: Drug Withdrawal** with NOC `2108` **Substance Withdrawal Severity**; alcohol-specific and longer-term alternatives are exposed contextually.
- Elopement risk uses NOC `1920` **Elopement Risk**.
- Cardiovascular risk uses NIC `4050` **Cardiac Risk Management** with NOC `1914` **Risk Control: Cardiovascular Disease**.
- Perioperative positioning risk uses NOC `0204` **Immobility Consequences: Physiological** as a conservative compatibility outcome and remains moderate confidence.
- SIDS-risk mapping uses NOC `1947` **Safe Home Environment: Child's Room** as a classification outcome while explicitly noting that this does not replace evidence-based safe-sleep guidance.
- FGM risk uses NOC `2501` **Protection from Abuse** with safeguarding-oriented local guidance.

Regression tests now lock the removed/renamed codes so they cannot silently reappear.

## Contextual examples

### Childbearing process

For NANDA-I `00208`, the compatibility pair remains appropriate for antenatal use, but the API also exposes:

- NIC `6760` — Childbirth Preparation
- NIC `6830` — Intrapartum Care
- NIC `6930` — Postpartum Care
- NOC `2510` — Maternal Status: Intrapartum
- NOC `2511` — Maternal Status: Postpartum

### Developmental age

For delayed/risk-for-delayed child development, the API can return age-specific teaching and developmental outcomes rather than pretending a single 5-year outcome applies to every child/adolescent age band.

### Withdrawal

For substance withdrawal, the compatibility mapping can be supplemented with alcohol-specific withdrawal care or broader long-term substance-use outcomes depending on the substance and phase of care.

## Bilingual QC

The API/display contract remains:

- **English:** `en-GB`
- **Portuguese:** `pt-BR`
- **Licensed audit source language:** Spanish (`es`)

All 277 primary SAE rows continue to contain bilingual NANDA, NIC and NOC display fields. All 627 link rows contain both `label_en` and `label_pt`. British spelling normalization remains enforced in tests for deployed English labels/prose.

Translations are project display translations; the canonical identity of a classification item is the code + edition. The project does not claim that the local en-GB/pt-BR wording is an official publisher translation where no such licensed translation source was supplied.

## Remaining expert-review queue

The source verification greatly improves code/edition correctness, but clinical mapping remains context-sensitive by design. The refreshed review queue is:

- **48 high-priority rows:** moderate-confidence compatibility primaries.
- **120 medium-priority rows:** high-confidence mappings whose pair-level support is mainly current-edition code/label verification plus semantic fit.
- **109 normal-priority rows:** high-confidence mappings with a more specific literature/source basis.

`sae_mapping_review.csv` is diagnosis-centric. `nnn_link_review.csv` contains all **627** primary and contextual links for institution-level review.

## Interpretation

Pass 5 establishes a current-edition, bilingual, auditable **curated clinical mapping layer**. It still does not claim that NANDA-I, NIC or NOC publishes an official one-to-one crosswalk for every diagnosis. The new one-to-many model is intentionally aligned with the supplied classification guidance that intervention and outcome selection is contextual and requires professional judgement.
