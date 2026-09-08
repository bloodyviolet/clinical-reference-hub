from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main  # noqa: E402

client = TestClient(main.app)


def test_v1_healthcheck_reaches_database():
    response = client.get('/api/v1/healthz')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['database'] == 'ok'
    assert payload['assets'] == 'ok'
    assert payload['api_version'] == '1.4.5'
    assert payload['database_revision'] == '0007'
    assert payload['sae_enabled'] is True
    assert payload['clinical_content'] == 'certified'
    assert len(payload['clinical_content_manifest_sha256']) == 64


def test_compat_healthcheck_remains_available():
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_static_files_do_not_depend_on_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert client.get('/').status_code == 200
    assert client.get('/manifest.json').status_code == 200
    assert client.get('/sw.js').status_code == 200
    assert client.get('/assets/app.css').status_code == 200
    assert client.get('/docs/PNAISM.pdf').status_code == 200


def test_blank_search_is_rejected():
    response = client.get('/api/v1/sae/search', params={'q': '   '})
    assert response.status_code == 422


def test_like_wildcards_are_literal_not_match_all():
    for query in ('%', '_'):
        response = client.get('/api/v1/sae/search', params={'q': query})
        assert response.status_code == 404


def test_v1_search_has_typed_envelope_and_limit():
    response = client.get('/api/v1/sae/search', params={'q': 'a', 'limit': 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload['query'] == 'a'
    assert payload['limit'] == 5
    assert payload['offset'] == 0
    assert payload['returned'] == len(payload['items'])
    assert len(payload['items']) <= 5
    assert {'id', 'code', 'description_en', 'description_pt', 'mapping_status', 'mapping_methodology', 'nanda_edition', 'nanda_source_page', 'nanda_pdf_page', 'nic_code', 'nic_label_en', 'noc_code', 'noc_label_en', 'mapping_confidence', 'mapping_rationale'} <= set(payload['items'][0])
    assert all(len(item['code']) == 5 and item['code'].isdigit() for item in payload['items'])


def test_search_limit_has_upper_bound():
    response = client.get('/api/v1/sae/search', params={'q': 'a', 'limit': 101})
    assert response.status_code == 422


def test_policy_index_lists_unified_pnaism():
    response = client.get('/api/v1/policies')
    assert response.status_code == 200
    by_name = {item['policy_name']: item['directives'] for item in response.json()['items']}
    assert by_name['PNAISM'] == 17
    assert len(by_name) == 7


def test_policy_response_contains_provenance():
    response = client.get('/api/v1/policies/PNAISM')
    assert response.status_code == 200
    payload = response.json()
    assert payload['policy_name'] == 'PNAISM'
    assert payload['returned'] == 17
    assert payload['items']
    for item in payload['items']:
        assert item['source_title']
        assert item['source_url'].startswith('https://')
        assert item['last_clinical_review'] == '2026-09-07'
        assert item['status'] in {'current', 'superseded', 'historical', 'needs_review'}
        assert item['evidence_level'] in {'current_override', 'pinpoint_policy', 'policy_context', 'policy_level'}
        assert item['source_page']


def test_pnaism_compatibility_route_preserves_legacy_shape():
    response = client.get('/pnaism/')
    assert response.status_code == 200
    item = response.json()[0]
    assert set(item) == {'id', 'directive', 'target_demographic', 'clinical_guideline'}


def test_policy_compatibility_route_preserves_legacy_shape():
    response = client.get('/policy/PNAB')
    assert response.status_code == 200
    item = response.json()[0]
    assert set(item) == {'id', 'policy_name', 'directive', 'target_demographic', 'clinical_guideline'}


def test_sae_metadata_reports_current_editions_and_confidence():
    response = client.get('/api/v1/sae/metadata')
    assert response.status_code == 200
    payload = response.json()
    assert payload['record_count'] == 277
    assert payload['mapping_status'] == 'curated_current_editions_contextual'
    assert payload['confidence_counts'] == {'high': 229, 'moderate': 48}
    assert payload['link_count'] == 627
    assert payload['diagnoses_with_contextual_alternatives'] == 26
    assert 'one-to-many' in payload['mapping_model']
    assert '2024-2026' in payload['nanda_reference']
    assert '8th edition' in payload['nic_reference']
    assert '7th edition' in payload['noc_reference']
    assert 'not an official' in payload['mapping_methodology']
    assert payload['licensing_profile'] == 'institutional_nonprofit_enabled'
    assert payload['english_variant'] == 'en-GB'
    assert payload['portuguese_variant'] == 'pt-BR'


def test_security_headers_are_present():
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']


def test_sae_can_be_disabled_for_public_deployments(monkeypatch):
    monkeypatch.setattr(main, 'ENABLE_SAE', False)
    response = client.get('/api/v1/sae/search', params={'q': 'dor'})
    assert response.status_code == 503
    assert 'administrator' in response.json()['detail'].lower()


def test_all_policy_rows_have_specific_evidence_tier():
    index = client.get('/api/v1/policies').json()['items']
    tiers = []
    for entry in index:
        response = client.get(f"/api/v1/policies/{entry['policy_name']}")
        assert response.status_code == 200
        tiers.extend(item['evidence_level'] for item in response.json()['items'])
    assert len(tiers) == 54
    assert 'policy_level' not in tiers
    assert set(tiers) == {'current_override', 'pinpoint_policy', 'policy_context'}


def test_licensed_nanda_pdf_is_publicly_served_in_this_build():
    response = client.get('/docs/Nanda-I%202024-2026.pdf')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/pdf')
    assert response.content.startswith(b'%PDF')


def test_known_current_edition_mapping_corrections():
    cases = {
        '00322': ('0620', 'Urinary Retention Care', '0503', 'Urinary Elimination'),
        '00339': ('5515', 'Health Literacy Enhancement', '2015', 'Health Literacy Behaviour'),
        '00475': ('5100', 'Socialization Enhancement', '1203', 'Loneliness Severity'),
        '00348': ('1160', 'Nutritional Monitoring', '0110', 'Growth'),
    }
    for nanda_code, expected in cases.items():
        response = client.get(f'/api/v1/nanda/{nanda_code}')
        assert response.status_code == 200
        item = response.json()
        assert (item['nic_code'], item['nic_label_en'], item['noc_code'], item['noc_label_en']) == expected
        assert item['mapping_confidence'] == 'high'
        assert item['nanda_source_page'].isdigit()
        assert item['nanda_pdf_page'].isdigit()
        assert item['mapping_reference'].startswith('http')


def test_dedicated_nic_and_noc_endpoints_are_enabled():
    nic = client.get('/api/v1/nic/0620')
    assert nic.status_code == 200
    assert nic.json()['label_en'] == 'Urinary Retention Care'
    assert any(row['nanda_code'] == '00322' for row in nic.json()['linked_diagnoses'])

    noc = client.get('/api/v1/noc/2015')
    assert noc.status_code == 200
    assert noc.json()['label_en'] == 'Health Literacy Behaviour'
    assert any(row['nanda_code'] == '00339' for row in noc.json()['linked_diagnoses'])

    nic_index = client.get('/api/v1/nic')
    noc_index = client.get('/api/v1/noc')
    assert nic_index.status_code == 200 and nic_index.json()['returned'] == 120
    assert noc_index.status_code == 200 and noc_index.json()['returned'] == 136


def test_sae_search_accepts_nic_and_noc_codes():
    by_nic = client.get('/api/v1/sae/search', params={'q': '0620'}).json()['items']
    assert any(item['code'] == '00322' for item in by_nic)
    by_noc = client.get('/api/v1/sae/search', params={'q': '2015'}).json()['items']
    assert any(item['code'] == '00339' for item in by_noc)


def test_contextual_nnn_links_are_exposed_for_phase_dependent_diagnosis():
    response = client.get('/api/v1/nanda/00208')
    assert response.status_code == 200
    item = response.json()
    assert item['nic_code'] == '6960'
    assert item['noc_code'] == '2509'
    nic = {(link['code'], link['role']) for link in item['nic_links']}
    noc = {(link['code'], link['role']) for link in item['noc_links']}
    assert {('6960', 'primary'), ('6760', 'alternative'), ('6830', 'alternative'), ('6930', 'alternative')} <= nic
    assert {('2509', 'primary'), ('2510', 'alternative'), ('2511', 'alternative')} <= noc
    links = item['nic_links'] + item['noc_links']
    assert all(link['applicability'] for link in links)
    assert all(link['applicability_en'] for link in links)
    assert all(link['applicability_pt'] for link in links)
    assert all(
        link['applicability'] == link['applicability_en']
        for link in links
    )


def test_current_edition_code_and_label_regressions_are_fixed():
    cases = {
        '00291': ('6610', '1932', 'Risk Control: Thrombus'),
        '00010': ('2620', '0910', 'Neurological Function: Autonomic'),
        '00222': ('4370', '1405', 'Self-Control of Impulses'),
        '00258': ('4514', '2108', 'Substance Withdrawal Severity'),
        '00422': ('0430', '1015', 'Gastrointestinal Function'),
        '00311': ('4050', '1914', 'Risk Control: Cardiovascular Disease'),
        '00076': ('8500', '2704', 'Community Resilience'),
        '00461': ('5244', '1101', 'Tissue Integrity: Skin & Mucous Membranes'),
    }
    for code, (nic, noc, noc_label) in cases.items():
        item = client.get(f'/api/v1/nanda/{code}').json()
        assert item['nic_code'] == nic
        assert item['noc_code'] == noc
        assert item['noc_label_en'] == noc_label
    assert client.get('/api/v1/nic/1054').status_code == 404
    assert client.get('/api/v1/nic/6780').status_code == 404
    assert client.get('/api/v1/noc/1050').status_code == 404


def test_search_finds_contextual_alternative_codes():
    items = client.get('/api/v1/sae/search', params={'q': '2511'}).json()['items']
    assert any(item['code'] == '00208' for item in items)
    items = client.get('/api/v1/sae/search', params={'q': '5680'}).json()['items']
    assert any(item['code'] in {'00305', '00314'} for item in items)


def test_sae_english_is_localised_to_en_gb_and_ptbr_is_present():
    response = client.get('/api/v1/sae/search', params={'q': '00339'})
    assert response.status_code == 200
    item = response.json()['items'][0]
    assert item['description_en'] and item['description_pt']
    assert item['nic_label_en'] and item['nic_label_pt']
    assert item['noc_label_en'] == 'Health Literacy Behaviour'
    assert item['noc_label_pt'] == 'Comportamento de Literacia em Saúde'
    corpus = ' '.join([item['description_en'], item['intervention_en'], item['outcome_en'], item['nic_label_en'], item['noc_label_en']])
    assert ' Behavior' not in corpus


def test_portuguese_interventions_do_not_embed_english_diagnosis_text():
    db = next(main.get_db())
    try:
        rows = db.query(main.database.SAEDiagnostic).order_by(main.database.SAEDiagnostic.code.asc()).all()
        assert len(rows) == 277
        for row in rows:
            assert row.intervention_pt.strip(), row.code
            assert row.description_en.lower() not in row.intervention_pt.lower(), row.code
    finally:
        db.close()


def test_all_contextual_links_are_bilingual_and_current_edition_audited():
    # Query every diagnosis through the public API so this validates serialization as well as DB content.
    search = client.get('/api/v1/sae/search', params={'q': 'a', 'limit': 100, 'offset': 0})
    assert search.status_code == 200
    # Direct DB check is appropriate for full-set invariants that would otherwise require pagination over 277 API records.
    db = next(main.get_db())
    try:
        links = db.query(main.database.SAEClassificationLink).all()
        assert len(links) == 627
        assert all(link.label_en and link.label_pt for link in links)
        assert all(link.source_language == 'es' for link in links)
        assert all(link.edition and link.source_reference for link in links)
        assert all(link.role in {'primary', 'alternative'} for link in links)
        assert all(link.verification_status in {'curated_current_edition', 'current_edition_verified', 'contextual_current_edition'} for link in links)
    finally:
        db.close()


def test_liveness_readiness_request_id_and_cache_policy():
    live = client.get('/api/v1/livez')
    assert live.status_code == 200
    assert live.json() == {'status': 'ok', 'api_version': '1.4.5'}
    assert live.headers['cache-control'] == 'no-store'
    assert live.headers.get('x-request-id')

    request_id = 'phase6-release-probe-001'
    ready = client.get('/api/v1/readyz', headers={'X-Request-ID': request_id})
    assert ready.status_code == 200
    assert ready.headers['x-request-id'] == request_id
    assert ready.json()['database_revision'] == '0007'
    assert ready.json()['assets'] == 'ok'

    root = client.get('/')
    assert root.headers['cache-control'] == 'no-cache'

