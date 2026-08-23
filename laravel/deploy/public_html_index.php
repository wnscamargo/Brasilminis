<?php
/**
 * index.php para o public_html da Locaweb (Laravel FORA da pasta pública).
 *
 * Estrutura REAL confirmada da Locaweb:
 *   /home/storage/d/6c/81/brasilminis1/brasilminis/laravel   <- projeto Laravel (LOCAWEB_PATH)
 *   /home/storage/d/6c/81/brasilminis1/public_html           <- pasta pública do domínio (LOCAWEB_PUBLIC_PATH)
 *
 * O deploy (GitHub Actions) envia:
 *   - o Laravel completo (com vendor/ já pronto) para .../brasilminis/laravel
 *   - o conteúdo de laravel/public/ para .../public_html
 *   - este arquivo como .../public_html/index.php
 *
 * IMPORTANTE: vendor/ é gerado no GitHub Actions e enviado pronto. A Locaweb NÃO roda
 * composer/dump-autoload (php_strip_whitespace/proc_open estão bloqueados).
 */

use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

// public_html e "brasilminis" são irmãos; o Laravel está em brasilminis/laravel
$base = __DIR__.'/../brasilminis/laravel';

// Caminho ABSOLUTO confirmado (descomente se o relativo acima não resolver na Locaweb):
// $base = '/home/storage/d/6c/81/brasilminis1/brasilminis/laravel';

if (file_exists($maintenance = $base.'/storage/framework/maintenance.php')) {
    require $maintenance;
}

require $base.'/vendor/autoload.php';           // vendor pronto (vindo do CI)

$app = require_once $base.'/bootstrap/app.php';

$app->handleRequest(Request::capture());
