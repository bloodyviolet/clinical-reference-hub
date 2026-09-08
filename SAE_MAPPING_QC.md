# SAE / NANDA-I → NIC → NOC Mapping QC — Pass 5

Review date: **2026-09-07**

## Current edition baseline

- **NANDA-I:** *Nursing Diagnoses: Definitions and Classification 2024–2026*, 13th edition.
- **NIC:** *Nursing Interventions Classification*, 8th edition.
- **NOC:** *Nursing Outcomes Classification*, 7th edition.

Pass 5 uses the institutionally supplied Spanish NIC 8 and NOC 7 books as licensed audit sources and retains **en-GB + pt-BR** as the deployed bilingual presentation.

See `NNN_CURRENT_EDITION_AUDIT.md` and `data/nnn_source_manifest.json` for source provenance and hashes.

## Why the model changed

The current NIC source describes several ways to identify an intervention and requires clinical selection. The current NOC source describes outcome selection as dependent on the diagnosis/problem, patient/population, preferences and context. Therefore a strict one-diagnosis/one-intervention/one-outcome data model overstates certainty.

Pass 5 keeps one primary NIC and one primary NOC for compatibility, but migration `0005` adds a one-to-many `sae_classification_links` table for contextual alternatives.

## Current QC totals

- Diagnoses: **277**
- Mapping status: **277/277 `curated_current_editions_contextual`**
- Primary confidence: **229 high / 48 moderate**
- Compatibility primary links: **554**
- Contextual alternatives: **73**
- Total links: **627**
- Diagnoses with contextual alternatives: **26**
- Unique primary NIC codes: **110**
- Unique primary NOC codes: **115**
- Unique NIC codes across all links: **120**
- Unique NOC codes across all links: **136**
- Unmapped diagnoses: **0**

All 627 link rows contain bilingual `label_en` and `label_pt`, edition, role, applicability, confidence, verification status, source language/reference, review date and notes.

## Removed/current-edition regression targets

The regression suite explicitly rejects obsolete/wrong primary identifiers found during review:

- NIC `1054` — removed from the current mapping set.
- NIC `6780` — removed from the current mapping set.
- NOC `1050` — removed; gastrointestinal function is mapped to current NOC `1015`.

It also locks selected current mappings including thrombosis, autonomic function, impulse control, withdrawal, bowel function, cardiovascular risk, community resilience and breastfeeding-related care.

## Review queue

`sae_mapping_review.csv` contains one row per NANDA diagnosis and now includes contextual-link counts/codes.

Current priority distribution:

- **48 high:** moderate-confidence compatibility primary.
- **120 medium:** high-confidence, but pair-level evidence is mainly current-edition code/label verification + semantic clinical fit.
- **109 normal:** high-confidence with a more specific literature/source reference.

`nnn_link_review.csv` contains every primary and alternative link (**627 rows**) and should be used for the institution's detailed NNN sign-off.

## Safety interpretation

A primary mapping is a useful default/compatibility choice, not a patient-specific order set. Real care plans may require multiple NIC interventions, multiple NOC outcomes, licensed activities/indicators/scales, local protocols, medical/interprofessional actions, contraindication screening and additional nursing diagnoses.
