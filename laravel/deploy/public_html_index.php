<?php
/**
 * index.php para o public_html da Locaweb (Laravel FORA da pasta pública).
 *
 * Estrutura real da Locaweb:
 *   /home/storage/.../brasilminis1/brasilminis/app/laravel   <- projeto Laravel
 *   /home/storage/.../brasilminis1/public_html               <- pasta pública do domínio
 *
 * Copie o CONTEÚDO de .../app/laravel/public para o public_html (ou faça symlink)
 * e substitua o index.php do public_html por este arquivo.
 *
 * Ajuste $base conforme a profundidade real entre public_html e app/laravel.
 * Se necessário, use o caminho ABSOLUTO informado pela Locaweb.
 */

use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

// public_html e "brasilminis" são irmãos; o Laravel está em brasilminis/app/laravel
$base = __DIR__.'/../brasilminis/app/laravel';

// Exemplo com caminho absoluto (descomente e ajuste se o relativo não funcionar):
// $base = '/home/storage/x/yy/zzzzzz/brasilminis1/brasilminis/app/laravel';

if (file_exists($maintenance = $base.'/storage/framework/maintenance.php')) {
    require $maintenance;
}

require $base.'/vendor/autoload.php';   // ../brasilminis/app/laravel/vendor/autoload.php

$app = require_once $base.'/bootstrap/app.php'; // ../brasilminis/app/laravel/bootstrap/app.php

$app->handleRequest(Request::capture());
