#!/usr/bin/env bash
# Bootstrap idempotente do PostgreSQL de PREVIEW (ambiente Emergent, dados efêmeros).
# Recria role/DB da aplicação após reinício de pod, para o backend conseguir conectar.
# NÃO usar em produção (na VPS o Postgres persiste e o role/DB são criados uma vez).
set -uo pipefail

for i in $(seq 1 30); do
  su - postgres -c "psql -tc 'SELECT 1'" >/dev/null 2>&1 && break
  sleep 1
done

su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='brasilminis'\" | grep -q 1 \
  || psql -c \"CREATE ROLE brasilminis LOGIN PASSWORD 'brasilminis';\"" || true
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='brasilminis'\" | grep -q 1 \
  || psql -c \"CREATE DATABASE brasilminis OWNER brasilminis;\"" || true

echo "ensure_db: role/DB brasilminis garantidos."
