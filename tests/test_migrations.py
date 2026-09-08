import os
from pathlib import Path
import sqlite3
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_upgrade(db_path: Path):
    env = os.environ.copy()
    env['MEDICAL_API_DATABASE_URL'] = f'sqlite:///{db_path}'
    subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_migration_builds_fresh_database(tmp_path):
    db_path = tmp_path / 'fresh.db'
    run_upgrade(db_path)
    con = sqlite3.connect(db_path)
    tables = {row[0] for row in con.execute("select name from sqlite_master where type='table'")}
    assert {'sae_diagnostics', 'sae_classification_links', 'public_health_policies', 'alembic_version'} <= tables
    assert 'pnaism_policies' not in tables
    columns = {row[1] for row in con.execute('pragma table_info(public_health_policies)')}
    assert {'source_title', 'source_url', 'last_clinical_review', 'status', 'evidence_level'} <= columns
    sae_columns = {row[1] for row in con.execute('pragma table_info(sae_diagnostics)')}
    assert {'mapping_status', 'mapping_methodology', 'mapping_review_date', 'mapping_notes', 'nanda_edition', 'nanda_domain', 'nanda_class', 'nanda_source_page', 'nanda_pdf_page', 'nic_edition', 'nic_code', 'nic_label_en', 'nic_label_pt', 'noc_edition', 'noc_code', 'noc_label_en', 'noc_label_pt', 'mapping_confidence', 'mapping_reference', 'mapping_rationale'} <= sae_columns
    link_columns = {row[1] for row in con.execute('pragma table_info(sae_classification_links)')}
    assert {'sae_diagnostic_id', 'classification', 'code', 'role', 'applicability', 'applicability_en', 'applicability_pt', 'confidence', 'verification_status', 'source_reference', 'review_date'} <= link_columns
    assert con.execute('select version_num from alembic_version').fetchone()[0] == '0007'


def test_migration_preserves_legacy_policy_rows_and_unifies_pnaism(tmp_path):
    db_path = tmp_path / 'legacy.db'
    con = sqlite3.connect(db_path)
    con.executescript('''
        create table sae_diagnostics (
            id integer primary key,
            code varchar not null unique,
            description_en text not null,
            description_pt text not null,
            intervention_en text not null,
            intervention_pt text not null,
            outcome_en text not null,
            outcome_pt text not null
        );
        create table public_health_policies (
            id integer primary key,
            policy_name varchar not null,
            directive varchar not null,
            target_demographic varchar not null,
            clinical_guideline text not null
        );
        create table pnaism_policies (
            id integer primary key,
            directive varchar not null,
            target_demographic varchar not null,
            clinical_guideline text not null
        );
        insert into sae_diagnostics values (1, '97', 'x', 'x', 'x', 'x', 'x', 'x');
        insert into public_health_policies values (1, 'PNAB', 'Legacy PNAB', 'Everyone', 'Keep me');
        insert into pnaism_policies values (1, 'Legacy PNAISM', 'Women', 'Keep me too');
    ''')
    con.commit(); con.close()

    run_upgrade(db_path)
    con = sqlite3.connect(db_path)
    rows = con.execute(
        'select policy_name, directive, status from public_health_policies order by policy_name'
    ).fetchall()
    assert rows == [
        ('PNAB', 'Legacy PNAB', 'needs_review'),
        ('PNAISM', 'Legacy PNAISM', 'needs_review'),
    ]
    assert con.execute(
        "select count(*) from sqlite_master where type='table' and name='pnaism_policies'"
    ).fetchone()[0] == 0
    assert con.execute('select code from sae_diagnostics where id=1').fetchone()[0] == '00097'

