@extends('layouts.app')
@section('title', 'Criar conta | Brasil Minis')
@section('content')
<div class="min-h-[80vh] grid place-items-center px-4 py-12">
    <div class="w-full max-w-md">
        <div class="text-center mb-8">
            <img src="{{ config('brasilminis.logo_emblem') }}" class="h-16 w-16 mx-auto rounded-xl object-cover" alt="Brasil Minis">
            <h1 class="text-3xl font-display font-black uppercase text-white mt-4">Criar conta</h1>
            <p class="text-gray-500 mt-2 text-sm">Junte-se ao clube dos colecionadores.</p>
        </div>
        <div class="bm-card p-8">
            <form action="{{ route('register') }}" method="POST" class="space-y-4">@csrf
                <input name="name" required placeholder="Nome completo" value="{{ old('name') }}" class="input-bm rounded-full py-3.5" data-testid="register-name">
                <input name="email" type="email" required placeholder="E-mail" value="{{ old('email') }}" class="input-bm rounded-full py-3.5" data-testid="register-email">
                <input name="password" type="password" required placeholder="Senha (mín. 6)" class="input-bm rounded-full py-3.5" data-testid="register-password">
                <input name="password_confirmation" type="password" required placeholder="Confirmar senha" class="input-bm rounded-full py-3.5" data-testid="register-password-confirmation">
                <label class="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" name="newsletter" value="1" checked class="accent-bm-yellow"> Quero receber novidades e promoções</label>
                <button data-testid="register-submit" class="w-full btn-buy">Criar conta →</button>
            </form>
            <p class="text-center text-sm text-gray-400 mt-6">Já tem conta? <a href="{{ route('login') }}" class="text-bm-yellow font-semibold">Entrar</a></p>
        </div>
    </div>
</div>
@endsection
