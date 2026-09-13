# SUS PCDT Public Document Repository

## Purpose

The Clinical Reference Hub will maintain a self-hosted archive of
recoverable official PCDT-related PDF assets.

The archive complements the structured metadata registry.

## Storage

Persistent binary storage:

`/var/lib/medical-api/documents/pcdt`

PDF objects are not stored in Git and are not stored as SQLite BLOBs.

## Byte identity

Each archived PDF is immutable and identified by SHA-256.

Canonical object layout:

`objects/sha256/<first-two-hex>/<full-sha256>.pdf`

Upstream byte changes never silently overwrite an older object.

## Public namespace

Target public prefix:

`/documents/pcdt`

Only archived objects with verified public redistribution status may
receive a self-hosted public URL.

## Provenance

Every archived object preserves:

- canonical official source URL;
- resolved download URL;
- SHA-256;
- size;
- MIME type;
- retrieval/verification timestamps;
- license evidence.

## Import safety

The future mutating importer must follow:

discover → review → fetch temporary file → validate → hash → atomically
archive → update manifest → verify.

The first implementation is deliberately discovery-only and cannot
download or populate the persistent archive.

## Performance isolation

PCDT PDFs do not participate in unrelated clinical calculator requests.

Large PDFs are intended for static nginx delivery rather than runtime
clinical-engine processing.

The complete archive is never bulk-preloaded into the PWA cache.

## Historical completeness

The target is all recoverable official PCDT-related PDF assets within
documented official-source discovery scope.

Known missing or unrecoverable assets are retained as explicit metadata
gaps rather than silently discarded.

## First controlled archive tranche

BH9A3 preserved the first five reviewed `protocol_text` PDFs in the
persistent SHA-256-addressed archive:

- Artrite Reumatoide;
- Asma;
- Câncer de Mama;
- Osteoporose;
- Atenção Integral às Pessoas com Infecções Sexualmente Transmissíveis.

The objects were staged from official sources, validated as PDF content,
hashed, installed byte-for-byte in the persistent object store, and
independently reverified before registry/manifest linkage.

These objects remain in
`archive_only_pending_license_review` state. No self-hosted public URL is
assigned until per-object redistribution evidence is qualified.

This controlled tranche does not enable nginx document serving, API/UI
exposure, or PWA PDF precaching. It is the canary tranche for subsequent
expansion toward the full recoverable PCDT corpus.

## Canary redistribution qualification

BH9A3B2 independently re-fetched all five canary `protocol_text` PDFs
from their official gov.br sources and reproduced the archived SHA-256
and byte size for every object.

Each corresponding official gov.br resource page also exposed the
Creative Commons **Atribuição-SemDerivações 3.0 Não Adaptada**
licensing notice. The evidence was recorded per object rather than
inferred across the historical corpus.

Evidence report SHA-256:

`497cacf2f0415528c88297f6a5609ec43138f4aa4cbea088e28e3335bb4d1199`

BH9A3B3 therefore promotes these five exact archive objects to
`public_verified` redistribution status.

`public_verified` does **not** mean the object is already being served.
The `public_url` and `self_hosted_public_url` fields remain unset until
the static-serving/nginx layer is separately implemented and qualified.

No blanket redistribution conclusion is made for other current,
historical, superseded, or subsequently discovered PCDT assets.

## Current protocol-text corpus completion

BH9A4 qualified and archived the remaining 127 current
`protocol_text` documents after the five-object canary.

The resulting current protocol-text layer contains **132 logical
documents and 132 unique immutable SHA-256 PDF objects**.

All 127 additional documents passed the same controls used for the
canary:

- official gov.br-family source;
- valid PDF signature, non-trivial size, and EOF structure;
- SHA-256 content identity;
- corresponding official resource-page evidence for Creative Commons
  Atribuição-SemDerivações 3.0 Não Adaptada;
- per-object and per-document provenance;
- no hash collision with the five canary objects.

Bulk qualification report SHA-256:

`7c0b742349384170f70e956d2a3fda57f770b22815a2d4d7af252285f28fd855`

Ready-object plan SHA-256:

`865116a471f933da08e8879b2fdfea4827a172319bf84d9cd38aad335f062fa8`

All 132 current `protocol_text` objects are therefore
`public_verified` for redistribution while remaining unserved locally.
`public_url` and `self_hosted_public_url` remain unset.

This completes the **current protocol-text layer only**.

**v2 release-scope boundary.** For the v2.0.0 release, Item 9 is
intentionally limited to the qualified current PCDT corpus, its
represented current associated official documents, and structured
revision metadata/assets already demonstrated by official sources.
The 13 historical approval relationships already present in the
registry are retained, but further historical protocol/version
discovery and ingestion are explicitly deferred until after v2.0.0 is
completed and deployed.

Historical expansion is therefore post-v2 work. Before historical
`protocol_text` documents are introduced, the registry will require
explicit current-version semantics and validated supersession-graph
relationships so that document role is not used to infer currentness.
For the qualified v2 corpus, each of the 132 PCDTs continues to have
exactly one current `protocol_text`-bearing approval version.

No nginx route, API/browser/UI exposure, or PWA PDF bulk precaching is
enabled by this step.

## Represented current associated-asset ingestion

BH9A5 originally qualified 243 associated current relationships.
A subsequent metadata-integrity correction removed one misassociated
approval-act relationship. The qualified current associated layer now
contains **242 logical documents**:

- 134 approval acts;
- 20 Ministry publications;
- 88 protocol summaries.

The 242 logical relationships resolve to **234 unique SHA-256 binaries**.
All 234 associated binaries are distinct from the 132 current
protocol-text objects. The qualified current v2 corpus therefore resolves
to **366 unique archive objects**, serving **374 current logical
documents** (132 current protocol texts plus 242 represented associated
documents).

The archive contains **376 immutable objects overall**: the 366 current
objects plus 10 additional objects supporting the 13 historical approval
relationships already retained in the registry.

Original BH9A5 qualification report SHA-256 (pre-correction tranche
evidence):

`f2d9752ae6424ba3acdc834281c3b2785b6314d773172b86780ef690aee63269`

Every represented associated document is `archived` and
`public_verified`, while `public_url` and `self_hosted_public_url`
remain unset.

This does **not** establish completeness of all associated current PCDT
materials. Independent catalogue/source discovery remains required for
annexes, amendments, rectifications, recommendation reports, public
consultation material, Ministry publications and other official
supporting documents not yet represented in the registry.

No nginx route, API/browser/UI exposure, or PWA bulk PDF precaching is
enabled by this step.
