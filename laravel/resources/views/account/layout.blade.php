@extends('layouts.app')
@section('content')
<div class="max-w-[1200px] mx-auto px-4 lg:px-8 py-10">
    <div class="flex items-center gap-4 mb-8">
        <div class="h-14 w-14 rounded-full bg-bm-blue grid place-items-center text-white font-display font-bold text-xl">{{ substr(auth()->user()->name, 0, 1) }}</div>
        <div>
            <h1 class="text-2xl font-display font-black uppercase text-white">Olá, {{ \Illuminate\Support\Str::of(auth()->user()->name)->before(' ') }}</h1>
            <p class="text-gray-500 text-sm">{{ auth()->user()->email }}</p>
        </div>
        @if(auth()->user()->isAdmin())
            <a href="{{ route('admin.dashboard') }}" class="ml-auto bg-bm-green text-white text-sm font-semibold rounded-full px-5 py-2.5" data-testid="go-admin">Painel Admin</a>
        @endif
    </div>

    <div class="grid lg:grid-cols-4 gap-8">
        <aside class="bm-card p-3 h-fit">
            @php $nav = ['account.orders'=>'Pedidos','account.addresses'=>'Endereços','account.profile'=>'Meus Dados','account.password'=>'Senha']; @endphp
            @foreach($nav as $r => $l)
                <a href="{{ route($r) }}" data-testid="account-tab-{{ \Illuminate\Support\Str::afterLast($r,'.') }}"
                   class="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors {{ request()->routeIs($r) ? 'bg-bm-blue text-white' : 'text-gray-400 hover:text-white hover:bg-white/5' }}">{{ $l }}</a>
            @endforeach
            <form action="{{ route('logout') }}" method="POST">@csrf
                <button data-testid="logout-btn" class="w-full text-left flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10">Sair</button>
            </form>
        </aside>
        <div class="lg:col-span-3">@yield('account')</div>
    </div>
</div>
@endsection
