@extends('layouts.app')
@section('title', 'Marcas | Brasil Minis')
@section('content')
<div class="max-w-[1400px] mx-auto px-4 lg:px-8 py-12">
    <div class="bm-stripe rounded-full max-w-[120px] mb-5"></div>
    <h1 class="text-3xl lg:text-5xl font-display font-black uppercase text-white">Marcas</h1>
    <p class="text-gray-500 mt-2 mb-10">As melhores fabricantes de miniaturas do mundo, reunidas aqui.</p>
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        @foreach($brands as $b)
            <a href="{{ route('catalog', ['brand' => $b->slug]) }}" class="group bm-card p-8 h-40 flex flex-col items-center justify-center text-center hover:border-bm-yellow transition-colors">
                <span class="text-xl font-display font-black uppercase tracking-tight text-white group-hover:text-bm-yellow">{{ $b->name }}</span>
                <span class="text-xs text-gray-500 mt-2">Ver produtos</span>
            </a>
        @endforeach
    </div>
</div>
@endsection
