@php
    $discount = ($product->compare_at_price && $product->compare_at_price > $product->price)
        ? (int) round((1 - $product->price / $product->compare_at_price) * 100) : 0;
    $img = optional($product->images->first())->path;
    $isFav = auth()->check() && auth()->user()->favorites->contains('product_id', $product->id);
@endphp
<div class="group bm-card overflow-hidden flex flex-col hover:border-bm-blue transition-colors duration-300" data-testid="product-card-{{ $product->id }}">
    <div class="relative aspect-square overflow-hidden bg-[#171717]">
        <a href="{{ route('product', $product) }}">
            <img src="{{ $img }}" alt="{{ $product->name }}" loading="lazy" class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105">
        </a>
        <div class="absolute top-3 left-3 flex flex-col gap-1.5 max-w-[70%]">
            @foreach(array_slice($product->badges ?? [], 0, 2) as $b)
                <span class="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full {{ badge_class($b) }}">{{ $b }}</span>
            @endforeach
            @if($discount > 0)
                <span class="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full bg-bm-yellow text-bm-black">-{{ $discount }}%</span>
            @endif
        </div>
        @auth
        <form action="{{ route('favorites.toggle', $product) }}" method="POST" class="absolute top-3 right-3">
            @csrf
            <button data-testid="fav-toggle-{{ $product->id }}" class="h-9 w-9 grid place-items-center rounded-full border transition-colors {{ $isFav ? 'bg-bm-green border-bm-green text-white' : 'bg-black/50 border-white/20 text-white hover:bg-black/70' }}">
                <svg width="16" height="16" fill="{{ $isFav ? 'currentColor' : 'none' }}" stroke="currentColor" stroke-width="2"><path d="M8 14s-5-3.2-5-6.5A2.8 2.8 0 018 5a2.8 2.8 0 015 2.5C13 10.8 8 14 8 14z"/></svg>
            </button>
        </form>
        @endauth
    </div>
    <div class="p-4 flex flex-col flex-1">
        <span class="text-[11px] uppercase tracking-widest {{ $product->brand ? 'text-bm-blue' : 'text-gray-500' }} font-semibold mb-1">
            {{ $product->brand->name ?? ucfirst($product->group) }}
        </span>
        <a href="{{ route('product', $product) }}" class="flex-1">
            <h3 class="text-sm font-medium text-white leading-snug line-clamp-2 hover:text-bm-yellow transition-colors">{{ $product->name }}</h3>
        </a>
        @if($product->reviews_count > 0)
            <div class="flex items-center gap-1 mt-2 text-bm-yellow text-xs">★ <span class="text-gray-400">{{ $product->rating }} ({{ $product->reviews_count }})</span></div>
        @endif
        <div class="mt-3 flex items-end justify-between gap-2">
            <div>
                @if($discount > 0)
                    <span class="block text-xs text-gray-500 line-through">{{ brl($product->compare_at_price) }}</span>
                @endif
                <span class="text-lg font-display font-bold text-white">{{ brl($product->price) }}</span>
            </div>
            <form action="{{ route('cart.add') }}" method="POST">
                @csrf
                <input type="hidden" name="product_id" value="{{ $product->id }}">
                <button data-testid="add-cart-{{ $product->id }}" @disabled($product->stock <= 0)
                    class="bg-bm-blue text-white text-xs font-semibold rounded-full px-4 py-2 hover:bg-blue-900 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                    {{ $product->stock <= 0 ? 'Esgotado' : 'Comprar' }}
                </button>
            </form>
        </div>
    </div>
</div>
