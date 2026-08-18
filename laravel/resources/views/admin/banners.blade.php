@extends('admin.layout')
@section('title', 'Banners | Admin')
@section('admin')
<h1 class="text-3xl font-display font-black uppercase text-white mb-6">Banners</h1>
<form action="{{ route('admin.banners.store') }}" method="POST" class="bm-card p-5 mb-6 grid sm:grid-cols-2 gap-3" data-testid="banner-form">@csrf
    <input name="title" required placeholder="Título" class="input-bm" data-testid="banner-title">
    <input name="subtitle" placeholder="Subtítulo" class="input-bm" data-testid="banner-subtitle">
    <input name="image" required placeholder="URL da imagem" class="input-bm col-span-2" data-testid="banner-image">
    <input name="cta_text" placeholder="Texto do botão" class="input-bm">
    <input name="cta_link" placeholder="Link do botão" class="input-bm">
    <input name="position" type="number" value="0" placeholder="Posição" class="input-bm">
    <label class="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" name="active" value="1" checked class="accent-bm-yellow"> Ativo</label>
    <button data-testid="save-banner-btn" class="btn-buy col-span-2">+ Adicionar banner</button>
</form>
<div class="grid md:grid-cols-2 gap-4">
    @foreach($banners as $b)
    <div class="bm-card overflow-hidden" data-testid="admin-banner-{{ $b->id }}">
        <div class="relative h-40">
            <img src="{{ $b->image }}" class="h-full w-full object-cover">
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent"></div>
            <div class="absolute bottom-3 left-4"><p class="text-white font-display font-bold">{{ $b->title }}</p><p class="text-gray-300 text-xs">{{ $b->subtitle }}</p></div>
            @unless($b->active)<span class="absolute top-3 right-3 bg-red-500/80 text-white text-xs px-2 py-1 rounded-full">Inativo</span>@endunless
        </div>
        <div class="p-3 flex justify-end">
            <form action="{{ route('admin.banners.destroy', $b) }}" method="POST" onsubmit="return confirm('Remover?')">@csrf @method('DELETE')<button class="text-gray-400 hover:text-red-400 text-sm">Excluir</button></form>
        </div>
    </div>
    @endforeach
</div>
@endsection
