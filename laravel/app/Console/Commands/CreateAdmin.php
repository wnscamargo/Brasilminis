<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class CreateAdmin extends Command
{
    protected $signature = 'bm:create-admin
        {email : E-mail do administrador}
        {--name=Administrador : Nome}
        {--password= : Senha (se omitida, uma senha forte é gerada e exibida uma única vez)}';

    protected $description = 'Cria (ou promove) um administrador de produção de forma segura, sem senha versionada.';

    public function handle(): int
    {
        $email = strtolower(trim($this->argument('email')));
        $password = $this->option('password') ?: Str::password(16);

        $user = User::updateOrCreate(
            ['email' => $email],
            [
                'name' => $this->option('name'),
                'password' => Hash::make($password),
                'role' => 'admin',
            ]
        );

        $this->info("Administrador pronto: {$user->email}");
        if (! $this->option('password')) {
            $this->warn('Senha gerada (guarde agora, não será exibida novamente):');
            $this->line("  {$password}");
        }

        return self::SUCCESS;
    }
}
