# WHO growth reference attribution and provenance

## Scope

Clinical Reference Hub v2 includes normalized WHO growth reference
tables for offline calculation of paediatric anthropometric z-scores.

The numerical reference layer and the Brazilian clinical interpretation
layer are intentionally separate.

## WHO numerical sources

### WHO Child Growth Standards 2006

Source package:

- World Health Organization `anthro`
- pinned commit:
  `b776d8a12b1c97369c748b561159fd2ec4f4db58`
- upstream package declaration: `GPL-3`

Reference:
https://www.who.int/tools/child-growth-standards

### WHO Growth Reference 2007

Source package:

- World Health Organization `anthroplus`
- pinned commit:
  `7cfcdb39026e9a55de55732bc3cf14c82261bcf7`
- upstream package declaration: `GPL (>= 3)`

Reference:
https://www.who.int/tools/growth-reference-data-for-5to19-years

## Bundled license material

`assets/reference/who-growth/GPL-3.0.txt` contains GNU GPL version 3.

`assets/reference/who-growth/NOTICE.txt` records source repositories,
pinned commits, access date, normalization scope, and the explicit
non-endorsement statement.

## WHO terms

WHO's current publishing/data terms were reviewed on 2026-09-11:

https://www.who.int/about/policies/publishing/data-policy/terms-and-conditions

The application must not imply WHO endorsement.

## Brazilian interpretation layer

`BRAZIL_SISVAN.json` is a separately maintained national interpretation
layer based on Brazilian Ministry of Health / SISVAN guidance.

The Brazilian labels do not modify WHO LMS values, z-scores, or
percentiles.

## Engineering rule

Any update to the underlying WHO reference files must:

1. pin the new authoritative upstream revision;
2. regenerate normalized tables;
3. regenerate hashes in `SOURCES.json`;
4. rerun WHO official-vector parity tests;
5. review WHO and Brazilian source status again;
6. update this attribution record when provenance or terms change.
