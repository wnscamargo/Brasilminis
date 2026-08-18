@extends('layouts.app')
@section('title', $product->meta_title ?: $product->name.' | Brasil Minis')
@section('meta_description', $product->meta_description ?: \Illuminate\Support\Str::limit(strip_tags($product->description), 150))

@section('content')
@php
    $discount = ($product->compare_at_price && $product->compare_at_price > $product->price)
        ? (int) round((1 - $product->price / $product->compare_at_price) * 100) : 0;
    $isFav = auth()->check() && auth()->user()->favorites->contains('product_id', $product->id);
@endphp
<div class="max-w-[1400px] mx-auto px-4 lg:px-8 py-8" x-data="{ img: '{{ optional($product->images->first())->path }}', tab: 'desc', rating: 5 }">
    <nav class="flex items-center gap-1.5 text-xs text-gray-500 mb-6 flex-wrap">
        <a href="{{ route('home') }}" class="hover:text-white">Início</a> ›
        <a href="{{ route('catalog.group', $product->group) }}" class="hover:text-white capitalize">{{ $product->group }}</a> ›
        <span class="text-gray-300">{{ $product->name }}</span>
    </nav>

    <div class="grid lg:grid-cols-2 gap-10">
        <div>
            <div class="bm-card overflow-hidden aspect-square">
                <img :src="img" alt="{{ $product->name }}" class="h-full w-full object-cover" data-testid="product-main-image">
            </div>
            @if($product->images->count() > 1)
            <div class="flex gap-3 mt-3">
                @foreach($product->images as $im)
                    <button @click="img='{{ $im->path }}'" class="h-20 w-20 rounded-lg overflow-hidden border-2" :class="img==='{{ $im->path }}' ? 'border-bm-yellow' : 'border-bm-med'">
                        <img src="{{ $im->path }}" class="h-full w-full object-cover">
                    </button>
                @endforeach
            </div>
            @endif
        </div>

        <div>
            @if($product->brand)<span class="text-xs uppercase tracking-[0.25em] text-bm-blue font-bold">{{ $product->brand->name }}</span>@endif
            <h1 class="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white mt-2">{{ $product->name }}</h1>
            <div class="flex flex-wrap items-center gap-2 mt-4">
                @foreach($product->badges ?? [] as $b)<span class="px-3 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full {{ badge_class($b) }}">{{ $b }}</span>@endforeach
            </div>
            @if($product->reviews_count > 0)<div class="mt-4 text-bm-yellow text-sm">★ {{ $product->rating }} · {{ $product->reviews_count }} avaliações</div>@endif

            <div class="mt-6 flex items-end gap-3">
                @if($discount>0)<span class="text-lg text-gray-500 line-through">{{ brl($product->compare_at_price) }}</span>@endif
                <span class="text-4xl font-display font-black text-white">{{ brl($product->price) }}</span>
                @if($discount>0)<span class="mb-1.5 px-2 py-1 text-xs font-bold rounded-full bg-bm-yellow text-bm-black">-{{ $discount }}%</span>@endif
            </div>
            <p class="text-sm text-gray-500 mt-1">Em até 12x no cartão ou PIX à vista</p>
            <p class="text-gray-300 mt-6 leading-relaxed">{{ $product->description }}</p>
            <p class="mt-4 text-sm {{ $product->stock > 0 ? 'text-bm-green' : 'text-red-400' }}">{{ $product->stock > 0 ? $product->stock.' em estoque' : 'Esgotado' }}</p>

            <div class="mt-6 flex flex-wrap gap-3" x-data="{ qty: 1 }">
                <form action="{{ route('cart.add') }}" method="POST" class="flex flex-1 min-w-[220px] gap-3">
                    @csrf
                    <input type="hidden" name="product_id" value="{{ $product->id }}">
                    <div class="flex items-center bm-card">
                        <button type="button" @click="qty = Math.max(1, qty-1)" class="p-3 text-white hover:text-bm-yellow" data-testid="qty-minus">−</button>
                        <span class="w-10 text-center text-white font-semibold" data-testid="qty-value" x-text="qty"></span>
                        <button type="button" @click="qty = Math.min({{ $product->stock }}, qty+1)" class="p-3 text-white hover:text-bm-yellow" data-testid="qty-plus">+</button>
                        <input type="hidden" name="quantity" :value="qty">
                    </div>
                    <button data-testid="buy-now-btn" @disabled($product->stock<=0) class="btn-buy flex-1 py-4 disabled:opacity-40">Comprar Agora</button>
                </form>
                @auth
                <form action="{{ route('favorites.toggle', $product) }}" method="POST">@csrf
                    <button data-testid="detail-fav-btn" class="h-14 w-14 grid place-items-center rounded-full border {{ $isFav ? 'bg-bm-green border-bm-green text-white' : 'bg-bm-black border-white text-white hover:bg-white/10' }}">♥</button>
                </form>
                @endauth
            </div>

            <div class="grid grid-cols-2 gap-3 mt-8">
                <div class="bm-card p-4 flex items-center gap-3 text-sm text-gray-300"><span class="text-bm-yellow">🚚</span> Entrega para todo o Brasil</div>
                <div class="bm-card p-4 flex items-center gap-3 text-sm text-gray-300"><span class="text-bm-yellow">✔</span> Produto 100% original</div>
            </div>
        </div>
    </div>

    {{-- Tabs --}}
    <div class="mt-16">
        <div class="flex gap-2 border-b border-bm-med">
            <button @click="tab='desc'" :class="tab==='desc' ? 'text-bm-yellow border-b-2 border-bm-yellow' : 'text-gray-400'" class="px-5 py-3 text-sm font-semibold uppercase tracking-wide">Descrição</button>
            <button @click="tab='specs'" :class="tab==='specs' ? 'text-bm-yellow border-b-2 border-bm-yellow' : 'text-gray-400'" class="px-5 py-3 text-sm font-semibold uppercase tracking-wide">Especificações</button>
            <button @click="tab='reviews'" :class="tab==='reviews' ? 'text-bm-yellow border-b-2 border-bm-yellow' : 'text-gray-400'" class="px-5 py-3 text-sm font-semibold uppercase tracking-wide">Avaliações ({{ $product->reviews->count() }})</button>
        </div>
        <div class="py-8">
            <div x-show="tab==='desc'"><p class="text-gray-300 leading-relaxed max-w-3xl">{{ $product->description }}</p></div>
            <div x-show="tab==='specs'" x-cloak>
                <div class="max-w-2xl bm-honeycomb rounded-xl overflow-hidden">
                    @forelse($product->attributes as $i => $attr)
                        <div class="flex justify-between px-5 py-3 {{ $i % 2 ? 'bg-black/20' : '' }}"><span class="text-gray-400">{{ $attr->key }}</span><span class="text-white font-medium">{{ $attr->value }}</span></div>
                    @empty
                        <p class="text-gray-500 p-5">Especificações não informadas.</p>
                    @endforelse
                </div>
            </div>
            <div x-show="tab==='reviews'" x-cloak class="grid lg:grid-cols-2 gap-8">
                <div class="space-y-4">
                    @forelse($product->reviews as $r)
                        <div class="bm-card p-5">
                            <div class="flex justify-between"><span class="font-semibold text-white">{{ $r->user->name ?? 'Cliente' }}</span><span class="text-bm-yellow">{{ str_repeat('★', $r->rating) }}</span></div>
                            <p class="text-gray-400 text-sm mt-2">{{ $r->comment }}</p>
                        </div>
                    @empty
                        <p class="text-gray-500">Seja o primeiro a avaliar.</p>
                    @endforelse
                </div>
                @auth
                <form action="{{ route('product.review', $product) }}" method="POST" class="bm-card p-6 h-fit">@csrf
                    <h4 class="font-display font-bold text-white uppercase mb-4">Deixe sua avaliação</h4>
                    <div class="flex gap-1 mb-4">
                        @for($i=1;$i<=5;$i++)<button type="button" @click="rating={{ $i }}" class="text-2xl" :class="rating>={{ $i }} ? 'text-bm-yellow' : 'text-gray-600'">★</button>@endfor
                        <input type="hidden" name="rating" :value="rating">
                    </div>
                    <textarea name="comment" rows="4" required placeholder="Conte o que achou..." class="input-bm"></textarea>
                    <button class="mt-3 btn-cart">Enviar avaliação</button>
                </form>
                @else
                <div class="bm-card p-6 text-gray-400 h-fit">Faça <a href="{{ route('login') }}" class="text-bm-yellow">login</a> para avaliar.</div>
                @endauth
            </div>
        </div>
    </div>

    @if($related->count())
    <div class="mt-16">
        <h2 class="text-2xl lg:text-3xl font-display font-black uppercase text-white mb-8">Produtos relacionados</h2>
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            @foreach($related as $product) @include('partials.product-card') @endforeach
        </div>
    </div>
    @endif
</div>
@endsection
