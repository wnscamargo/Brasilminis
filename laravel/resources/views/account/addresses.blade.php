@extends('account.layout')
@section('title', 'Endereços | Brasil Minis')
@section('account')
<div x-data="{ open: false }">
    <button @click="open=!open" data-testid="add-address-btn" class="mb-4 btn-cart">+ Novo endereço</button>
    <form x-show="open" x-cloak action="{{ route('account.addresses.store') }}" method="POST" class="bm-card p-5 mb-4 grid grid-cols-2 gap-3">@csrf
        @foreach(['recipient'=>'Destinatário','zip'=>'CEP','street'=>'Rua','number'=>'Número','district'=>'Bairro','city'=>'Cidade','state'=>'Estado','complement'=>'Complemento'] as $k=>$l)
            <input name="{{ $k }}" placeholder="{{ $l }}" @required($k!=='complement') class="input-bm" data-testid="new-addr-{{ $k }}">
        @endforeach
        <button class="col-span-2 btn-buy">Salvar endereço</button>
    </form>
    @if($addresses->isEmpty())
        <div class="bm-card p-12 text-center text-gray-400">Nenhum endereço cadastrado.</div>
    @else
    <div class="grid sm:grid-cols-2 gap-4">
        @foreach($addresses as $a)
        <div class="bm-card p-5">
            <div class="flex justify-between">
                <span class="text-bm-yellow text-xs font-bold uppercase">{{ $a->label }}{{ $a->is_default ? ' · Padrão' : '' }}</span>
                <form action="{{ route('account.addresses.delete', $a->id) }}" method="POST">@csrf @method('DELETE')<button class="text-gray-500 hover:text-red-400 text-sm">Remover</button></form>
            </div>
            <p class="text-white text-sm mt-2">{{ $a->recipient }}</p>
            <p class="text-gray-400 text-sm">{{ $a->street }}, {{ $a->number }} {{ $a->complement }}</p>
            <p class="text-gray-400 text-sm">{{ $a->district }} · {{ $a->city }}/{{ $a->state }}</p>
            <p class="text-gray-500 text-xs mt-1">CEP {{ $a->zip }}</p>
        </div>
        @endforeach
    </div>
    @endif
</div>
@endsection
