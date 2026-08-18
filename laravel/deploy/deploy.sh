#!/usr/bin/env bash
# Deploy manual (Locaweb hospedagem compartilhada) — alternativa ao GitHub Actions.
# Estrutura real: /home/storage/.../brasilminis1/brasilminis/app/laravel  (Laravel FORA do public_html)
set -e

APP_DIR="${DEPLOY_PATH:-$HOME/brasilminis/app/laravel}"
PHP="/usr/bin/php83"
COMPOSER="$PHP $HOME/bin/composer"

cd "$APP_DIR"

echo "==> git pull"
git pull origin laravel-migration

echo "==> composer install (contornando noexec com php83)"
$COMPOSER install --no-dev --prefer-dist --optimize-autoloader --no-interaction

echo "==> migrations (NÃO destrutivas — nunca migrate:fresh / db:wipe em produção)"
$PHP artisan migrate --force

echo "==> storage link (fallback se symlink não permitido)"
$PHP artisan storage:link || echo "symlink indisponível — copie storage/app/public para public/storage manualmente"

echo "==> cache de config/rotas/views"
$PHP artisan config:cache
$PHP artisan route:cache
$PHP artisan view:cache

echo "==> Deploy concluído."
