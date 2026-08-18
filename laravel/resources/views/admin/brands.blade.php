@extends('admin.layout')
@section('title', 'Marcas | Admin')
@section('admin')
<h1 class="text-3xl font-display font-black uppercase text-white mb-6">Marcas</h1>
<form action="{{ route('admin.brands.store') }}" method="POST" class="bm-card p-5 mb-6 grid sm:grid-cols-3 gap-3">@csrf
    <input name="name" required placeholder="Nome" class="input-bm" data-testid="brand-name">
    <input name="description" placeholder="Descrição" class="input-bm">
    <button data-testid="save-brand-btn" class="btn-buy">+ Adicionar</button>
</form>
<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
    @foreach($brands as $b)
    <div class="bm-card p-5 flex items-center justify-between" data-testid="admin-brand-{{ $b->slug }}">
        <span class="text-white font-display font-semibold uppercase">{{ $b->name }}</span>
        <form action="{{ route('admin.brands.destroy', $b) }}" method="POST" onsubmit="return confirm('Remover?')">@csrf @method('DELETE')<button class="text-gray-500 hover:text-red-400">✕</button></form>
    </div>
    @endforeach
</div>
@endsection
