@extends('layouts.app')
@section('title', 'Pedido confirmado | Brasil Minis')

@section('content')
<div class="max-w-[700px] mx-auto px-4 py-20 text-center">
    <div class="text-6xl text-bm-green">✓</div>
    <h1 class="text-3xl font-display font-black uppercase text-white mt-6">Pedido confirmado!</h1>
    <p class="text-gray-400 mt-3">Pedido <span class="text-bm-yellow font-bold">#{{ $order->order_number }}</span> recebido com sucesso.</p>

    <div class="bm-card p-6 mt-8 text-left">
        <div class="bg-bm-yellow/10 border border-bm-yellow/30 rounded-lg p-3 mb-4 text-xs text-bm-yellow">
            Pagamento SIMULADO (aprovado). Integração Mercado Pago será ativada em produção.
        </div>
        @if($payment['pix_qr'] ?? false)
            <div class="mb-4">
                <p class="text-white text-sm font-semibold">PIX gerado</p>
                <p class="text-gray-500 text-xs break-all">{{ $payment['pix_qr'] }}</p>
            </div>
        @endif
        <div class="flex justify-between text-sm text-gray-400"><span>Total pago</span><span class="text-white font-bold">{{ brl($order->total) }}</span></div>
    </div>

    <div class="flex gap-3 justify-center mt-8">
        <a href="{{ route('account.order', $order) }}" class="btn-cart">Ver pedido</a>
        <a href="{{ route('catalog') }}" class="border border-white/30 text-white font-semibold rounded-full px-6 py-3">Continuar comprando</a>
    </div>
</div>
@endsection
