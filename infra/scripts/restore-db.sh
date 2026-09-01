#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Brasil Minis — RESTORE do PostgreSQL a partir de um dump .sql.gz.
# NUNCA roda automaticamente. Operação DESTRUTIVA: exige confirmação explícita.
#
# Uso:
#   bash infra/scripts/restore-db.sh /var/www/brasilminis/backups/brasilminis_2026-09-01_0300.sql.gz
#
# Recomendado: pare o backend antes (sudo systemctl stop brasilminis-backend) e
# suba depois (sudo systemctl start brasilminis-backend).
# ------------------------------------------------------------------------------
set -euo pipefail

DB_NAME="${DB_NAME:-brasilminis}"
DB_USER="${DB_USER:-brasilminis_app}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"

FILE="${1:-}"
[ -n "$FILE" ] || { echo "Uso: $0 <arquivo.sql.gz>"; exit 1; }
[ -f "$FILE" ] || { echo "ERRO: arquivo não encontrado: $FILE"; exit 1; }

echo "!!! ATENÇÃO: isto vai SOBRESCREVER o banco '$DB_NAME' em $DB_HOST:$DB_PORT com:"
echo "    $FILE"
read -r -p "Digite exatamente 'RESTAURAR' para confirmar: " CONFIRM
[ "$CONFIRM" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }

echo "==> Restaurando..."
gunzip -c "$FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
echo "==> Restore concluído. Rode as migrations se necessário: alembic upgrade head"
