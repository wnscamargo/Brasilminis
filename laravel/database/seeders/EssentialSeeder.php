<?php

namespace Database\Seeders;

use App\Models\Brand;
use App\Models\Category;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

/**
 * Dados ESSENCIAIS e seguros para qualquer ambiente (inclusive produção):
 * categorias e marcas. NÃO cria usuários nem credenciais.
 */
class EssentialSeeder extends Seeder
{
    public function run(): void
    {
        $categories = [
            ['Diecast 1:64', 'miniaturas'], ['Diecast 1:18', 'miniaturas'], ['JDM Legends', 'miniaturas'], ['Supercarros', 'miniaturas'],
            ['Treasure Hunt', 'colecionaveis'], ['Super Treasure Hunt', 'colecionaveis'], ['Premium', 'colecionaveis'],
            ['Edição Limitada', 'colecionaveis'], ['Dioramas', 'colecionaveis'], ['Garagens', 'colecionaveis'],
            ['Displays', 'acessorios'], ['Vitrines', 'acessorios'], ['Cases Acrílicos', 'acessorios'], ['Iluminação LED', 'acessorios'], ['Kits de Limpeza', 'acessorios'],
            ['Bonés', 'vestuario'], ['Camisetas', 'vestuario'], ['Moletons', 'vestuario'], ['Jaquetas', 'vestuario'], ['Mochilas', 'vestuario'],
            ['Gift Card', 'presentes'], ['Mystery Box', 'presentes'], ['Combos', 'presentes'], ['Kits', 'presentes'],
        ];
        foreach ($categories as [$name, $group]) {
            Category::updateOrCreate(['slug' => Str::slug($name)], ['name' => $name, 'group' => $group]);
        }

        foreach (['Hot Wheels', 'Matchbox', 'Mini GT', 'Inno64', 'Kaido House', 'Tomica', 'Greenlight', 'Majorette', 'Tarmac Works', 'M2 Machines'] as $b) {
            Brand::updateOrCreate(['slug' => Str::slug($b)], ['name' => $b]);
        }
    }
}
