@extends('account.layout')
@section('title', 'Meus dados | Brasil Minis')
@section('account')
<form action="{{ route('account.profile.update') }}" method="POST" class="bm-card p-6 space-y-4 max-w-lg">@csrf @method('PUT')
    <div><label class="text-xs text-gray-500 block mb-1">Nome</label><input name="name" value="{{ auth()->user()->name }}" class="input-bm" data-testid="profile-name"></div>
    <div><label class="text-xs text-gray-500 block mb-1">E-mail</label><input value="{{ auth()->user()->email }}" disabled class="input-bm opacity-60"></div>
    <div><label class="text-xs text-gray-500 block mb-1">Telefone</label><input name="phone" value="{{ auth()->user()->phone }}" class="input-bm" data-testid="profile-phone"></div>
    <label class="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" name="newsletter" value="1" @checked(auth()->user()->newsletter) class="accent-bm-yellow"> Receber newsletter</label>
    <button data-testid="profile-save" class="btn-buy">Salvar alterações</button>
</form>
@endsection
