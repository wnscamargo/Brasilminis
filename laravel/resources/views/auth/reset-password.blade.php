@extends('layouts.app')
@section('title', 'Nova senha | Brasil Minis')
@section('content')
<div class="min-h-[80vh] grid place-items-center px-4 py-12">
    <div class="w-full max-w-md">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-display font-black uppercase text-white mt-4">Nova senha</h1>
            <p class="text-gray-500 mt-2 text-sm">Defina sua nova senha de acesso.</p>
        </div>
        <div class="bm-card p-8">
            <form action="{{ route('password.store') }}" method="POST" class="space-y-4">@csrf
                <input type="hidden" name="token" value="{{ $token }}">
                <input name="email" type="email" required value="{{ $email }}" placeholder="E-mail" class="input-bm rounded-full py-3.5">
                <input name="password" type="password" required placeholder="Nova senha" class="input-bm rounded-full py-3.5" data-testid="reset-password">
                <input name="password_confirmation" type="password" required placeholder="Confirmar senha" class="input-bm rounded-full py-3.5">
                <button class="w-full btn-buy">Redefinir →</button>
            </form>
        </div>
    </div>
</div>
@endsection
