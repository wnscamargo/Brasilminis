#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Brasil Minis — Backup do PostgreSQL (pg_dump comprimido + timestamp + retenção).
# Gera: $BACKUP_DIR/brasilminis_YYYY-MM-DD_HHMM.sql.gz
#
# Uso (via cron, ex. diário às 03:00):
#   0 3 * * * /var/www/brasilminis/infra/scripts/backup-db.sh >> /var/log/brasilminis-backup.log 2>&1
#
# Configuração por env (ou defaults):
#   DB_NAME (brasilminis) DB_USER (brasilminis_app) DB_HOST (127.0.0.1) DB_PORT (5432)
#   BACKUP_DIR (/var/www/brasilminis/backups) RETENTION_DAYS (14)
#   PGPASSWORD deve vir do ambiente ou de ~/.pgpass (NUNCA versionar senha).
# ------------------------------------------------------------------------------
set -euo pipefail

DB_NAME="${DB_NAME:-brasilminis}"
DB_USER="${DB_USER:-brasilminis_app}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/var/www/brasilminis/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%F_%H%M)"
OUT="$BACKUP_DIR/brasilminis_${STAMP}.sql.gz"

echo "==> Backup de '$DB_NAME' -> $OUT"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --no-owner --no-privileges "$DB_NAME" | gzip -9 > "$OUT"

# valida arquivo não-vazio
[ -s "$OUT" ] || { echo "ERRO: backup vazio, removendo"; rm -f "$OUT"; exit 1; }
echo "==> OK ($(du -h "$OUT" | cut -f1))"

echo "==> Retenção: removendo backups com mais de ${RETENTION_DAYS} dias"
find "$BACKUP_DIR" -name 'brasilminis_*.sql.gz' -type f -mtime +"$RETENTION_DAYS" -print -delete || true
echo "==> Backup concluído."
