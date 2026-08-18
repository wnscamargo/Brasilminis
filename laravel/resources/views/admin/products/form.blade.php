@extends('admin.layout')
@section('title', ($product->exists ? 'Editar' : 'Novo').' produto | Admin')
@section('admin')
@php $editing = $product->exists; @endphp
<h1 class="text-3xl font-display font-black uppercase text-white mb-6">{{ $editing ? 'Editar' : 'Novo' }} produto</h1>
<form action="{{ $editing ? route('admin.products.update', $product) : route('admin.products.store') }}" method="POST" class="bm-card p-6 max-w-3xl">
    @csrf
    @if($editing) @method('PUT') @endif
    <div class="grid grid-cols-2 gap-3">
        <div class="col-span-2"><label class="text-xs text-gray-500 block mb-1">Nome</label><input name="name" value="{{ old('name', $product->name) }}" required class="input-bm" data-testid="pf-name"></div>
        <div class="col-span-2"><label class="text-xs text-gray-500 block mb-1">Descrição</label><textarea name="description" rows="3" class="input-bm" data-testid="pf-desc">{{ old('description', $product->description) }}</textarea></div>
        <div><label class="text-xs text-gray-500 block mb-1">Preço</label><input name="price" type="number" step="0.01" value="{{ old('price', $product->price) }}" required class="input-bm" data-testid="pf-price"></div>
        <div><label class="text-xs text-gray-500 block mb-1">Preço comparativo</label><input name="compare_at_price" type="number" step="0.01" value="{{ old('compare_at_price', $product->compare_at_price) }}" class="input-bm" data-testid="pf-compare"></div>
        <div><label class="text-xs text-gray-500 block mb-1">Grupo</label>
            <select name="group" class="input-bm" data-testid="pf-group">
                @foreach(config('brasilminis.group_labels') as $g=>$l)<option value="{{ $g }}" @selected(old('group',$product->group)===$g)>{{ $l }}</option>@endforeach
            </select>
        </div>
        <div><label class="text-xs text-gray-500 block mb-1">Categoria</label>
            <select name="category_id" class="input-bm" data-testid="pf-category">
                <option value="">—</option>
                @foreach($categories as $c)<option value="{{ $c->id }}" @selected(old('category_id',$product->category_id)==$c->id)>{{ $c->name }}</option>@endforeach
            </select>
        </div>
        <div><label class="text-xs text-gray-500 block mb-1">Marca</label>
            <select name="brand_id" class="input-bm" data-testid="pf-brand">
                <option value="">Sem marca</option>
                @foreach($brands as $b)<option value="{{ $b->id }}" @selected(old('brand_id',$product->brand_id)==$b->id)>{{ $b->name }}</option>@endforeach
            </select>
        </div>
        <div><label class="text-xs text-gray-500 block mb-1">Estoque</label><input name="stock" type="number" value="{{ old('stock', $product->stock ?? 0) }}" required class="input-bm" data-testid="pf-stock"></div>
        <div class="col-span-2"><label class="text-xs text-gray-500 block mb-1">SKU</label><input name="sku" value="{{ old('sku', $product->sku) }}" class="input-bm"></div>
        <div class="col-span-2"><label class="text-xs text-gray-500 block mb-1">Imagens (URLs separadas por vírgula ou linha)</label>
            <textarea name="images" rows="2" class="input-bm" data-testid="pf-images">{{ $product->images->pluck('path')->implode(', ') }}</textarea></div>
    </div>

    <div class="mt-4"><label class="text-xs text-gray-500 block mb-2">Badges</label>
        <div class="flex flex-wrap gap-2">
            @foreach(config('brasilminis.badges') as $b)
                <label class="px-3 py-1 rounded-full text-xs font-semibold border cursor-pointer {{ in_array($b, old('badges', $product->badges ?? [])) ? 'bg-bm-blue border-bm-blue text-white' : 'border-bm-med text-gray-400' }}">
                    <input type="checkbox" name="badges[]" value="{{ $b }}" class="hidden" @checked(in_array($b, old('badges', $product->badges ?? []))) onchange="this.closest('label').classList.toggle('bg-bm-blue');this.closest('label').classList.toggle('text-white')"> {{ $b }}
                </label>
            @endforeach
        </div>
    </div>

    <div class="flex gap-4 mt-4">
        <label class="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" name="featured" value="1" @checked(old('featured',$product->featured)) class="accent-bm-yellow"> Destaque</label>
        <label class="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" name="is_active" value="1" @checked(old('is_active',$product->is_active ?? true)) class="accent-bm-yellow"> Ativo</label>
    </div>

    <div class="flex gap-3 mt-6">
        <a href="{{ route('admin.products.index') }}" class="flex-1 text-center border border-bm-med text-white rounded-full py-3">Cancelar</a>
        <button data-testid="save-product-btn" class="flex-1 btn-buy">Salvar</button>
    </div>
</form>
@endsection
