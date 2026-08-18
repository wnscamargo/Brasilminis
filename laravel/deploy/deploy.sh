#!/usr/bin/env bash
# Deploy manual (Locaweb hospedagem compartilhada) — alternativa ao GitHub Actions.
set -e

cd ~/brasilminis

echo "==> git pull"
git pull origin main

echo "==> composer install (contornando noexec com php83)"
/usr/bin/php83 ~/bin/composer install --no-dev --prefer-dist --optimize-autoloader --no-interaction

echo "==> migrations (não destrutivas)"
/usr/bin/php83 artisan migrate --force

echo "==> storage link (fallback se symlink não permitido)"
/usr/bin/php83 artisan storage:link || echo "symlink indisponível — usar cópia manual de storage/app/public para public/storage"

echo "==> cache de config/rotas/views"
/usr/bin/php83 artisan config:cache
/usr/bin/php83 artisan route:cache
/usr/bin/php83 artisan view:cache

echo "==> Deploy concluído."
