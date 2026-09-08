# Medical API — Canonical Production Operations

## Production layout

The authoritative production layout is:

- application: `/opt/medical-api/app`
- runtime database: `/var/lib/medical-api/medical.db`
- database backups: `/var/lib/medical-api/backups`
- production environment: `/etc/medical-api/medical-api.env`
- application service: `medical-api.service`
- backup service: `medical-api-backup.service`
- backup timer: `medical-api-backup.timer`

The application is bound to loopback port 8000 and is exposed publicly
only through nginx.

The historical symlink/release-tree deployment topology is retired and
must not be used for production recovery.

## Database backup

The production backup service executes:

`/opt/medical-api/app/.venv/bin/python /opt/medical-api/app/scripts/backup_db.py --keep 14`

The timer runs daily at 03:15 UTC with up to 15 minutes randomized
delay and is persistent across downtime.

A usable backup must pass all of the following:

1. SQLite integrity check.
2. Adjacent metadata validation.
3. SHA-256 verification.
4. Expected Alembic revision.
5. Release/content compatibility checks appropriate to that version.

A checksum-valid file alone is not sufficient recovery evidence.

## Failure-atomic rollback

Rollback is a code-and-database pair operation.

`scripts/rollback_release.py` requires:

1. a complete rollback application tree staged separately from the
   active application;
2. the staging tree and active application on the same filesystem;
3. an integrity-clean rollback SQLite database;
4. rollback DB revision equal to rollback code migration head;
5. successful target preflight against a disposable copy of that DB;
6. integrity-clean current DB;
7. `medical-api.service` confirmed stopped.

Only after all validation succeeds does mutation begin.

The helper first creates a verified safety backup of the current DB,
then switches the application directory. The rollback DB is restored
only after the code switch succeeds.

If any post-switch operation fails, the helper restores both the
previous application tree and the safety DB before returning failure.

A failed rollback therefore must not leave a mixed code/database pair.

## Recovery procedure

1. Verify public and local production health.
2. Verify rollback archive checksum.
3. Extract the rollback code and DB into a temporary root-controlled
   staging area on the same filesystem as the active application.
4. Adapt runtime paths to the canonical production layout without
   altering clinical content.
5. Preflight the rollback code against a disposable rollback DB copy.
6. Create and verify a fresh current-production DB backup.
7. Stop `medical-api.service`.
8. Confirm the service and loopback listener are stopped.
9. Execute the failure-atomic rollback helper with its explicit
   confirmation token.
10. Start `medical-api.service`.
11. Verify local/public readiness, API version, DB revision, clinical
    sentinel data and service restart state.
12. Verify nginx, Fail2ban, Tailscale, Docker/containerd and TeamSpeak.
13. Retain the pre-rollback safety DB until rollback acceptance.

The retained cold rollback archive contains historical deployment
artifacts and must not be activated by copying its old service,
environment, nginx or port configuration directly into production.

Cold-recovery sign-off requires a disposable compatible-host rehearsal.

## Protected shared-host components

Medical API deployment/recovery procedures must not modify:

- Tailscale
- Docker/containerd
- TeamSpeak
- firewall, iptables or nftables
- routing
- network sysctls
- SSH configuration

Fail2ban configuration must also remain untouched except during a
separately reviewed Fail2ban-aware nginx logging change.
