@extends('layouts.app')
@section('title', 'Entrar | Brasil Minis')
@section('content')
<div class="min-h-[80vh] grid place-items-center px-4 py-12">
    <div class="w-full max-w-md">
        <div class="text-center mb-8">
            <img src="{{ config('brasilminis.logo_emblem') }}" class="h-16 w-16 mx-auto rounded-xl object-cover" alt="Brasil Minis">
            <h1 class="text-3xl font-display font-black uppercase text-white mt-4">Entrar</h1>
            <p class="text-gray-500 mt-2 text-sm">Bem-vindo de volta ao universo Brasil Minis.</p>
        </div>
        <div class="bm-card p-8">
            <form action="{{ route('login') }}" method="POST" class="space-y-4">@csrf
                <input name="email" type="email" required placeholder="E-mail" value="{{ old('email') }}" class="input-bm rounded-full py-3.5" data-testid="login-email">
                <input name="password" type="password" required placeholder="Senha" class="input-bm rounded-full py-3.5" data-testid="login-password">
                <div class="text-right"><a href="{{ route('password.request') }}" class="text-xs text-gray-400 hover:text-bm-yellow">Esqueci minha senha</a></div>
                <button data-testid="login-submit" class="w-full btn-buy">Entrar →</button>
            </form>
            <p class="text-center text-sm text-gray-400 mt-6">Não tem conta? <a href="{{ route('register') }}" class="text-bm-yellow font-semibold">Cadastre-se</a></p>
        </div>
    </div>
</div>
@endsection
