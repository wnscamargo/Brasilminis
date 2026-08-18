@extends('admin.layout')
@section('title', 'Produtos | Admin')
@section('admin')
<div class="flex flex-wrap items-center justify-between gap-4 mb-6">
    <h1 class="text-3xl font-display font-black uppercase text-white">Produtos</h1>
    <div class="flex gap-3">
        <form method="GET"><input name="q" value="{{ request('q') }}" placeholder="Buscar..." class="input-bm rounded-full bg-bm-dark"></form>
        <a href="{{ route('admin.products.create') }}" data-testid="new-product-btn" class="btn-buy px-5 py-2.5">+ Novo</a>
    </div>
</div>
<div class="bm-card overflow-hidden overflow-x-auto">
    <table class="w-full text-sm">
        <thead class="bg-bm-black text-gray-500 uppercase text-xs"><tr>
            <th class="text-left p-4">Produto</th><th class="text-left p-4">Categoria</th><th class="text-left p-4">Preço</th><th class="text-left p-4">Estoque</th><th class="text-right p-4">Ações</th>
        </tr></thead>
        <tbody>
        @foreach($products as $p)
        <tr class="border-t border-bm-med" data-testid="admin-product-{{ $p->id }}">
            <td class="p-4"><div class="flex items-center gap-3"><img src="{{ optional($p->images->first())->path }}" class="h-10 w-10 rounded-lg object-cover"><span class="text-white line-clamp-1 max-w-[220px]">{{ $p->name }}</span></div></td>
            <td class="p-4 text-gray-400">{{ $p->category->name ?? '—' }}</td>
            <td class="p-4 text-white">{{ brl($p->price) }}</td>
            <td class="p-4"><span class="{{ $p->stock <= 5 ? 'text-bm-yellow' : 'text-gray-300' }}">{{ $p->stock }}</span></td>
            <td class="p-4"><div class="flex justify-end gap-2">
                <a href="{{ route('admin.products.edit', $p) }}" data-testid="edit-product-{{ $p->id }}" class="px-3 py-1.5 rounded-lg text-gray-400 hover:text-bm-yellow hover:bg-white/5">Editar</a>
                <form action="{{ route('admin.products.destroy', $p) }}" method="POST" onsubmit="return confirm('Remover?')">@csrf @method('DELETE')<button data-testid="delete-product-{{ $p->id }}" class="px-3 py-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-white/5">Excluir</button></form>
            </div></td>
        </tr>
        @endforeach
        </tbody>
    </table>
</div>
<div class="mt-6">{{ $products->links() }}</div>
@endsection
