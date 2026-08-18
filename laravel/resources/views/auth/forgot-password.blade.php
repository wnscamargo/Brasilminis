@extends('layouts.app')
@section('title', 'Recuperar senha | Brasil Minis')
@section('content')
<div class="min-h-[80vh] grid place-items-center px-4 py-12">
    <div class="w-full max-w-md">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-display font-black uppercase text-white mt-4">Recuperar senha</h1>
            <p class="text-gray-500 mt-2 text-sm">Enviaremos instruções para o seu e-mail.</p>
        </div>
        <div class="bm-card p-8">
            <form action="{{ route('password.email') }}" method="POST" class="space-y-4">@csrf
                <input name="email" type="email" required placeholder="E-mail" class="input-bm rounded-full py-3.5" data-testid="forgot-email">
                <button class="w-full btn-buy">Enviar →</button>
                <p class="text-center text-sm text-gray-400"><a href="{{ route('login') }}" class="text-bm-yellow">Voltar</a></p>
            </form>
        </div>
    </div>
</div>
@endsection
