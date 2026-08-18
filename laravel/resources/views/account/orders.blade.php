@extends('account.layout')
@section('title', 'Meus pedidos | Brasil Minis')
@section('account')
    @forelse($orders as $o)
    <div class="bm-card p-5 mb-4" data-testid="order-{{ $o->order_number }}">
        <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-bm-med">
            <div><span class="text-white font-display font-bold">#{{ $o->order_number }}</span><span class="text-gray-500 text-xs ml-3">{{ $o->created_at->format('d/m/Y') }}</span></div>
            <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-bm-green/20 text-bm-green">{{ $o->statusLabel() }}</span>
        </div>
        <div class="flex gap-2 mt-3 flex-wrap">
            @foreach($o->items as $i)<img src="{{ $i->image }}" title="{{ $i->quantity }}x {{ $i->name }}" class="h-14 w-14 rounded-lg object-cover">@endforeach
        </div>
        <div class="flex justify-between mt-3 text-sm">
            <a href="{{ route('account.order', $o) }}" class="text-gray-400 hover:text-bm-yellow">{{ $o->items->count() }} item(s) · {{ strtoupper($o->payment_method) }} · ver detalhes</a>
            <span class="text-white font-bold">{{ brl($o->total) }}</span>
        </div>
    </div>
    @empty
    <div class="bm-card p-12 text-center text-gray-400">Você ainda não fez pedidos. <a href="{{ route('catalog') }}" class="text-bm-yellow">Comprar agora</a></div>
    @endforelse
@endsection
