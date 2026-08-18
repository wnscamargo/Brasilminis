@extends('admin.layout')
@section('title', 'Pedidos | Admin')
@section('admin')
<h1 class="text-3xl font-display font-black uppercase text-white mb-6">Pedidos</h1>
@if($orders->isEmpty())
    <div class="bm-card p-12 text-center text-gray-400">Nenhum pedido recebido ainda.</div>
@else
<div class="bm-card overflow-hidden overflow-x-auto">
    <table class="w-full text-sm">
        <thead class="bg-bm-black text-gray-500 uppercase text-xs"><tr>
            <th class="text-left p-4">Pedido</th><th class="text-left p-4">Cliente</th><th class="text-left p-4">Data</th><th class="text-left p-4">Total</th><th class="text-left p-4">Pagto</th><th class="text-left p-4">Status</th>
        </tr></thead>
        <tbody>
        @foreach($orders as $o)
        <tr class="border-t border-bm-med" data-testid="admin-order-{{ $o->order_number }}">
            <td class="p-4 text-white font-semibold">#{{ $o->order_number }}</td>
            <td class="p-4 text-gray-300">{{ $o->user->name ?? '—' }}<br><span class="text-gray-600 text-xs">{{ $o->user->email ?? '' }}</span></td>
            <td class="p-4 text-gray-400">{{ $o->created_at->format('d/m/Y') }}</td>
            <td class="p-4 text-white">{{ brl($o->total) }}</td>
            <td class="p-4 text-gray-400 uppercase text-xs">{{ $o->payment_method }}</td>
            <td class="p-4">
                <form action="{{ route('admin.orders.status', $o) }}" method="POST">@csrf @method('PUT')
                    <select name="status" onchange="this.form.submit()" data-testid="order-status-{{ $o->order_number }}" class="input-bm text-xs py-1.5">
                        @foreach(\App\Models\Order::STATUSES as $s)<option value="{{ $s }}" @selected($o->status===$s)>{{ \App\Models\Order::STATUS_LABELS[$s] }}</option>@endforeach
                    </select>
                </form>
            </td>
        </tr>
        @endforeach
        </tbody>
    </table>
</div>
<div class="mt-6">{{ $orders->links() }}</div>
@endif
@endsection
