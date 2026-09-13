# Persistent UX + Bloodviolet theme — Phase 7 UAT candidate

## Purpose

This candidate extends the v2 Phase 7 browser experience without changing
clinical arithmetic, clinical registries, clinical-source manifests, the
packaged database, or production deployment.

## Browser-session persistence boundary

`sessionStorage` stores:

- active primary tab;
- active Calculator subgroup;
- active Scale subgroup;
- selected SUS policy;
- last successful inputs for each of the 26 Calculator/Scale tools;
- the rendered last-successful result for each tool;
- the latest successful request/result/source bridge for the 18 instruments
  eligible for Serial Trends.

This state survives refresh inside the same browser tab/session.

It is not stored in:

- `localStorage`;
- IndexedDB;
- service-worker storage;
- the API;
- the server database.

The pre-existing language preference remains a separate non-clinical
`localStorage` preference and is not part of this feature.

The 26 covered calculator/scale forms contain structured fields only. They do
not contain free-text or textarea patient-information fields.

## Reset semantics

Each Calculator/Scale form receives its own Reset button.

Reset:

- restores that form to its HTML default inputs;
- clears that tool's remembered successful result;
- clears that tool's remembered Serial Trends latest-result bridge, when one
  exists;
- does not delete observations already deliberately added to Serial Trends;
- does not reset any other Calculator/Scale tool.

## Home navigation

The canonical Nursing Clinical Hub icon replaces the old `Rx` mark.

The icon and:

- `Clinical Reference Hub`
- `SAE / NNN & Políticas Nacionais do SUS`

form one accessible link to `/`.

Selecting this Home link explicitly sets the primary view to SAE. Calculator,
Scale, policy and result state remain available for the rest of the same
browser session.

Refresh therefore preserves location/state rather than acting as Home.

## Bloodviolet visual identity

Foundation:

- near-black;
- deep plum.

Secondary accent:

- violet.

Primary brand/action accent:

- blood red;
- crimson.

Foreground:

- white;
- pale lavender;
- muted lavender on dark structural surfaces.

Success remains emerald and warnings remain amber. Error/destructive rose
remains a brighter red family than ordinary blood-red brand actions.

PWA metadata:

- background: `#09030F`
- theme: `#5A0B32`
- cache: `clinical-reference-v27-v2-bloodviolet-persistent-ux`

## Human UAT required

Mechanical qualification does not close browser UAT.

Required retest:

1. refresh on every primary tab;
2. refresh on Calculator subgroups;
3. refresh on Scale subgroups;
4. selected SUS policy survives refresh;
5. successful result/input restoration across all 26 tools;
6. individual Reset across all 26 tools;
7. restored result can still be added to Serial Trends for all supported
   instruments;
8. Reset does not erase saved Serial Trends observations;
9. linked icon/text Home behavior;
10. PT-BR / EN-GB;
11. keyboard focus;
12. 200% zoom;
13. visual contrast and button affordance under the Bloodviolet palette.
