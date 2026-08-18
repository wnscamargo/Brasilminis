@extends('admin.layout')
@section('title', 'Clientes | Admin')
@section('admin')
<h1 class="text-3xl font-display font-black uppercase text-white mb-6">Clientes</h1>
@if($customers->isEmpty())
    <div class="bm-card p-12 text-center text-gray-400">Nenhum cliente cadastrado ainda.</div>
@else
<div class="bm-card overflow-hidden overflow-x-auto">
    <table class="w-full text-sm">
        <thead class="bg-bm-black text-gray-500 uppercase text-xs"><tr>
            <th class="text-left p-4">Nome</th><th class="text-left p-4">E-mail</th><th class="text-left p-4">Telefone</th><th class="text-left p-4">Pedidos</th><th class="text-left p-4">Newsletter</th>
        </tr></thead>
        <tbody>
        @foreach($customers as $c)
        <tr class="border-t border-bm-med" data-testid="admin-customer-{{ $c->id }}">
            <td class="p-4 text-white">{{ $c->name }}</td>
            <td class="p-4 text-gray-400">{{ $c->email }}</td>
            <td class="p-4 text-gray-400">{{ $c->phone ?: '—' }}</td>
            <td class="p-4 text-white">{{ $c->orders_count }}</td>
            <td class="p-4">{!! $c->newsletter ? '<span class="text-bm-green">Sim</span>' : '<span class="text-gray-600">Não</span>' !!}</td>
        </tr>
        @endforeach
        </tbody>
    </table>
</div>
<div class="mt-6">{{ $customers->links() }}</div>
@endif
@endsection
