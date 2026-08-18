@extends('account.layout')
@section('title', 'Pedido #'.$order->order_number)
@section('account')
<div class="bm-card p-6">
    <div class="flex justify-between items-center pb-4 border-b border-bm-med">
        <h2 class="font-display font-bold text-white uppercase">Pedido #{{ $order->order_number }}</h2>
        <span class="px-3 py-1 rounded-full text-xs font-bold uppercase bg-bm-green/20 text-bm-green">{{ $order->statusLabel() }}</span>
    </div>
    <div class="space-y-3 mt-4">
        @foreach($order->items as $i)
        <div class="flex gap-3 items-center">
            <img src="{{ $i->image }}" class="h-14 w-14 rounded-lg object-cover">
            <div class="flex-1"><p class="text-white text-sm">{{ $i->name }}</p><p class="text-gray-500 text-xs">{{ $i->quantity }}x {{ brl($i->price) }}</p></div>
            <span class="text-white text-sm">{{ brl($i->line_total) }}</span>
        </div>
        @endforeach
    </div>
    <div class="border-t border-bm-med mt-4 pt-4 space-y-1 text-sm">
        <div class="flex justify-between text-gray-400"><span>Subtotal</span><span>{{ brl($order->subtotal) }}</span></div>
        @if($order->discount>0)<div class="flex justify-between text-bm-green"><span>Desconto ({{ $order->coupon_code }})</span><span>-{{ brl($order->discount) }}</span></div>@endif
        <div class="flex justify-between text-gray-400"><span>Frete</span><span>{{ $order->shipping==0 ? 'Grátis' : brl($order->shipping) }}</span></div>
        <div class="flex justify-between text-white font-bold text-lg pt-2"><span>Total</span><span>{{ brl($order->total) }}</span></div>
    </div>
    @if($order->address)
    <div class="mt-6 text-sm text-gray-400">
        <p class="text-white font-semibold mb-1">Entrega</p>
        {{ $order->address['recipient'] ?? '' }} — {{ $order->address['street'] ?? '' }}, {{ $order->address['number'] ?? '' }} · {{ $order->address['city'] ?? '' }}/{{ $order->address['state'] ?? '' }}
    </div>
    @endif
    <div class="mt-6">
        <p class="text-white font-semibold text-sm mb-2">Histórico</p>
        @foreach($order->history as $h)
            <p class="text-xs text-gray-500">{{ $h->created_at->format('d/m/Y H:i') }} — {{ \App\Models\Order::STATUS_LABELS[$h->to_status] ?? $h->to_status }} {{ $h->note ? '('.$h->note.')' : '' }}</p>
        @endforeach
    </div>
</div>
@endsection
