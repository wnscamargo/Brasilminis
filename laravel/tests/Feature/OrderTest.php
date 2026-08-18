<?php

use App\Models\User;
use App\Services\OrderService;

beforeEach(function () {
    $this->seed(\Database\Seeders\BrasilMinisSeeder::class);
});

it('cria pedido com baixa de estoque e frete grátis acima de R$300', function () {
    $user = User::where('role', 'client')->first();
    $product = \App\Models\Product::where('price', '>', 300)->first();
    $stockBefore = $product->stock;

    [$order] = app(OrderService::class)->place(
        $user->id,
        [$product->id => 1],
        'pix',
        null,
        ['recipient' => 'X', 'zip' => '01000-000', 'street' => 'Rua', 'number' => '1', 'district' => 'Centro', 'city' => 'SP', 'state' => 'SP'],
    );

    expect($order->shipping)->toEqual('0.00');
    expect($order->status)->toBe('PAID');
    expect($product->fresh()->stock)->toBe($stockBefore - 1);
});

it('aplica cupom percentual respeitando pedido mínimo', function () {
    $service = app(OrderService::class);
    [$discount, $code] = $service->resolveCoupon('BRASIL10', 200);
    expect($code)->toBe('BRASIL10');
    expect($discount)->toEqual(20.0);
});

it('rejeita cupom abaixo do pedido mínimo', function () {
    app(OrderService::class)->resolveCoupon('MINIS20', 100);
})->throws(\Illuminate\Validation\ValidationException::class);
