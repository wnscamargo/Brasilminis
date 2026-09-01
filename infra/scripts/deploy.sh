#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Brasil Minis — Deploy na VPS (Ubuntu 24.04). Simples e SEGURO, com smoke-test.
#
# NÃO destrói dados: sem git reset --hard, sem force push, sem seed automático,
# sem reset de banco, preserva .env e uploads.
#
# Fluxo: git pull -> pip -> alembic upgrade head -> build isolado -> promover build
#        -> restart backend -> aguardar -> checar /api/health -> só então concluir.
# Se o /api/health falhar: rollback SEGURO apenas do FRONTEND (restaura build anterior),
# log claro do motivo e EXIT 1. NÃO faz rollback de migration nem restore de banco.
#
# Uso: bash infra/scripts/deploy.sh
# Requer sudoers p/ systemctl restart brasilminis-backend, nginx -t, systemctl reload nginx.
# ------------------------------------------------------------------------------
set -euo pipefail

APP_ROOT="${APP_ROOT:-/var/www/brasilminis}"
BACKEND_DIR="$APP_ROOT/backend"
FRONTEND_DIR="$APP_ROOT/frontend"
VENV="$BACKEND_DIR/.venv"
BRANCH="${DEPLOY_BRANCH:-python-vps}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/health}"
HEALTH_RETRIES="${HEALTH_RETRIES:-10}"
HEALTH_DELAY="${HEALTH_DELAY:-2}"

log()  { echo -e "\n\033[1;34m==>\033[0m $*"; }
fail() { echo -e "\n\033[1;31mDEPLOY FALHOU:\033[0m $*" >&2; exit 1; }

[ -d "$APP_ROOT/.git" ] || fail "Repositório git não encontrado em $APP_ROOT"
[ -f "$BACKEND_DIR/.env" ] || fail ".env do backend ausente em $BACKEND_DIR/.env"
[ -x "$VENV/bin/python" ] || fail "virtualenv ausente em $VENV"
[ -f "$FRONTEND_DIR/.env" ] || fail "frontend/.env ausente (REACT_APP_BACKEND_URL=https://brasilminis.com)"

cd "$APP_ROOT"
PREV_SHA="$(git rev-parse HEAD)"
log "Commit atual (para rollback manual, se necessário): $PREV_SHA"

log "Atualizando código (git pull --ff-only, sem reset)"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "Backend: dependências Python"
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

log "Backend: migrations Alembic (upgrade head)"
( cd "$BACKEND_DIR" && "$VENV/bin/alembic" upgrade head )

log "Frontend: build isolado (build_new)"
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
[ -f build_new/index.html ] || fail "Build falhou — versão atual preservada (nada promovido)"

log "Promovendo build (mantendo a anterior como build_prev para rollback)"
rm -rf build_prev
[ -d build ] && cp -a build build_prev
rm -rf build && mv build_new build
cd "$APP_ROOT"

log "Reiniciando backend (systemd)"
sudo systemctl restart brasilminis-backend

log "Smoke-test: aguardando /api/health ficar saudável"
HEALTHY=0
for i in $(seq 1 "$HEALTH_RETRIES"); do
    sleep "$HEALTH_DELAY"
    CODE="$(curl -s -o /tmp/bm_health.json -w '%{http_code}' "$HEALTH_URL" || echo 000)"
    if [ "$CODE" = "200" ] && grep -q '"status": *"ok"' /tmp/bm_health.json 2>/dev/null; then
        HEALTHY=1; break
    fi
    echo "   tentativa $i/$HEALTH_RETRIES -> HTTP $CODE ($(cat /tmp/bm_health.json 2>/dev/null))"
done

if [ "$HEALTHY" != "1" ]; then
    echo -e "\n\033[1;31mHEALTH CHECK FALHOU\033[0m — motivo:"
    echo "   HTTP=$CODE body=$(cat /tmp/bm_health.json 2>/dev/null)"
    log "Rollback SEGURO do frontend (restaurando build anterior)"
    if [ -d "$FRONTEND_DIR/build_prev" ]; then
        rm -rf "$FRONTEND_DIR/build_failed"
        mv "$FRONTEND_DIR/build" "$FRONTEND_DIR/build_failed"
        mv "$FRONTEND_DIR/build_prev" "$FRONTEND_DIR/build"
        sudo nginx -t && sudo systemctl reload nginx || true
        echo "   build anterior restaurada. Build problemática em frontend/build_failed."
    else
        echo "   AVISO: build_prev inexistente (primeiro deploy?). Frontend NÃO revertido."
    fi
    echo "   NÃO foi feito rollback de banco/migrations (por segurança)."
    echo "   Para reverter o CÓDIGO manualmente: git checkout $PREV_SHA (sem reset --hard) e re-deploy."
    fail "backend não ficou saudável após restart. Verifique: journalctl -u brasilminis-backend -n 100"
fi

log "Health OK. Recarregando Nginx"
sudo nginx -t
sudo systemctl reload nginx

rm -rf "$FRONTEND_DIR/build_prev"
log "Deploy concluído com sucesso (health: $(cat /tmp/bm_health.json))."
