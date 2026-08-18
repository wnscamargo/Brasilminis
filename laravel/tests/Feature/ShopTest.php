<?php

use App\Models\User;

beforeEach(function () {
    $this->seed(\Database\Seeders\BrasilMinisSeeder::class);
});

it('mostra a home com produtos em destaque', function () {
    $this->get('/')->assertOk()->assertSee('Sua paixão em miniatura', false);
});

it('lista o catálogo com os produtos semeados', function () {
    $this->get('/produtos')->assertOk()->assertSee('produto(s) encontrado(s)');
});

it('permite registrar um novo cliente', function () {
    $res = $this->post('/cadastro', [
        'name' => 'Novo Cliente',
        'email' => 'novo@teste.com',
        'password' => 'senha123',
        'password_confirmation' => 'senha123',
    ]);
    $res->assertRedirect();
    $this->assertDatabaseHas('users', ['email' => 'novo@teste.com', 'role' => 'client']);
});

it('faz login do admin e acessa o painel', function () {
    $admin = User::where('role', 'admin')->first();
    $this->actingAs($admin)->get('/admin')->assertOk()->assertSee('Dashboard');
});

it('bloqueia clientes no painel admin', function () {
    $client = User::where('role', 'client')->first();
    $this->actingAs($client)->get('/admin')->assertForbidden();
});

it('adiciona ao carrinho e calcula o total', function () {
    $product = \App\Models\Product::first();
    $this->post('/carrinho', ['product_id' => $product->id, 'quantity' => 2])->assertRedirect();
    $this->get('/carrinho')->assertOk()->assertSee('Total');
});
