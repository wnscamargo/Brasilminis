@extends('layouts.app')
@section('title', 'Brasil Minis | Sua paixão em miniatura')

@section('content')
@php $hero = $banner?->image ?? 'https://images.unsplash.com/photo-1637494873826-795116ba38cc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600'; @endphp
<section class="relative min-h-[88vh] flex items-center overflow-hidden">
    <img src="{{ $hero }}" alt="Garagem premium" class="absolute inset-0 h-full w-full object-cover">
    <div class="absolute inset-0 bg-gradient-to-r from-bm-black via-bm-black/85 to-bm-black/30"></div>
    <div class="relative max-w-[1400px] mx-auto px-4 lg:px-8 w-full">
        <div class="max-w-2xl">
            <span class="inline-flex items-center gap-2 text-bm-yellow text-xs uppercase tracking-[0.3em] font-semibold mb-5"><span class="h-px w-8 bg-bm-yellow"></span> Brasil Minis</span>
            <h1 class="text-5xl lg:text-7xl font-display font-black uppercase tracking-tighter text-white leading-[0.95]">{{ $banner?->title ?? 'Sua paixão em miniatura.' }}</h1>
            <p class="mt-6 text-lg lg:text-xl text-gray-300 max-w-lg">{{ $banner?->subtitle ?? 'As melhores marcas e edições exclusivas estão aqui.' }}</p>
            <div class="mt-9 flex flex-wrap gap-4">
                <a href="{{ route('catalog') }}" data-testid="hero-comprar" class="btn-buy shadow-[0_0_25px_rgba(255,193,7,0.35)] py-4">Comprar Agora →</a>
                <a href="{{ route('catalog', ['badge' => 'LANÇAMENTO']) }}" data-testid="hero-lancamentos" class="border border-white/30 text-white font-semibold uppercase tracking-wider rounded-full px-8 py-4 hover:bg-white/10 transition-colors">Ver Lançamentos</a>
            </div>
        </div>
    </div>
</section>

@include('partials.trust')

<section class="max-w-[1400px] mx-auto px-4 lg:px-8 py-20">
    <span class="text-bm-yellow text-xs uppercase tracking-[0.3em] font-semibold">Explore</span>
    <h2 class="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white mt-2">Categorias</h2>
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mt-8">
        @foreach(config('brasilminis.group_labels') as $slug => $label)
            <a href="{{ route('catalog.group', $slug) }}" data-testid="group-card-{{ $slug }}" class="group block bm-card p-6 h-32 flex flex-col justify-between hover:border-bm-yellow transition-colors">
                <span class="text-3xl font-display font-black text-bm-med group-hover:text-bm-blue transition-colors">0{{ $loop->iteration }}</span>
                <span class="text-sm font-semibold uppercase tracking-wide text-white">{{ $label }}</span>
            </a>
        @endforeach
    </div>
</section>

<section class="max-w-[1400px] mx-auto px-4 lg:px-8 pb-8">
    <div class="flex items-end justify-between">
        <div><span class="text-bm-yellow text-xs uppercase tracking-[0.3em] font-semibold">Destaques</span>
        <h2 class="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white mt-2">Mais Vendidos</h2></div>
        <a href="{{ route('catalog') }}" class="text-sm text-gray-400 hover:text-bm-yellow">Ver tudo →</a>
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mt-8">
        @foreach($featured as $product) @include('partials.product-card') @endforeach
    </div>
</section>

@if($launches->count())
<section class="max-w-[1400px] mx-auto px-4 lg:px-8 py-16">
    <div class="flex items-end justify-between">
        <div><span class="text-bm-yellow text-xs uppercase tracking-[0.3em] font-semibold">Novidades</span>
        <h2 class="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white mt-2">Lançamentos</h2></div>
        <a href="{{ route('catalog', ['badge' => 'LANÇAMENTO']) }}" class="text-sm text-gray-400 hover:text-bm-yellow">Ver tudo →</a>
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mt-8">
        @foreach($launches as $product) @include('partials.product-card') @endforeach
    </div>
</section>
@endif

<section class="max-w-[1400px] mx-auto px-4 lg:px-8 py-4">
    <div class="relative overflow-hidden rounded-3xl border border-bm-med p-10 lg:p-16 bg-[#161616]">
        <div class="bm-stripe absolute top-0 left-0 right-0"></div>
        <div class="max-w-xl">
            <span class="text-bm-green uppercase tracking-[0.3em] text-xs font-bold">Frete Grátis</span>
            <h3 class="text-3xl lg:text-4xl font-display font-black uppercase text-white mt-3 leading-tight">Acima de R$300 o frete é por nossa conta</h3>
            <p class="text-gray-400 mt-3">Monte sua coleção e economize. Válido para todo o Brasil.</p>
            <a href="{{ route('catalog') }}" class="inline-block mt-6 btn-buy">Aproveitar →</a>
        </div>
    </div>
</section>

@if($sale->count())
<section class="max-w-[1400px] mx-auto px-4 lg:px-8 py-16">
    <div class="flex items-end justify-between">
        <div><span class="text-bm-yellow text-xs uppercase tracking-[0.3em] font-semibold">Ofertas</span>
        <h2 class="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white mt-2">Promoções</h2></div>
        <a href="{{ route('catalog', ['on_sale' => 1]) }}" class="text-sm text-gray-400 hover:text-bm-yellow">Ver tudo →</a>
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mt-8">
        @foreach($sale as $product) @include('partials.product-card') @endforeach
    </div>
</section>
@endif

<section class="max-w-[1400px] mx-auto px-4 lg:px-8 py-12">
    <h2 class="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white">Marcas</h2>
    <div class="flex flex-wrap gap-3 mt-8">
        @foreach($brands as $b)
            <a href="{{ route('catalog', ['brand' => $b->slug]) }}" class="px-6 py-3 bm-card hover:border-bm-blue transition-colors text-sm font-display font-semibold uppercase tracking-wider text-gray-200">{{ $b->name }}</a>
        @endforeach
    </div>
</section>
@endsection
