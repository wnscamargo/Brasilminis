<footer class="mt-24 border-t border-bm-med bg-[#0d0d0d]">
    <div class="bm-stripe"></div>
    <div class="max-w-[1400px] mx-auto px-4 lg:px-8 py-14">
        <div class="bm-card p-8 lg:p-12 flex flex-col lg:flex-row items-center justify-between gap-6">
            <div>
                <h3 class="text-2xl font-display font-bold text-white uppercase tracking-tight">Entre para o clube</h3>
                <p class="text-gray-400 mt-2">Receba lançamentos, Treasure Hunts e promoções exclusivas antes de todo mundo.</p>
            </div>
            <form action="{{ route('contact.send') }}" method="POST" class="flex w-full lg:w-auto gap-2">
                @csrf
                <input type="hidden" name="name" value="Newsletter">
                <input type="hidden" name="message" value="Inscrição newsletter">
                <input type="email" name="email" required placeholder="Seu melhor e-mail" data-testid="newsletter-input"
                       class="flex-1 lg:w-80 bg-bm-black border border-bm-med rounded-full px-5 py-3 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-bm-yellow">
                <button class="btn-buy" data-testid="newsletter-submit">Assinar</button>
            </form>
        </div>
    </div>

    <div class="max-w-[1400px] mx-auto px-4 lg:px-8 pb-12 grid grid-cols-2 md:grid-cols-4 gap-8">
        <div class="col-span-2 md:col-span-1">
            <img src="{{ config('brasilminis.logo_header') }}" alt="Brasil Minis" class="h-10 w-auto mb-4">
            <p class="text-sm text-gray-500 leading-relaxed">Sua paixão em miniatura. As melhores marcas e edições exclusivas do universo automotivo.</p>
        </div>
        <div>
            <h4 class="font-display font-semibold text-white uppercase text-sm tracking-wider mb-4">Institucional</h4>
            <ul class="space-y-2.5 text-sm">
                <li><a href="{{ route('contact') }}" class="text-gray-400 hover:text-bm-yellow">Sobre nós</a></li>
                <li><a href="{{ route('brands') }}" class="text-gray-400 hover:text-bm-yellow">Marcas</a></li>
                <li><a href="{{ route('catalog', ['badge' => 'LANÇAMENTO']) }}" class="text-gray-400 hover:text-bm-yellow">Lançamentos</a></li>
                <li><a href="{{ route('catalog', ['on_sale' => 1]) }}" class="text-gray-400 hover:text-bm-yellow">Promoções</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-display font-semibold text-white uppercase text-sm tracking-wider mb-4">Ajuda</h4>
            <ul class="space-y-2.5 text-sm">
                <li><a href="{{ route('contact') }}" class="text-gray-400 hover:text-bm-yellow">Contato</a></li>
                <li><a href="{{ route('contact') }}" class="text-gray-400 hover:text-bm-yellow">Trocas e devoluções</a></li>
                <li><a href="{{ route('account.orders') }}" class="text-gray-400 hover:text-bm-yellow">Minha conta</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-display font-semibold text-white uppercase text-sm tracking-wider mb-4">Redes Sociais</h4>
            <div class="flex gap-3">
                @foreach(['Instagram','Facebook','TikTok','YouTube'] as $s)
                    <a href="#" class="h-10 w-10 grid place-items-center rounded-full border border-bm-med text-gray-300 hover:border-bm-yellow hover:text-bm-yellow transition-colors text-xs">{{ substr($s,0,2) }}</a>
                @endforeach
            </div>
            <p class="text-xs text-gray-600 mt-6">Pagamento seguro • PIX • Cartão • Boleto</p>
        </div>
    </div>

    <div class="border-t border-bm-med py-5">
        <p class="text-center text-xs text-gray-600">© {{ date('Y') }} Brasil Minis. Todos os direitos reservados.</p>
    </div>
</footer>
