@extends('layouts.app')
@section('title', 'Carrinho | Brasil Minis')

@section('content')
@php $subtotal = $cart->subtotal(); $shipping = ($subtotal >= 300 || $subtotal == 0) ? 0 : 29.90; $missing = max(0, 300 - $subtotal); @endphp
<div class="max-w-[1200px] mx-auto px-4 lg:px-8 py-10">
    <h1 class="text-3xl lg:text-4xl font-display font-black uppercase text-white mb-8">Carrinho</h1>

    @if($cart->items->isEmpty())
        <div class="bm-card p-16 text-center">
            <p class="text-gray-400">Seu carrinho está vazio.</p>
            <a href="{{ route('catalog') }}" class="inline-block mt-6 btn-buy">Ver produtos →</a>
        </div>
    @else
    <div class="grid lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-4">
            @foreach($cart->items as $item)
            <div class="bm-card p-4 flex gap-4" data-testid="cart-item-{{ $item->product_id }}">
                <a href="{{ route('product', $item->product) }}" class="h-24 w-24 rounded-lg overflow-hidden bg-[#171717] shrink-0">
                    <img src="{{ optional($item->product->images->first())->path }}" class="h-full w-full object-cover">
                </a>
                <div class="flex-1 min-w-0">
                    <a href="{{ route('product', $item->product) }}" class="text-white font-medium hover:text-bm-yellow line-clamp-2">{{ $item->product->name }}</a>
                    <p class="text-bm-yellow font-display font-bold mt-1">{{ brl($item->price) }}</p>
                    <div class="flex items-center justify-between mt-3">
                        <form action="{{ route('cart.update', $item->id) }}" method="POST" class="flex items-center bm-card">@csrf @method('PATCH')
                            <button name="quantity" value="{{ $item->quantity - 1 }}" class="p-2 text-white hover:text-bm-yellow">−</button>
                            <span class="w-8 text-center text-white text-sm">{{ $item->quantity }}</span>
                            <button name="quantity" value="{{ $item->quantity + 1 }}" class="p-2 text-white hover:text-bm-yellow">+</button>
                        </form>
                        <form action="{{ route('cart.remove', $item->id) }}" method="POST">@csrf @method('DELETE')
                            <button data-testid="remove-{{ $item->product_id }}" class="text-gray-500 hover:text-red-400 text-sm">Remover</button>
                        </form>
                    </div>
                </div>
            </div>
            @endforeach
        </div>

        <div class="bm-card p-6 h-fit sticky top-28">
            <h3 class="font-display font-bold text-white uppercase mb-4">Resumo</h3>
            @if($missing > 0)
                <p class="text-xs text-gray-400 mb-4 bg-bm-black rounded-lg p-3 border border-bm-med">Faltam <span class="text-bm-green font-bold">{{ brl($missing) }}</span> para o frete grátis!</p>
            @else
                <p class="text-xs text-bm-green mb-4 bg-bm-green/10 rounded-lg p-3 border border-bm-green/30 font-semibold">Você ganhou frete grátis! 🎉</p>
            @endif
            <div class="space-y-2 text-sm">
                <div class="flex justify-between text-gray-400"><span>Subtotal</span><span class="text-white">{{ brl($subtotal) }}</span></div>
                <div class="flex justify-between text-gray-400"><span>Frete</span><span class="text-white">{{ $shipping == 0 ? 'Grátis' : brl($shipping) }}</span></div>
            </div>
            <div class="border-t border-bm-med mt-4 pt-4 flex justify-between items-baseline">
                <span class="text-white font-semibold">Total</span>
                <span class="text-2xl font-display font-black text-white" data-testid="cart-total">{{ brl($subtotal + $shipping) }}</span>
            </div>
            <a href="{{ route('checkout') }}" data-testid="checkout-btn" class="block text-center w-full mt-6 btn-buy">Finalizar compra →</a>
            <a href="{{ route('catalog') }}" class="block text-center text-sm text-gray-400 hover:text-white mt-4">Continuar comprando</a>
        </div>
    </div>
    @endif
</div>
@endsection
