@extends('admin.layout')
@section('title', 'Categorias | Admin')
@section('admin')
<div class="flex items-center justify-between mb-6">
    <h1 class="text-3xl font-display font-black uppercase text-white">Categorias</h1>
</div>
<form action="{{ route('admin.categories.store') }}" method="POST" class="bm-card p-5 mb-6 grid sm:grid-cols-4 gap-3">@csrf
    <input name="name" required placeholder="Nome" class="input-bm" data-testid="cat-name">
    <select name="group" class="input-bm" data-testid="cat-group">@foreach(config('brasilminis.group_labels') as $g=>$l)<option value="{{ $g }}">{{ $l }}</option>@endforeach</select>
    <input name="description" placeholder="Descrição" class="input-bm">
    <button data-testid="save-category-btn" class="btn-buy">+ Adicionar</button>
</form>
<div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
    @foreach($categories as $c)
    <div class="bm-card p-5" data-testid="admin-category-{{ $c->slug }}">
        <div class="flex justify-between">
            <span class="text-bm-yellow text-xs uppercase font-bold">{{ $c->group }}</span>
            <form action="{{ route('admin.categories.destroy', $c) }}" method="POST" onsubmit="return confirm('Remover?')">@csrf @method('DELETE')<button class="text-gray-500 hover:text-red-400 text-sm">✕</button></form>
        </div>
        <p class="text-white font-semibold mt-2">{{ $c->name }}</p>
        <p class="text-gray-500 text-xs mt-1 line-clamp-2">{{ $c->description }}</p>
    </div>
    @endforeach
</div>
@endsection
