@extends('layouts.app')
@section('title', 'Contato | Brasil Minis')
@section('content')
<div class="max-w-[1100px] mx-auto px-4 lg:px-8 py-12">
    <div class="bm-stripe rounded-full max-w-[120px] mb-5"></div>
    <h1 class="text-3xl lg:text-5xl font-display font-black uppercase text-white">Contato</h1>
    <p class="text-gray-500 mt-2 mb-10">Fale com nossa equipe de especialistas em colecionismo.</p>
    <div class="grid lg:grid-cols-2 gap-8">
        <div class="space-y-4">
            @foreach([['E-mail','contato@brasilminis.com.br'],['WhatsApp','(11) 99999-0000'],['Endereço','São Paulo · SP · Brasil']] as $c)
            <div class="bm-card p-5 flex items-center gap-4">
                <div class="h-11 w-11 grid place-items-center rounded-full border border-bm-med text-bm-yellow">•</div>
                <div><p class="text-xs text-gray-500 uppercase">{{ $c[0] }}</p><p class="text-white font-medium">{{ $c[1] }}</p></div>
            </div>
            @endforeach
        </div>
        <form action="{{ route('contact.send') }}" method="POST" class="bm-card p-6 space-y-4">@csrf
            <input name="name" required placeholder="Seu nome" class="input-bm">
            <input name="email" type="email" required placeholder="Seu e-mail" class="input-bm">
            <textarea name="message" rows="5" required placeholder="Sua mensagem" class="input-bm"></textarea>
            <button class="btn-buy">Enviar mensagem</button>
        </form>
    </div>
</div>
@endsection
