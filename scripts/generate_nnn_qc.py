from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAE = ROOT / 'sae_bilingual_final.csv'
LINKS = ROOT / 'data' / 'sae_nnn_links.csv'
REVIEW = ROOT / 'sae_mapping_review.csv'
LINK_REVIEW = ROOT / 'nnn_link_review.csv'
MANIFEST = ROOT / 'data' / 'nnn_source_manifest.json'
REVIEW_DATE = '2026-09-07'

def source_metadata(classification: str) -> dict:
    if not MANIFEST.is_file():
        raise FileNotFoundError(
            f"Packaged NNN provenance manifest not found: {MANIFEST}"
        )

    payload = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    matches = [
        source
        for source in payload.get("sources", [])
        if source.get("classification") == classification
    ]

    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one packaged provenance entry for "
            f"{classification}; found {len(matches)}."
        )

    source = matches[0]

    filename = str(
        source.get("uploaded_filename", "")
    ).strip()

    digest = str(
        source.get("sha256", "")
    ).strip().lower()

    if not filename:
        raise ValueError(
            f"Missing uploaded_filename for {classification}."
        )

    if (
        len(digest) != 64
        or any(ch not in "0123456789abcdef" for ch in digest)
    ):
        raise ValueError(
            f"Invalid SHA-256 provenance for {classification}: "
            f"{digest!r}"
        )

    if source.get("packaged_with_application") is not False:
        raise ValueError(
            f"{classification} provenance unexpectedly claims "
            "the licensed source is packaged with the application."
        )

    return source


NIC_SOURCE_META = source_metadata("NIC")
NOC_SOURCE_META = source_metadata("NOC")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def evidence_basis(ref: str) -> str:
    r = (ref or '').lower()
    if 'doi.org/' in r or 'pubmed' in r or 'ncbi.nlm.nih.gov' in r or 'researchgate.net' in r:
        return 'specific_literature_or_source'
    if 'salusplay.com' in r:
        return 'current_edition_code_label_listing_plus_semantic_match'
    return 'edition_baseline_plus_semantic_match'


def review_priority(confidence: str, basis: str) -> str:
    if confidence == 'moderate':
        return 'high'
    if basis == 'specific_literature_or_source':
        return 'normal'
    return 'medium'


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    sae = read_csv(SAE)
    links = read_csv(LINKS)
    by_code = {r['code'].zfill(5): r for r in sae}
    links_by_code: dict[str, list[dict[str, str]]] = {}
    for link in links:
        links_by_code.setdefault(link['nanda_code'].zfill(5), []).append(link)

    nic_reuse = Counter(r['nic_code'] for r in sae)
    noc_reuse = Counter(r['noc_code'] for r in sae)
    review_rows: list[dict[str, str]] = []
    for row in sae:
        code = row['code'].zfill(5)
        basis = evidence_basis(row.get('mapping_reference', ''))
        code_links = links_by_code.get(code, [])
        alts = [x for x in code_links if x['role'] == 'alternative']
        alt_nic = [x for x in alts if x['classification'] == 'NIC']
        alt_noc = [x for x in alts if x['classification'] == 'NOC']
        review_rows.append({
            'review_priority': review_priority(row['mapping_confidence'], basis),
            'evidence_basis': basis,
            'code': code,
            'description_en': row['description_en'],
            'description_pt': row['description_pt'],
            'nanda_domain': row['nanda_domain'],
            'nanda_class': row['nanda_class'],
            'nanda_source_page': row['nanda_source_page'],
            'nanda_pdf_page': row['nanda_pdf_page'],
            'nic_code': row['nic_code'],
            'nic_label_en': row['nic_label_en'],
            'nic_label_pt': row['nic_label_pt'],
            'nic_reuse_count': str(nic_reuse[row['nic_code']]),
            'noc_code': row['noc_code'],
            'noc_label_en': row['noc_label_en'],
            'noc_label_pt': row['noc_label_pt'],
            'noc_reuse_count': str(noc_reuse[row['noc_code']]),
            'mapping_confidence': row['mapping_confidence'],
            'mapping_status': row['mapping_status'],
            'contextual_alternative_count': str(len(alts)),
            'contextual_nic_codes': '; '.join(f"{x['code']} {x['label_en']}" for x in alt_nic),
            'contextual_noc_codes': '; '.join(f"{x['code']} {x['label_en']}" for x in alt_noc),
            'mapping_reference': row['mapping_reference'],
            'mapping_rationale': row['mapping_rationale'],
            'mapping_review_date': row['mapping_review_date'],
        })
    priority_order = {'high': 0, 'medium': 1, 'normal': 2}
    review_rows.sort(key=lambda x: (priority_order[x['review_priority']], x['code']))
    write_csv(REVIEW, review_rows, list(review_rows[0].keys()))

    link_rows: list[dict[str, str]] = []
    for link in links:
        d = by_code[link['nanda_code'].zfill(5)]
        link_rows.append({
            'nanda_code': link['nanda_code'].zfill(5),
            'diagnosis_en': d['description_en'],
            'diagnosis_pt': d['description_pt'],
            **{k: link[k] for k in [
                'classification','code','label_en','label_pt','edition','role','applicability','applicability_en','applicability_pt','confidence',
                'verification_status','source_language','source_reference','source_page','review_date','notes'
            ]},
        })
    link_rows.sort(key=lambda r: (r['nanda_code'], r['classification'], 0 if r['role']=='primary' else 1, r['code']))
    write_csv(LINK_REVIEW, link_rows, list(link_rows[0].keys()))

    manifest = {
        'review_date': REVIEW_DATE,
        'purpose': 'Licensed-source provenance for the Pass 5 NANDA-I/NIC/NOC mapping audit. Source books are not copied into the deployment package.',
        'language_policy': {
            'source_books': 'es',
            'api_display': ['en-GB', 'pt-BR'],
            'translation_policy': 'Classification identifiers remain canonical. Short user-facing labels are locally rendered in en-GB and pt-BR; clinical definitions, activities and indicators are not reproduced.'
        },
        'sources': [
            {
                'classification': 'NIC',
                'edition': '8th edition',
                'uploaded_filename': NIC_SOURCE_META['uploaded_filename'],
                'sha256': NIC_SOURCE_META['sha256'],
                'pdf_pages': 616,
                'language': 'Spanish',
                'institutional_source': True,
                'packaged_with_application': False,
                'source_use': 'Edition/methodology verification and licensed terminology review; current code-label list cross-checked against the current NIC 8 classification listing.',
                'methodology_locator': 'PDF viewer page 17: Cómo encontrar una intervención',
            },
            {
                'classification': 'NOC',
                'edition': '7th edition (2024 Spanish translation)',
                'uploaded_filename': NOC_SOURCE_META['uploaded_filename'],
                'sha256': NOC_SOURCE_META['sha256'],
                'pdf_pages': 876,
                'language': 'Spanish',
                'institutional_source': True,
                'packaged_with_application': False,
                'source_use': 'Edition/methodology verification and licensed terminology review; current code-label list cross-checked against the current NOC 7 classification listing.',
                'methodology_locator': 'PDF viewer pages 28-29: Identificación del destinatario / Cómo elegir los resultados',
            },
        ],
        'supplemental_current_code_label_sources': {
            'NIC': 'https://www.salusplay.com/blog/clasificacion-completa-intervenciones-enfermeria-nic-2024/',
            'NOC': 'https://www.salusplay.com/apuntes/pae-y-diagnosticos-de-enfermeria-nanda-noc-y-nic/anexo-2-clasificacion-completa-de-resultados-de-enfermeria-noc-2024-8',
            'official_edition_baseline': 'https://nursing.uiowa.edu/center-for-nursing-classification-and-clinical-effectiveness',
        },
        'audit_counts': {
            'nanda_diagnoses': len(sae),
            'primary_mappings': len(sae) * 2,
            'total_classification_links': len(links),
            'contextual_alternatives': sum(1 for r in links if r['role'] == 'alternative'),
            'diagnoses_with_contextual_alternatives': len({r['nanda_code'] for r in links if r['role'] == 'alternative'}),
            'primary_mapping_confidence': dict(Counter(r['mapping_confidence'] for r in sae)),
            'link_verification_status': dict(Counter(r['verification_status'] for r in links)),
        },
        'interpretation': 'The sources explicitly support context-sensitive selection. The project therefore stores a compatibility primary NIC/NOC pair for backward compatibility plus one-to-many contextual alternatives where phase, age, substance, or care context materially changes the appropriate classification target.'
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print('review priorities', Counter(r['review_priority'] for r in review_rows))
    print('wrote', REVIEW)
    print('wrote', LINK_REVIEW, len(link_rows))
    print('wrote', MANIFEST)

if __name__ == '__main__':
    main()
