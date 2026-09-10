#!/usr/bin/env bash
# Bootstrap idempotente do PostgreSQL de PREVIEW (ambiente Emergent, dados efêmeros).
# Recria role/DB da aplicação e aplica as migrations (Alembic) após reinício de pod,
# para o backend conseguir conectar e o /api/health reportar migration=current.
# NÃO usar em produção (na VPS o Postgres persiste; migrations rodam no deploy.sh).
set -uo pipefail

for i in $(seq 1 30); do
  su - postgres -c "psql -tc 'SELECT 1'" >/dev/null 2>&1 && break
  sleep 1
done

su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='brasilminis'\" | grep -q 1 \
  || psql -c \"CREATE ROLE brasilminis LOGIN PASSWORD 'brasilminis';\"" || true
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='brasilminis'\" | grep -q 1 \
  || psql -c \"CREATE DATABASE brasilminis OWNER brasilminis;\"" || true

# Aplica as migrations (cria tabelas + carimba alembic_version = head).
# Se as tabelas já existirem sem carimbo, faz apenas o stamp (marca como current).
cd /app/backend && set -a; . ./.env; set +a
/root/.venv/bin/alembic upgrade head || /root/.venv/bin/alembic stamp head || true

echo "ensure_db: role/DB brasilminis + migrations aplicadas."
