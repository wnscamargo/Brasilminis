#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Pós-deploy MANUAL na Locaweb (hospedagem compartilhada, PHP 8.3).
#
# IMPORTANTE:
#   - O BUILD (composer install / vite build) acontece SOMENTE no GitHub Actions.
#   - A Locaweb NÃO roda composer, npm, dump-autoload, symlink, exec ou proc_open.
#   - Este script executa APENAS comandos Artisan e é tolerante a funções bloqueadas.
#   - Use-o só se precisar rodar o pós-deploy à mão via SSH (o CI já faz isso sozinho).
#
# Estrutura real da Locaweb:
#   LOCAWEB_PATH        = /home/storage/d/6c/81/brasilminis1/brasilminis/laravel  (Laravel FORA do public_html)
#   LOCAWEB_PUBLIC_PATH = /home/storage/d/6c/81/brasilminis1/public_html          (pasta pública do domínio)
#
# Uso:
#   LOCAWEB_PATH=/caminho/para/laravel LOCAWEB_PUBLIC_PATH=/caminho/para/public_html bash deploy/deploy.sh
# ------------------------------------------------------------------------------
set -uo pipefail

PHP="${PHP_BIN:-/usr/bin/php83}"
APP_DIR="${LOCAWEB_PATH:-$HOME/brasilminis/laravel}"
PUBLIC_DIR="${LOCAWEB_PUBLIC_PATH:-$HOME/public_html}"

cd "$APP_DIR" || { echo "ERRO: não foi possível acessar $APP_DIR"; exit 1; }

echo "==> Verificando artefato (vendor/ deve ter vindo pronto do GitHub Actions)"
if [ ! -f vendor/autoload.php ]; then
  echo "ERRO: vendor/autoload.php ausente. O build deve ser feito no GitHub Actions e enviado por rsync."
  echo "       NÃO rode 'composer install' aqui — a Locaweb bloqueia php_strip_whitespace/proc_open."
  exit 1
fi

echo "==> Garantindo diretórios graváveis (sem symlink — proibido na Locaweb)"
mkdir -p storage/framework/sessions storage/framework/views storage/framework/cache/data storage/logs bootstrap/cache "$PUBLIC_DIR/uploads"
chmod -R 775 storage bootstrap/cache 2>/dev/null || true

echo "==> Migrations (NÃO destrutivas — nunca migrate:fresh / db:wipe em produção)"
"$PHP" artisan migrate --force || echo "AVISO: migrate falhou — verifique DB_* no .env"

echo "==> Cache de config/rotas/views (com fallback se função bloqueada interferir)"
"$PHP" artisan config:cache || { echo "config:cache falhou — config:clear"; "$PHP" artisan config:clear || true; }
"$PHP" artisan route:cache  || { echo "route:cache falhou — route:clear";   "$PHP" artisan route:clear  || true; }
"$PHP" artisan view:cache   || { echo "view:cache falhou — view:clear";      "$PHP" artisan view:clear   || true; }

echo "==> Pós-deploy concluído (storage:link NÃO utilizado — uploads vão para public/uploads)."
