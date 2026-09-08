import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Settings
from observability import SlidingWindowLimiter
from scripts.db_ops import alembic_revision, backup_sqlite, restore_sqlite, sha256_file, sqlite_integrity, verify_backup_metadata


def test_production_configuration_fails_closed_and_safe_example_passes(tmp_path):
    bad = Settings.from_env({'MEDICAL_API_ENV': 'production'})
    errors, _ = bad.validate()
    assert any('ALLOWED_HOSTS' in error for error in errors)
    assert any('PUBLIC_ORIGIN' in error for error in errors)

    env = {
        'MEDICAL_API_ENV': 'production',
        'MEDICAL_API_ALLOWED_HOSTS': 'medical.example.org',
        'MEDICAL_API_PUBLIC_ORIGIN': 'https://medical.example.org',
        'MEDICAL_API_HSTS': 'true',
        'MEDICAL_API_RATE_LIMIT_ENABLED': 'true',
        'MEDICAL_API_TRUSTED_PROXIES': '127.0.0.1,::1',
        'MEDICAL_API_BACKUP_DIR': str(tmp_path),
    }
    safe = Settings.from_env(env)
    assert safe.assert_valid() == []
    wildcard = dict(env, MEDICAL_API_TRUSTED_PROXIES='*')
    assert any('TRUSTED_PROXIES' in e for e in Settings.from_env(wildcard).validate()[0])


def test_sliding_window_rate_limiter_enforces_limit():
    async def scenario():
        limiter = SlidingWindowLimiter(max_clients=100)
        assert (await limiter.check('client', limit=2))[0]
        assert (await limiter.check('client', limit=2))[0]
        allowed, remaining, retry = await limiter.check('client', limit=2)
        assert not allowed and remaining == 0 and retry >= 1
    asyncio.run(scenario())


def test_backup_verify_and_restore_round_trip(tmp_path):
    source = PROJECT_ROOT / 'medical.db'
    backup, metadata_path = backup_sqlite(source, tmp_path / 'backups', keep=3)
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    assert metadata['sha256'] == sha256_file(backup)
    assert metadata['alembic_revision'] == '0007'
    assert sqlite_integrity(backup)[0]
    assert verify_backup_metadata(backup)[0]

    restored = tmp_path / 'restored.db'
    restore_sqlite(backup, restored)
    assert sqlite_integrity(restored)[0]
    assert alembic_revision(restored) == '0007'
    assert sha256_file(restored) == sha256_file(backup)


def test_production_preflight_is_non_mutating_and_passes(tmp_path):
    db = tmp_path / 'runtime.db'
    shutil.copy2(PROJECT_ROOT / 'medical.db', db)
    before = sha256_file(db)
    env = os.environ.copy()
    env.update({
        'MEDICAL_API_ENV': 'production',
        'MEDICAL_API_ALLOWED_HOSTS': 'medical.example.org',
        'MEDICAL_API_PUBLIC_ORIGIN': 'https://medical.example.org',
        'MEDICAL_API_HSTS': 'true',
        'MEDICAL_API_ENABLE_DOCS': 'false',
        'MEDICAL_API_ENFORCE_DEPENDENCY_LOCK': 'false',
        'MEDICAL_API_RATE_LIMIT_ENABLED': 'true',
        'MEDICAL_API_TRUSTED_PROXIES': '127.0.0.1,::1',
        'MEDICAL_API_DATABASE_URL': f'sqlite:///{db}',
        'MEDICAL_API_BACKUP_DIR': str(tmp_path / 'backups'),
    })
    result = subprocess.run(
        [sys.executable, 'scripts/preflight.py'], cwd=PROJECT_ROOT, env=env,
        text=True, capture_output=True, check=True,
    )
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload['status'] == 'ok'
    assert payload['revision'] == '0007'
    assert payload['sae_records'] == 277
    assert payload['classification_links'] == 627
    assert sha256_file(db) == before
