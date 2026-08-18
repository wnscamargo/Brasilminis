@extends('layouts.app')
@section('title', 'Catálogo | Brasil Minis')

@section('content')
<div class="max-w-[1400px] mx-auto px-4 lg:px-8 py-10">
    <div class="bm-stripe rounded-full max-w-[120px] mb-5"></div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
            <h1 class="text-3xl lg:text-5xl font-display font-black uppercase tracking-tight text-white" data-testid="catalog-title">
                {{ $group ? (config('brasilminis.group_labels')[$group] ?? $group) : (request('search') ? 'Resultados: "'.request('search').'"' : (request('badge') ?: (request('on_sale') ? 'Promoções' : 'Todos os produtos'))) }}
            </h1>
            <p class="text-gray-500 mt-2">{{ $products->total() }} produto(s) encontrado(s)</p>
        </div>
        <form method="GET" class="flex items-center gap-3">
            @foreach(request()->except('sort','page') as $k => $v)<input type="hidden" name="{{ $k }}" value="{{ $v }}">@endforeach
            <select name="sort" onchange="this.form.submit()" data-testid="sort-select" class="input-bm bg-bm-dark">
                @foreach(['recent'=>'Mais recentes','price_asc'=>'Menor preço','price_desc'=>'Maior preço','rating'=>'Melhor avaliados','name'=>'Nome (A-Z)'] as $v=>$l)
                    <option value="{{ $v }}" @selected(request('sort')===$v)>{{ $l }}</option>
                @endforeach
            </select>
        </form>
    </div>

    <div class="flex gap-8">
        <aside class="w-64 shrink-0 hidden lg:block">
            <div class="bm-card p-5 sticky top-28">
                <h4 class="text-xs uppercase tracking-widest text-bm-yellow font-bold mb-3">Categorias</h4>
                <div class="space-y-1 mb-6 max-h-64 overflow-y-auto">
                    <a href="{{ route($group ? 'catalog.group' : 'catalog', $group ?? []) }}" class="block text-sm px-3 py-1.5 rounded-lg {{ !request('category') ? 'bg-bm-blue text-white' : 'text-gray-400 hover:text-white hover:bg-white/5' }}">Todas</a>
                    @foreach($categories as $c)
                        <a href="{{ request()->fullUrlWithQuery(['category' => $c->slug]) }}" class="block text-sm px-3 py-1.5 rounded-lg {{ request('category')===$c->slug ? 'bg-bm-blue text-white' : 'text-gray-400 hover:text-white hover:bg-white/5' }}">{{ $c->name }}</a>
                    @endforeach
                </div>
                <h4 class="text-xs uppercase tracking-widest text-bm-yellow font-bold mb-3">Marcas</h4>
                <div class="space-y-1 max-h-64 overflow-y-auto">
                    <a href="{{ request()->fullUrlWithQuery(['brand' => null]) }}" class="block text-sm px-3 py-1.5 rounded-lg {{ !request('brand') ? 'bg-bm-blue text-white' : 'text-gray-400 hover:text-white hover:bg-white/5' }}">Todas</a>
                    @foreach($brands as $b)
                        <a href="{{ request()->fullUrlWithQuery(['brand' => $b->slug]) }}" class="block text-sm px-3 py-1.5 rounded-lg {{ request('brand')===$b->slug ? 'bg-bm-blue text-white' : 'text-gray-400 hover:text-white hover:bg-white/5' }}">{{ $b->name }}</a>
                    @endforeach
                </div>
            </div>
        </aside>

        <div class="flex-1">
            @if($products->count())
                <div class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6" data-testid="products-grid">
                    @foreach($products as $product) @include('partials.product-card') @endforeach
                </div>
                <div class="mt-10">{{ $products->links() }}</div>
            @else
                <div class="bm-card p-16 text-center text-gray-400">Nenhum produto encontrado com os filtros selecionados.</div>
            @endif
        </div>
    </div>
</div>
@endsection
