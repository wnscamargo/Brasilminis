@extends('layouts.app')
@section('title', 'Checkout | Brasil Minis')

@section('content')
<div class="max-w-[1200px] mx-auto px-4 lg:px-8 py-10">
    <h1 class="text-3xl lg:text-4xl font-display font-black uppercase text-white mb-8">Checkout</h1>
    <form action="{{ route('checkout.store') }}" method="POST" x-data="{ pay: 'pix' }">
        @csrf
        <div class="grid lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 space-y-6">
                <div class="bm-card p-6">
                    <h3 class="font-display font-bold text-white uppercase mb-4">Endereço de entrega</h3>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="col-span-2"><label class="text-xs text-gray-500 block mb-1">Destinatário</label><input name="recipient" value="{{ auth()->user()->name }}" required class="input-bm" data-testid="addr-recipient"></div>
                        <div><label class="text-xs text-gray-500 block mb-1">CEP</label><input name="zip" required class="input-bm" data-testid="addr-zip"></div>
                        <div><label class="text-xs text-gray-500 block mb-1">Estado</label><input name="state" maxlength="2" required class="input-bm" data-testid="addr-state"></div>
                        <div><label class="text-xs text-gray-500 block mb-1">Rua</label><input name="street" required class="input-bm" data-testid="addr-street"></div>
                        <div><label class="text-xs text-gray-500 block mb-1">Número</label><input name="number" required class="input-bm" data-testid="addr-number"></div>
                        <div><label class="text-xs text-gray-500 block mb-1">Bairro</label><input name="district" required class="input-bm" data-testid="addr-district"></div>
                        <div><label class="text-xs text-gray-500 block mb-1">Cidade</label><input name="city" required class="input-bm" data-testid="addr-city"></div>
                        <div class="col-span-2"><label class="text-xs text-gray-500 block mb-1">Complemento</label><input name="complement" class="input-bm" data-testid="addr-complement"></div>
                    </div>
                </div>

                <div class="bm-card p-6">
                    <h3 class="font-display font-bold text-white uppercase mb-4">Pagamento</h3>
                    <div class="grid sm:grid-cols-3 gap-3">
                        @foreach(['pix'=>['PIX','Aprovação imediata'],'card'=>['Cartão','Em até 12x'],'boleto'=>['Boleto','Vence em 3 dias']] as $v=>$info)
                        <label class="p-4 rounded-xl border cursor-pointer transition-colors block" :class="pay==='{{ $v }}' ? 'border-bm-yellow bg-bm-yellow/5' : 'border-bm-med'" data-testid="pay-{{ $v }}">
                            <input type="radio" name="payment_method" value="{{ $v }}" x-model="pay" class="hidden">
                            <p class="text-white text-sm font-semibold">{{ $info[0] }}</p>
                            <p class="text-gray-500 text-xs">{{ $info[1] }}</p>
                        </label>
                        @endforeach
                    </div>
                    <p class="text-xs text-bm-yellow mt-4 bg-bm-yellow/10 border border-bm-yellow/30 rounded-lg p-3">Pagamento SIMULADO (mock). Integração Mercado Pago será ativada em produção.</p>
                </div>
            </div>

            <div class="bm-card p-6 h-fit sticky top-28">
                <h3 class="font-display font-bold text-white uppercase mb-4">Resumo</h3>
                <div class="max-h-48 overflow-y-auto space-y-3 mb-4">
                    @foreach($cart->items as $i)
                    <div class="flex gap-3 items-center">
                        <img src="{{ optional($i->product->images->first())->path }}" class="h-12 w-12 rounded-lg object-cover">
                        <div class="flex-1 min-w-0"><p class="text-xs text-white line-clamp-1">{{ $i->product->name }}</p><p class="text-xs text-gray-500">{{ $i->quantity }}x {{ brl($i->price) }}</p></div>
                    </div>
                    @endforeach
                </div>
                <div class="flex gap-2 mb-4">
                    <input form="coupon-form" name="code" value="{{ $coupon }}" placeholder="Cupom" data-testid="coupon-input" class="input-bm rounded-full">
                    <button form="coupon-form" type="submit" data-testid="apply-coupon" class="btn-cart px-4 py-2 whitespace-nowrap">Aplicar</button>
                </div>
                <div class="space-y-2 text-sm">
                    <div class="flex justify-between text-gray-400"><span>Subtotal</span><span class="text-white">{{ brl($subtotal) }}</span></div>
                    @if($discount>0)<div class="flex justify-between text-bm-green"><span>Desconto</span><span>-{{ brl($discount) }}</span></div>@endif
                    <div class="flex justify-between text-gray-400"><span>Frete</span><span class="text-white">{{ $shipping==0 ? 'Grátis' : brl($shipping) }}</span></div>
                </div>
                <div class="border-t border-bm-med mt-4 pt-4 flex justify-between items-baseline">
                    <span class="text-white font-semibold">Total</span>
                    <span class="text-2xl font-display font-black text-white" data-testid="checkout-total">{{ brl($total) }}</span>
                </div>
                <button data-testid="place-order-btn" class="w-full mt-6 btn-buy">Pagar agora</button>
            </div>
        </div>
    </form>
    <form id="coupon-form" action="{{ route('checkout.coupon') }}" method="POST" class="hidden">@csrf</form>
</div>
@endsection
