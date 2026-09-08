# Classification-content licensing configuration — Pass 4

Review/configuration date: **2026-09-07**

## Deployment profile selected for this build

At the deployer's request, Pass 4 is configured for the stated **institutional, non-profit licensed use** of the NANDA-I and NNN materials:

- SAE/NANDA/NIC/NOC API functionality is **enabled by default**.
- `pdfs/Nanda-I 2024-2026.pdf` is restored to the publicly served `/docs/` tree.
- The dashboard links directly to the institutional NANDA-I PDF and can deep-link to the actual PDF page for each diagnosis.
- Structured NANDA/NIC/NOC code/label and mapping metadata are exposed through API v1.

The public NANDA-I PDF path in this build is:

```text
/docs/Nanda-I%202024-2026.pdf
```

## Important license boundary

This technical configuration follows the license context supplied by the deployer. It is **not a legal determination that “non-profit” status by itself grants public redistribution rights**. The actual institutional agreement, publisher/rightsholder terms, access restrictions, territory, user population, and software/database clauses remain controlling.

If this build is later moved outside that institutional scope, the deployment owner should re-check the agreement before leaving the PDF or classification endpoints public.

The optional administrative switch remains available:

```bash
MEDICAL_API_ENABLE_SAE=false
```

This switch is retained as an operational control for a different deployment profile; it is **not** the default for this Pass 4 package.

## Rights-holder/source references

- INKA / NANDA current classification and licensing information:
  - https://nanda.org/nanda-book/
  - https://nanda.org/use-and-licensing/
  - https://nanda.org/terms-and-conditions/
- University of Iowa Center for Nursing Classification and Clinical Effectiveness:
  - https://nursing.uiowa.edu/center-for-nursing-classification-and-clinical-effectiveness
- NIC publications/current edition:
  - https://nursing.uiowa.edu/cncce/nic-publications
- NOC publications/current edition:
  - https://nursing.uiowa.edu/cncce/noc-publications
- Elsevier copyright/permissions guidance:
  - https://www.elsevier.com/about/policies-and-standards/copyright/permissions

This remains a technical licensing/configuration note, not legal advice.

## Pass 5 NIC/NOC source handling

The institution supplied Spanish-language NIC 8th-edition and NOC 7th-edition PDFs for the Pass 5 audit. They are used as licensed source material but are **not added to the web-served `/docs/` tree and are not copied into the deployment ZIP**. Their SHA-256 hashes, edition/language and audit purpose are recorded in `data/nnn_source_manifest.json`.

This is an intentional packaging choice, not an assertion that the institutional agreement forbids serving them. Public serving can be enabled later if the deployment owner explicitly wants it and the applicable agreement permits that use.
