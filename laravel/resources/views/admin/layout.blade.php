<!doctype html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'Admin | Brasil Minis')</title>
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="min-h-screen bg-[#0d0d0d] flex">
    @php $nav = ['admin.dashboard'=>'Dashboard','admin.products.index'=>'Produtos','admin.categories.index'=>'Categorias','admin.brands.index'=>'Marcas','admin.orders.index'=>'Pedidos','admin.customers.index'=>'Clientes','admin.banners.index'=>'Banners']; @endphp
    <aside class="w-64 shrink-0 border-r border-bm-med bg-bm-black hidden lg:flex flex-col sticky top-0 h-screen">
        <div class="p-5 flex items-center gap-3 border-b border-bm-med">
            <img src="{{ config('brasilminis.logo_emblem') }}" class="h-10 w-10 rounded-lg object-cover">
            <div><p class="font-display font-black text-white uppercase text-sm leading-none">Brasil Minis</p><p class="text-xs text-bm-yellow">Admin</p></div>
        </div>
        <nav class="p-3 flex-1">
            @foreach($nav as $r => $l)
                <a href="{{ route($r) }}" data-testid="admin-nav-{{ \Illuminate\Support\Str::slug($l) }}"
                   class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium mb-1 transition-colors {{ request()->routeIs($r) || request()->routeIs(str_replace('.index','.*',$r)) ? 'bg-bm-blue text-white' : 'text-gray-400 hover:text-white hover:bg-white/5' }}">{{ $l }}</a>
            @endforeach
        </nav>
        <a href="{{ route('home') }}" class="m-3 px-4 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-white/5">← Voltar à loja</a>
    </aside>
    <div class="flex-1 min-w-0">
        <div class="lg:hidden bm-glass sticky top-0 z-40 px-4 py-3 flex gap-2 overflow-x-auto">
            @foreach($nav as $r => $l)<a href="{{ route($r) }}" class="whitespace-nowrap text-xs text-gray-300 px-3 py-1.5 rounded-full border border-bm-med">{{ $l }}</a>@endforeach
        </div>
        <div class="p-4 lg:p-8">
            @include('partials.flash')
            @yield('admin')
        </div>
    </div>
</body>
</html>
