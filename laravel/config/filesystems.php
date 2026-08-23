<?php

return [
    'default' => env('FILESYSTEM_DISK', 'public'),

    'disks' => [
        'local' => [
            'driver' => 'local',
            'root' => storage_path('app/private'),
            'serve' => true,
            'throw' => false,
        ],

        'public' => [
            'driver' => 'local',
            'root' => storage_path('app/public'),
            'url' => env('APP_URL').'/storage',
            'visibility' => 'public',
            'throw' => false,
        ],

        // Disco público SEM symlink (compatível com hospedagem compartilhada Locaweb).
        // Grava uploads diretamente numa pasta pública controlada. Em produção aponte
        // UPLOADS_ROOT para .../public_html/uploads e UPLOADS_URL para https://dominio/uploads.
        // Não depende de `php artisan storage:link` (symlink() está bloqueado na Locaweb).
        'uploads' => [
            'driver' => 'local',
            'root' => env('UPLOADS_ROOT', public_path('uploads')),
            'url' => env('UPLOADS_URL', env('APP_URL').'/uploads'),
            'visibility' => 'public',
            'throw' => false,
        ],
    ],

    // storage:link NÃO é usado na Locaweb (symlink desabilitado). Mantido apenas para dev local.
    'links' => [
        public_path('storage') => storage_path('app/public'),
    ],
];
