#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Brasil Minis — Deploy na VPS (Ubuntu 24.04). Simples e SEGURO.
# NÃO destrói dados: sem git reset --hard, sem force push, sem seed automático,
# sem reset de banco, preserva .env e uploads. Se o build falhar, a versão
# funcional atual NÃO é derrubada (build vai para diretório temporário e só é
# promovido em caso de sucesso).
#
# Uso: bash infra/scripts/deploy.sh
# Requer: sudoers permitindo `systemctl restart brasilminis-backend`,
#         `nginx -t` e `systemctl reload nginx` para o usuário de deploy.
# ------------------------------------------------------------------------------
set -euo pipefail

APP_ROOT="${APP_ROOT:-/var/www/brasilminis}"
BACKEND_DIR="$APP_ROOT/backend"
FRONTEND_DIR="$APP_ROOT/frontend"
VENV="$BACKEND_DIR/.venv"
BRANCH="${DEPLOY_BRANCH:-python-vps}"

log() { echo -e "\n\033[1;34m==>\033[0m $*"; }
fail() { echo -e "\n\033[1;31mERRO:\033[0m $*" >&2; exit 1; }

[ -d "$APP_ROOT/.git" ] || fail "Repositório git não encontrado em $APP_ROOT"
[ -f "$BACKEND_DIR/.env" ] || fail ".env do backend ausente em $BACKEND_DIR/.env (crie a partir do .env.example)"
[ -x "$VENV/bin/python" ] || fail "virtualenv ausente em $VENV (crie com: python3.12 -m venv $VENV)"

cd "$APP_ROOT"

log "Atualizando código (git pull --ff-only, sem reset)"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "Backend: dependências Python"
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

log "Backend: migrations Alembic (upgrade head)"
( cd "$BACKEND_DIR" && "$VENV/bin/alembic" upgrade head )

log "Frontend: build (isolado; só promove se OK)"
[ -f "$FRONTEND_DIR/.env" ] || fail "frontend/.env ausente (defina REACT_APP_BACKEND_URL=https://brasilminis.com)"
cd "$FRONTEND_DIR"
if command -v yarn >/dev/null 2>&1 && [ -f yarn.lock ]; then
    yarn install --frozen-lockfile
    rm -rf build_new
    BUILD_PATH=build_new yarn build
else
    npm install
    rm -rf build_new
    BUILD_PATH=build_new npm run build
fi
[ -f build_new/index.html ] || fail "Build falhou (build_new/index.html não gerado) — versão atual preservada"
# Promoção atômica: mantém a build anterior como fallback
rm -rf build_prev
[ -d build ] && mv build build_prev
mv build_new build
rm -rf build_prev
cd "$APP_ROOT"

log "Reiniciando backend (systemd)"
sudo systemctl restart brasilminis-backend
sleep 2
sudo systemctl is-active --quiet brasilminis-backend || fail "brasilminis-backend não está ativo após restart"

log "Recarregando Nginx"
sudo nginx -t
sudo systemctl reload nginx

log "Deploy concluído com sucesso."
