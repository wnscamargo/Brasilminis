<?php
/**
 * index.php para o public_html da Locaweb quando o Laravel fica FORA da pasta pública.
 *
 * Estrutura na Locaweb:
 *   /home/usuario/brasilminis         <- projeto Laravel (repositório git)
 *   /home/usuario/public_html         <- pasta pública (aponta o domínio)
 *
 * Copie o CONTEÚDO de brasilminis/public para public_html (ou faça symlink) e
 * substitua o index.php do public_html por este arquivo, ajustando o caminho
 * relativo abaixo (../brasilminis) conforme a sua estrutura real.
 */

use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

$base = __DIR__.'/../brasilminis';

if (file_exists($maintenance = $base.'/storage/framework/maintenance.php')) {
    require $maintenance;
}

require $base.'/vendor/autoload.php';

$app = require_once $base.'/bootstrap/app.php';

$app->handleRequest(Request::capture());
