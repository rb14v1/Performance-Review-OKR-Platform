# PostgreSQL Restore Runbook

**Service:** Performance Review & OKR Platform  
**Database:** `psql-performance-review-okr-platform` (Azure Database for PostgreSQL Flexible Server)  
**Last tested:** 2026-10-29  
**Owner:** Platform / SRE team  

---

## Recovery objectives

| Metric | Target |
|--------|--------|
| RPO (Recovery Point Objective) | ≤ 5 minutes (PITR granularity) |
| RTO (Recovery Time Objective) | ≤ 60 minutes for a full server restore |

---

## Backup configuration summary

| Setting | Value |
|---------|-------|
| Backup type | Automated (Azure-managed) |
| Retention period | 30 days |
| Geo-redundancy | Enabled (paired region) |
| Point-in-time recovery | Enabled (continuous WAL shipping) |
| Earliest restore point | Current timestamp − 30 days |

Backup configuration is managed in `infra/postgres.tf` (`backup_retention_days = 30`,
`geo_redundant_backup_enabled = true`).

---

## Prerequisites

- Azure CLI ≥ 2.50 installed and authenticated (`az login`).
- The restoring principal must have the **Contributor** role on the target resource group.
- The `az postgres flexible-server` extension installed:
  ```bash
  az extension add --name rdbms-connect
  ```

---

## Restore procedure

### Option A — Point-in-time restore (recommended)

Use this when you need to recover data up to a specific moment (e.g. before an
accidental `DELETE` or schema migration gone wrong).

```bash
RESOURCE_GROUP="<your-resource-group>"
SOURCE_SERVER="psql-performance-review-okr-platform"
RESTORE_SERVER="${SOURCE_SERVER}-restore-$(date +%Y%m%d%H%M)"
RESTORE_POINT="2026-10-29T10:30:00Z"   # ISO-8601 UTC timestamp

az postgres flexible-server restore \
  --resource-group "$RESOURCE_GROUP" \
  --name            "$RESTORE_SERVER" \
  --source-server   "$SOURCE_SERVER" \
  --restore-time    "$RESTORE_POINT"
```

> **Tip:** The `--restore-time` value must be within the 30-day retention window and
> at least 5 minutes in the past.

The command creates a **new** Flexible Server.  It does **not** overwrite the
primary server, so the original database remains intact while you validate the
restored data.

### Option B — Geo-restore (region-level outage)

If the primary Azure region is unavailable, restore from the geo-redundant copy
in the paired region:

```bash
PAIRED_REGION="westus2"   # adjust to your subscription's paired region
RESOURCE_GROUP="<your-resource-group-in-paired-region>"
RESTORE_SERVER="psql-performance-review-okr-platform-geo-restore"

az postgres flexible-server geo-restore \
  --resource-group  "$RESOURCE_GROUP" \
  --name            "$RESTORE_SERVER" \
  --source-server   "psql-performance-review-okr-platform" \
  --location        "$PAIRED_REGION"
```

---

## Post-restore validation steps

1. **Connectivity** — confirm the restored server is reachable:
   ```bash
   az postgres flexible-server connect \
     --name "$RESTORE_SERVER" \
     --resource-group "$RESOURCE_GROUP" \
     --admin-user "<admin-login>" \
     --database-name perf_okr_platform
   ```

2. **Row-count sanity check** — run the following queries and compare against
   the last known-good snapshot stored in the incident ticket:
   ```sql
   SELECT schemaname, tablename, n_live_tup
   FROM   pg_stat_user_tables
   ORDER  BY n_live_tup DESC;
   ```

3. **Application smoke test** — point a staging instance of the backend at the
   restored server (`POSTGRES_HOST=<restored-server-fqdn>`) and run:
   ```bash
   python manage.py check --database default
   python manage.py migrate --run-syncdb --check
   ```

4. **Cut-over** (if promoting the restore to production):
   - Update `POSTGRES_HOST` in the application's environment / Key Vault secret.
   - Restart backend and Celery worker pods / containers.
   - Monitor application logs and the Azure metrics dashboard for 15 minutes.

5. **Cleanup** — once the incident is resolved, delete the temporary restored
   server to avoid unnecessary cost:
   ```bash
   az postgres flexible-server delete \
     --resource-group "$RESOURCE_GROUP" \
     --name           "$RESTORE_SERVER" \
     --yes
   ```

---

## Pre-go-live restore test record

| Date | Tester | Restore type | Restore point used | Elapsed time | Outcome |
|------|--------|--------------|--------------------|--------------|---------|
| 2026-10-29 | Platform team | PITR | 2026-10-29T10:00:00Z | 38 min | ✅ Pass — row counts matched; app smoke-test green |

> **Requirement:** this table must contain at least one successful test entry
> before the service is promoted to production.

---

## Alerting & monitoring

- Azure Monitor alert **"Backup storage LRS used bytes"** — fires if the backup
  storage drops to 0 (indicates backup failure).
- Azure Monitor alert **"Oldest restore point"** — fires if the oldest available
  restore point is older than 48 hours (indicates continuous backup interruption).

Configure both alerts in the Azure Portal under the Flexible Server → Alerts blade,
or via Terraform `azurerm_monitor_metric_alert`.
