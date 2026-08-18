@extends('account.layout')
@section('title', 'Alterar senha | Brasil Minis')
@section('account')
<form action="{{ route('account.password.update') }}" method="POST" class="bm-card p-6 space-y-4 max-w-lg">@csrf @method('PUT')
    <input type="password" name="current_password" required placeholder="Senha atual" class="input-bm" data-testid="current-password">
    <input type="password" name="new_password" required placeholder="Nova senha" class="input-bm" data-testid="new-password">
    <input type="password" name="new_password_confirmation" required placeholder="Confirmar nova senha" class="input-bm">
    <button data-testid="password-save" class="btn-buy">Alterar senha</button>
</form>
@endsection
