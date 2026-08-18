<header class="sticky top-0 z-50" x-data="{ open: false }">
    <div class="bm-stripe"></div>
    <div class="bm-glass">
        <div class="max-w-[1400px] mx-auto px-4 lg:px-8">
            <div class="flex items-center gap-4 h-20">
                <button class="lg:hidden text-white" @click="open = !open" data-testid="mobile-menu-toggle" aria-label="Menu">
                    <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h18M4 13h18M4 19h18"/></svg>
                </button>

                <a href="{{ route('home') }}" data-testid="logo-link" class="shrink-0">
                    <img src="{{ config('brasilminis.logo_header') }}" alt="Brasil Minis" class="h-11 w-auto object-contain">
                </a>

                <form action="{{ route('catalog') }}" method="GET" class="hidden md:flex flex-1 max-w-xl mx-4 relative">
                    <input name="search" value="{{ request('search') }}" placeholder="Buscar miniaturas, marcas, acessórios..."
                           data-testid="search-input"
                           class="w-full bg-bm-dark border border-bm-med rounded-full py-2.5 pl-5 pr-12 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-bm-blue">
                    <button type="submit" data-testid="search-submit" class="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-bm-blue text-white">
                        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7" cy="7" r="5"/><path d="M15 15l-4-4"/></svg>
                    </button>
                </form>

                <div class="flex items-center gap-1 md:gap-2 ml-auto">
                    <a href="{{ auth()->check() ? route('account.orders') : route('login') }}" data-testid="account-link" class="flex items-center gap-2 px-3 py-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                        <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="7" r="4"/><path d="M3 21a8 8 0 0116 0"/></svg>
                        <span class="hidden xl:inline text-sm">{{ auth()->check() ? \Illuminate\Support\Str::of(auth()->user()->name)->before(' ') : 'Entrar' }}</span>
                    </a>
                    <a href="{{ route('favorites') }}" data-testid="favorites-link" class="p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                        <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M11 19s-7-4.5-7-9a4 4 0 017-2.5A4 4 0 0118 10c0 4.5-7 9-7 9z"/></svg>
                    </a>
                    <a href="{{ route('cart') }}" data-testid="cart-link" class="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                        <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.5 13h11"/></svg>
                        @if(($globalCartCount ?? 0) > 0)
                            <span data-testid="cart-count" class="absolute -top-0.5 -right-0.5 bg-bm-yellow text-bm-black text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center">{{ $globalCartCount }}</span>
                        @endif
                    </a>
                </div>
            </div>

            <nav class="hidden lg:flex items-center gap-1 pb-3 -mt-1">
                @foreach(config('brasilminis.menu') as $m)
                    <a href="{{ isset($m['param']) ? route($m['route'], $m['param']) : route($m['route']) }}"
                       class="px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 hover:text-bm-yellow transition-colors">
                        {{ $m['label'] }}
                    </a>
                @endforeach
            </nav>
        </div>
    </div>

    <div x-show="open" x-cloak class="lg:hidden bg-bm-dark border-b border-bm-med px-4 py-4">
        <form action="{{ route('catalog') }}" method="GET" class="relative mb-3">
            <input name="search" placeholder="Buscar..." class="w-full bg-bm-black border border-bm-med rounded-full py-2.5 pl-4 pr-12 text-sm text-white">
        </form>
        <div class="grid grid-cols-2 gap-1">
            @foreach(config('brasilminis.menu') as $m)
                <a href="{{ isset($m['param']) ? route($m['route'], $m['param']) : route($m['route']) }}" class="px-3 py-2 text-sm uppercase tracking-wide text-gray-300 hover:text-bm-yellow">{{ $m['label'] }}</a>
            @endforeach
        </div>
    </div>
</header>
