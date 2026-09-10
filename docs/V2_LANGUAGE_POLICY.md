# Clinical Reference Hub v2.0.0 — Language Policy

## Canonical API contract

API field names and machine-readable identifiers use stable English
technical identifiers.

Calculations, scores, codes, thresholds, units and numerical results are
language-neutral.

Canonical API responses retain both PT-BR and EN-GB human-readable content.
The canonical representation is not reduced to a single language with a
`?lang=` parameter.

## User-facing languages

- Default UI: PT-BR
- Secondary UI: EN-GB
- New v2 clinical tools must be complete in both languages.
- Offline functionality must preserve the same bilingual behavior.
- Numeric output must be identical regardless of selected UI language.

## Translation provenance

Every clinical tool must identify:

- source language
- canonical language
- PT-BR translation status
- EN-GB translation status
- publisher
- source title
- source version
- source URL
- clinical review date
- limitations
- bilingual aliases

Validated instruments must preserve the canonical scoring logic.

Official or validated translations are preferred when available.
Locally translated material must be identified as such and must not be
represented as an official or independently validated translation.

Where the instrument owner requires a translation disclaimer or other
reproduction condition, metadata must explicitly record that requirement.

## Brazilian sources

For Brazilian Ministry of Health, PNI, PCDT and other authoritative Brazilian
content:

- canonical language: PT-BR
- PT-BR content remains authoritative
- EN-GB is an informational translation unless an official English source
  exists
- translated titles must not be represented as official Ministry titles

## International sources

The original publication language remains canonical.

PT-BR content must record whether it is an official translation, validated
translation, informational translation or local translation.

## Search

Clinical-tool metadata must support PT-BR and EN-GB aliases.

Examples:

- LRA / lesão renal aguda
- AKI / acute kidney injury
- deterioração clínica
- clinical deterioration

## v2 release gate

No new v2 clinical feature is complete unless all applicable checks pass:

1. PT-BR content present.
2. EN-GB content present.
3. Numerical parity across languages.
4. Provenance present.
5. Translation status present.
6. Limitations present.
7. Offline behavior qualified where applicable.
8. Clinical source/version independently QC'd.
9. Existing v1 regression suite remains green.
10. Real-browser bilingual behavior passes final qualification.

The production application remains 1.4.5 until the complete v2.0.0 bundle
passes final qualification.

## NEWS2 translation release gate

NEWS2 translated material is subject to the Royal College of Physicians'
translation condition.

Before v2.0.0 may be released publicly:

- the required RCP translation disclaimer must be included exactly as
  specified by the current official RCP NEWS2 resource;
- the RCP attribution requirement must be satisfied;
- locally translated PT-BR explanatory material must not be represented as
  an RCP-approved or independently validated translation;
- compliance must be checked again against the live RCP source during final
  release qualification.

This is a release-blocking compliance check.
