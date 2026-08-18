<?php

namespace Database\Seeders;

use App\Models\Banner;
use App\Models\Brand;
use App\Models\Category;
use App\Models\Coupon;
use App\Models\Product;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class BrasilMinisSeeder extends Seeder
{
    private array $img = [
        'hero' => 'https://images.unsplash.com/photo-1637494873826-795116ba38cc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600',
        'diecast' => [
            'https://images.unsplash.com/photo-1648711727240-7ee250483923?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1642374386978-9d5befc7af96?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1730291559818-a31641df6859?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1642374452721-19886859ef79?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1780577458908-aa868402b3b6?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1752900135471-956e6c4685af?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1594051673969-172a6f721d3c?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
        ],
        'model' => [
            'https://images.unsplash.com/photo-1764308060405-5fd82b66ad11?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1766389647695-bed08ae55f14?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1774682879572-96ec0155fcde?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
        ],
        'apparel' => [
            'https://images.unsplash.com/photo-1616030257764-0fe6a2f05138?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1601063476271-a159c71ab0b3?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1601754664414-aa3e4f42e6d4?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1517942420142-6a296f9ee4b1?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
        ],
        'accessory' => [
            'https://images.unsplash.com/photo-1783253188513-60ccd634a6f6?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1739102174050-85ffaadab43f?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
            'https://images.unsplash.com/photo-1629155362659-c2cf95a01e45?crop=entropy&cs=srgb&fm=jpg&q=85&w=900',
        ],
    ];

    public function run(): void
    {
        // Admin + demo customer
        User::updateOrCreate(['email' => env('ADMIN_EMAIL', 'admin@brasilminis.com')], [
            'name' => env('ADMIN_NAME', 'Administrador'),
            'password' => Hash::make(env('ADMIN_PASSWORD', 'Admin@2025')),
            'role' => 'admin',
        ]);
        User::updateOrCreate(['email' => 'cliente@teste.com'], [
            'name' => 'Cliente Teste', 'password' => Hash::make('senha123'), 'role' => 'client', 'newsletter' => true,
        ]);

        $categories = [
            ['Diecast 1:64', 'miniaturas'], ['Diecast 1:18', 'miniaturas'], ['JDM Legends', 'miniaturas'], ['Supercarros', 'miniaturas'],
            ['Treasure Hunt', 'colecionaveis'], ['Super Treasure Hunt', 'colecionaveis'], ['Premium', 'colecionaveis'],
            ['Edição Limitada', 'colecionaveis'], ['Dioramas', 'colecionaveis'], ['Garagens', 'colecionaveis'],
            ['Displays', 'acessorios'], ['Vitrines', 'acessorios'], ['Cases Acrílicos', 'acessorios'], ['Iluminação LED', 'acessorios'], ['Kits de Limpeza', 'acessorios'],
            ['Bonés', 'vestuario'], ['Camisetas', 'vestuario'], ['Moletons', 'vestuario'], ['Jaquetas', 'vestuario'], ['Mochilas', 'vestuario'],
            ['Gift Card', 'presentes'], ['Mystery Box', 'presentes'], ['Combos', 'presentes'], ['Kits', 'presentes'],
        ];
        $catBySlug = [];
        foreach ($categories as [$name, $group]) {
            $c = Category::updateOrCreate(['slug' => Str::slug($name)], ['name' => $name, 'group' => $group]);
            $catBySlug[$c->slug] = $c->id;
        }

        $brands = ['Hot Wheels', 'Matchbox', 'Mini GT', 'Inno64', 'Kaido House', 'Tomica', 'Greenlight', 'Majorette', 'Tarmac Works', 'M2 Machines'];
        $brandBySlug = [];
        foreach ($brands as $b) {
            $brand = Brand::updateOrCreate(['slug' => Str::slug($b)], ['name' => $b]);
            $brandBySlug[$brand->slug] = $brand->id;
        }

        if (Product::count() === 0) {
            foreach ($this->products() as $p) {
                $product = Product::create([
                    'name' => $p['name'],
                    'slug' => Str::slug($p['name']),
                    'description' => $p['desc'] ?? ($p['name'].' — item premium da curadoria Brasil Minis, ideal para colecionadores exigentes.'),
                    'group' => $p['group'],
                    'category_id' => $catBySlug[$p['category']] ?? null,
                    'brand_id' => isset($p['brand']) ? ($brandBySlug[$p['brand']] ?? null) : null,
                    'price' => $p['price'],
                    'compare_at_price' => $p['compare'] ?? null,
                    'stock' => $p['stock'],
                    'badges' => $p['badges'],
                    'featured' => $p['featured'] ?? false,
                    'is_active' => true,
                ]);
                foreach ($p['images'] as $i => $url) {
                    $product->images()->create(['path' => $url, 'position' => $i]);
                }
                foreach ($p['specs'] ?? [] as $k => $v) {
                    $product->attributes()->create(['key' => $k, 'value' => $v]);
                }
            }
        }

        Banner::updateOrCreate(['title' => 'Sua paixão em miniatura.'], [
            'subtitle' => 'As melhores marcas e edições exclusivas estão aqui.',
            'image' => $this->img['hero'],
            'cta_text' => 'Comprar Agora', 'cta_link' => '/produtos', 'position' => 0, 'active' => true,
        ]);

        foreach ([
            ['BRASIL10', 'percent', 10, 100, '10% de desconto acima de R$100'],
            ['MINIS20', 'percent', 20, 300, '20% de desconto acima de R$300'],
            ['FRETEGRATIS', 'fixed', 29.9, 0, 'Frete grátis'],
        ] as [$code, $type, $value, $min, $desc]) {
            Coupon::updateOrCreate(['code' => $code], ['type' => $type, 'value' => $value, 'min_order' => $min, 'active' => true, 'description' => $desc]);
        }
    }

    private function products(): array
    {
        $d = $this->img['diecast'];
        $m = $this->img['model'];
        $a = $this->img['apparel'];
        $ac = $this->img['accessory'];

        return [
            ['name' => 'Porsche 911 GT3 RS 1:64', 'price' => 89.90, 'category' => 'diecast-1-64', 'group' => 'miniaturas', 'brand' => 'mini-gt', 'images' => [$d[4], $d[5]], 'stock' => 24, 'badges' => ['LANÇAMENTO'], 'featured' => true, 'specs' => ['Escala' => '1:64', 'Material' => 'Zamac', 'Rodas' => 'Borracha real']],
            ['name' => 'Nissan Skyline GT-R R34 1:64', 'price' => 74.90, 'category' => 'jdm-legends', 'group' => 'miniaturas', 'brand' => 'kaido-house', 'images' => [$d[3], $d[2]], 'stock' => 18, 'badges' => ['TREASURE HUNT'], 'featured' => true, 'specs' => ['Escala' => '1:64']],
            ['name' => 'Ford Mustang Boss 302 1:64', 'price' => 59.90, 'category' => 'diecast-1-64', 'group' => 'miniaturas', 'brand' => 'greenlight', 'images' => [$d[0]], 'stock' => 40, 'badges' => ['NOVO'], 'specs' => ['Escala' => '1:64']],
            ['name' => 'Toyota Supra MK4 JDM 1:64', 'price' => 99.90, 'category' => 'jdm-legends', 'group' => 'miniaturas', 'brand' => 'inno64', 'images' => [$d[1]], 'stock' => 12, 'badges' => ['SUPER TH'], 'compare' => 129.90, 'featured' => true, 'specs' => ['Escala' => '1:64', 'Edição' => 'Limitada']],
            ['name' => 'Lamborghini Aventador 1:18', 'price' => 349.90, 'category' => 'diecast-1-18', 'group' => 'miniaturas', 'brand' => 'tarmac-works', 'images' => [$m[0], $m[2]], 'stock' => 8, 'badges' => ['PREMIUM', 'FRETE GRÁTIS'], 'featured' => true, 'specs' => ['Escala' => '1:18', 'Portas' => 'Abrem']],
            ['name' => 'McLaren 720S Amarelo 1:18', 'price' => 379.90, 'category' => 'supercarros', 'group' => 'miniaturas', 'brand' => 'tarmac-works', 'images' => [$m[2], $m[1]], 'stock' => 6, 'badges' => ['EDIÇÃO LIMITADA'], 'compare' => 449.90, 'specs' => ['Escala' => '1:18']],
            ['name' => 'BMW M3 E30 Preto 1:64', 'price' => 69.90, 'category' => 'diecast-1-64', 'group' => 'miniaturas', 'brand' => 'tomica', 'images' => [$d[6]], 'stock' => 30, 'badges' => ['NOVO'], 'specs' => ['Escala' => '1:64']],
            ['name' => 'Honda Civic Type R 1:64', 'price' => 64.90, 'category' => 'jdm-legends', 'group' => 'miniaturas', 'brand' => 'majorette', 'images' => [$d[2]], 'stock' => 22, 'badges' => ['PROMOÇÃO'], 'compare' => 84.90, 'specs' => ['Escala' => '1:64']],
            ['name' => 'Chevrolet Camaro SS 1:64', 'price' => 54.90, 'category' => 'diecast-1-64', 'group' => 'miniaturas', 'brand' => 'm2-machines', 'images' => [$d[0], $d[3]], 'stock' => 35, 'badges' => [], 'specs' => ['Escala' => '1:64']],
            ['name' => 'VW Fusca Racing 1:64', 'price' => 49.90, 'category' => 'diecast-1-64', 'group' => 'miniaturas', 'brand' => 'hot-wheels', 'images' => [$d[1]], 'stock' => 50, 'badges' => ['NOVO'], 'featured' => true, 'specs' => ['Escala' => '1:64']],
            ['name' => 'Set Treasure Hunt 2025 (5 peças)', 'price' => 199.90, 'category' => 'treasure-hunt', 'group' => 'colecionaveis', 'brand' => 'hot-wheels', 'images' => [$d[0], $d[1]], 'stock' => 10, 'badges' => ['TREASURE HUNT', 'FRETE GRÁTIS'], 'featured' => true],
            ['name' => 'Super TH Datsun 240Z', 'price' => 159.90, 'category' => 'super-treasure-hunt', 'group' => 'colecionaveis', 'brand' => 'hot-wheels', 'images' => [$d[3]], 'stock' => 5, 'badges' => ['SUPER TH', 'PRÉ-VENDA'], 'compare' => 189.90],
            ['name' => 'Diorama Posto Retrô 1:64', 'price' => 129.90, 'category' => 'dioramas', 'group' => 'colecionaveis', 'brand' => 'greenlight', 'images' => [$ac[0]], 'stock' => 14, 'badges' => ['LANÇAMENTO']],
            ['name' => 'Garagem 3 Andares 1:64', 'price' => 179.90, 'category' => 'garagens', 'group' => 'colecionaveis', 'brand' => 'greenlight', 'images' => [$ac[1]], 'stock' => 9, 'badges' => ['NOVO']],
            ['name' => 'Display Acrílico 12 Nichos', 'price' => 149.90, 'category' => 'displays', 'group' => 'acessorios', 'images' => [$ac[0], $ac[2]], 'stock' => 20, 'badges' => ['FRETE GRÁTIS'], 'featured' => true],
            ['name' => 'Vitrine LED 1:18', 'price' => 259.90, 'category' => 'vitrines', 'group' => 'acessorios', 'images' => [$ac[1]], 'stock' => 7, 'badges' => ['PREMIUM'], 'compare' => 299.90],
            ['name' => 'Case Acrílico Individual (10un)', 'price' => 79.90, 'category' => 'cases-acrilicos', 'group' => 'acessorios', 'images' => [$ac[2]], 'stock' => 60, 'badges' => []],
            ['name' => 'Kit Fita LED USB Colecionador', 'price' => 89.90, 'category' => 'iluminacao-led', 'group' => 'acessorios', 'images' => [$ac[0]], 'stock' => 25, 'badges' => ['NOVO']],
            ['name' => 'Kit de Limpeza Premium', 'price' => 44.90, 'category' => 'kits-de-limpeza', 'group' => 'acessorios', 'images' => [$ac[2]], 'stock' => 40, 'badges' => ['PROMOÇÃO'], 'compare' => 59.90],
            ['name' => 'Boné Brasil Minis Racing', 'price' => 89.90, 'category' => 'bones', 'group' => 'vestuario', 'images' => [$a[0]], 'stock' => 30, 'badges' => ['NOVO'], 'featured' => true],
            ['name' => 'Camiseta JDM Legends', 'price' => 79.90, 'category' => 'camisetas', 'group' => 'vestuario', 'images' => [$a[2]], 'stock' => 45, 'badges' => ['LANÇAMENTO']],
            ['name' => 'Moletom Premium Carbon', 'price' => 189.90, 'category' => 'moletons', 'group' => 'vestuario', 'images' => [$a[1], $a[3]], 'stock' => 20, 'badges' => ['FRETE GRÁTIS'], 'featured' => true],
            ['name' => 'Jaqueta Racing Team', 'price' => 349.90, 'category' => 'jaquetas', 'group' => 'vestuario', 'images' => [$a[3]], 'stock' => 8, 'badges' => ['PREMIUM'], 'compare' => 399.90],
            ['name' => 'Mochila Colecionador', 'price' => 219.90, 'category' => 'mochilas', 'group' => 'vestuario', 'images' => [$a[1]], 'stock' => 15, 'badges' => []],
            ['name' => 'Gift Card R$ 150', 'price' => 150.00, 'category' => 'gift-card', 'group' => 'presentes', 'images' => [$this->img['hero']], 'stock' => 999, 'badges' => ['NOVO']],
            ['name' => 'Mystery Box Colecionador', 'price' => 149.90, 'category' => 'mystery-box', 'group' => 'presentes', 'images' => [$d[0], $d[1]], 'stock' => 30, 'badges' => ['PROMOÇÃO', 'FRETE GRÁTIS'], 'compare' => 199.90, 'featured' => true, 'desc' => '5 miniaturas surpresa selecionadas pela nossa curadoria.'],
            ['name' => 'Combo Iniciante (3 minis + display)', 'price' => 219.90, 'category' => 'combos', 'group' => 'presentes', 'images' => [$ac[0], $d[2]], 'stock' => 18, 'badges' => ['PROMOÇÃO'], 'compare' => 269.90],
            ['name' => 'Kit Presente JDM', 'price' => 189.90, 'category' => 'kits', 'group' => 'presentes', 'images' => [$d[1], $a[2]], 'stock' => 22, 'badges' => ['NOVO']],
        ];
    }
}
