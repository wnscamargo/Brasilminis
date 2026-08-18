<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // Dados essenciais e seguros em qualquer ambiente.
        $this->call(EssentialSeeder::class);

        // Dados DEMO (produtos de exemplo, cupons, banner e usuários de teste)
        // NUNCA em produção — evita credenciais conhecidas em ambiente real.
        if (! app()->environment('production')) {
            $this->call(DemoSeeder::class);
        }
    }
}
