@extends('admin.layout')
@section('title', 'Dashboard | Admin')
@section('admin')
<h1 class="text-3xl font-display font-black uppercase text-white mb-8">Dashboard</h1>
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    @foreach([['Faturamento', brl($revenue),'bm-green'],['Pedidos',$totalOrders,'bm-blue'],['Produtos',$totalProducts,'bm-yellow'],['Clientes',$totalCustomers,'bm-blue']] as $c)
    <div class="bm-card p-5" data-testid="stat-{{ \Illuminate\Support\Str::slug($c[0]) }}">
        <p class="text-2xl font-display font-black text-white">{{ $c[1] }}</p>
        <p class="text-xs text-gray-500 uppercase tracking-wide mt-1">{{ $c[0] }}</p>
    </div>
    @endforeach
</div>

@if($lowStock > 0)
<div class="bm-card p-4 mb-6 flex items-center gap-3 border-bm-yellow/40">
    <span class="text-bm-yellow">⚠</span><span class="text-sm text-gray-300">{{ $lowStock }} produto(s) com estoque baixo (≤ 5 unidades).</span>
</div>
@endif

<div class="grid lg:grid-cols-3 gap-6">
    <div class="bm-card p-6 lg:col-span-2">
        <h3 class="font-display font-bold text-white uppercase mb-4">Faturamento (últimos dias)</h3>
        @forelse($series as $s)
            <div class="flex items-center gap-3 mb-2">
                <span class="text-xs text-gray-500 w-20">{{ \Illuminate\Support\Str::of($s->date)->substr(5) }}</span>
                <div class="flex-1 bg-bm-black rounded-full h-3 overflow-hidden">
                    <div class="h-full bg-bm-yellow" style="width: {{ $revenue > 0 ? min(100, $s->revenue / max($revenue,1) * 100) : 0 }}%"></div>
                </div>
                <span class="text-xs text-white w-24 text-right">{{ brl($s->revenue) }}</span>
            </div>
        @empty
            <p class="text-gray-500 text-sm py-12 text-center">Sem vendas ainda.</p>
        @endforelse
    </div>
    <div class="bm-card p-6">
        <h3 class="font-display font-bold text-white uppercase mb-4">Pedidos recentes</h3>
        @forelse($recentOrders as $o)
            <div class="flex justify-between items-center text-sm mb-3"><div><p class="text-white">#{{ $o->order_number }}</p></div><span class="text-bm-yellow font-semibold">{{ brl($o->total) }}</span></div>
        @empty
            <p class="text-gray-500 text-sm">Nenhum pedido ainda.</p>
        @endforelse
    </div>
</div>
@endsection
