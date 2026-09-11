# v2 Brazil Clinical Harmonization Policy

Clinical review date: 2026-09-11

## Purpose

Every clinical feature added to Clinical Reference Hub v2 must be
explicitly reviewed for Brazilian applicability before it can be
considered release-complete.

Brazilian review is independent from the international-source review.

A feature is not assumed to have a Brazilian variant merely because it
is used in Brazil. Conversely, an international source does not
automatically supersede a current Brazilian national SUS standard.

## Source hierarchy

Use the highest applicable level:

1. Ministério da Saúde / SUS
   - PCDT
   - Diretrizes Nacionais or Brasileiras
   - official Ministry manuals, lines of care and technical notes
   - CONITEC-approved guidance
   - SAPS / SAES / SVSA official guidance

2. ANVISA, where the clinical domain falls within its authority.

3. Other Brazilian federal health authorities when directly relevant,
   including ANS for supplementary-health standards.

4. National Brazilian professional societies when no applicable
   federal standard exists.

5. State, municipal, EBSERH or hospital protocols only as:
   - implementation evidence;
   - contextual evidence; or
   - a source of local practice where no national rule is claimed.

Local material must never be relabelled as a national Brazilian
standard.

## Allowed Brazil applicability statuses

- national_standard
- national_variant
- validated_brazilian_adaptation
- complementary_brazil_guidance
- no_national_variant_identified
- not_applicable

"No national variant identified" is a positive audit result only after
a documented search of authoritative Brazilian sources. It does not
mean that no Brazilian publication exists.

## International/Brazil coexistence

When Brazilian national guidance differs from the current international
reference:

- do not silently overwrite either source;
- preserve the current international calculation;
- expose the Brazilian/SUS interpretation or calculation separately;
- identify the authority and source version;
- explain the difference in PT-BR and EN-GB;
- never imply that a newer international recommendation has been
  formally adopted by SUS unless an authoritative Brazilian source
  establishes that fact.

Machine-readable concepts should remain explicit, for example:

- international_current
- brazil_sus
- brazil_context

## Translation rule

A validated Brazilian adaptation must take precedence over a locally
authored translation when licensing and source conditions permit.

The translation provenance must accurately distinguish:

- official_translation
- validated_translation
- informative_translation
- local_translation
- local_translation_with_disclaimer_required

## Context-specific standards

A Brazilian threshold applicable to a specific condition must not
become a universal threshold.

Examples:

- MAP targets used in septic shock do not define a universal normal MAP.
- obstetric Shock Index thresholds do not define a universal Shock
  Index threshold.
- toxic-alcohol anion-gap formulas do not replace the general
  acid-base calculator.

## Mandatory metadata

Every new v2 clinical feature must record:

- brazil_applicability_status
- brazil_review_date
- brazil_authority
- brazil_source_title
- brazil_source_url
- brazil_document_or_portaria, when applicable
- brazil_scope_pt
- brazil_scope_en
- brazil_differs_from_international
- brazil_difference_notes_pt
- brazil_difference_notes_en
- remediation_required
- final_brazil_review_status

## Release gate

No v2 feature may be marked final unless:

1. international source review is PASS;
2. Brazilian source review is PASS;
3. PT-BR behavior is PASS;
4. EN-GB behavior is PASS;
5. numerical parity is PASS where applicable;
6. international/Brazil distinctions are explicit;
7. source provenance is durable;
8. offline behavior preserves the same distinctions;
9. final source freshness is rechecked before v2.0.0 release.

This rule applies retrospectively to Items 1–6 and prospectively to all
subsequent v2 items.

## Future feature rule

Items 7 onward must complete Brazilian-source review before clinical
implementation begins, rather than receiving a Brazilian layer after
the feature is written.
