<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

/**
 * Conveniência para DEV/HOMOLOGAÇÃO: popula dados essenciais + demo.
 * Usado pelos testes. Em produção prefira `php artisan migrate` +
 * `db:seed --class=EssentialSeeder` e `php artisan bm:create-admin`.
 */
class BrasilMinisSeeder extends Seeder
{
    public function run(): void
    {
        $this->call(EssentialSeeder::class);
        $this->call(DemoSeeder::class);
    }
}
