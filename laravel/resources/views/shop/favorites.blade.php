@extends('layouts.app')
@section('title', 'Favoritos | Brasil Minis')
@section('content')
<div class="max-w-[1400px] mx-auto px-4 lg:px-8 py-10">
    <h1 class="text-3xl lg:text-4xl font-display font-black uppercase text-white mb-8">Favoritos</h1>
    @if($products->isEmpty())
        <div class="bm-card p-16 text-center text-gray-400">Você ainda não favoritou nenhum produto. <a href="{{ route('catalog') }}" class="text-bm-yellow">Explorar</a></div>
    @else
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            @foreach($products as $product) @include('partials.product-card') @endforeach
        </div>
    @endif
</div>
@endsection
