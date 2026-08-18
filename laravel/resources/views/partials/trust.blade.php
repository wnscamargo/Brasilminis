<section class="border-y border-bm-med bm-honeycomb">
    <div class="max-w-[1400px] mx-auto px-4 lg:px-8 py-8 grid grid-cols-2 md:grid-cols-5 gap-6">
        @foreach([
            ['Compra Segura'],['Entrega Nacional'],['Produtos Originais'],['Colecionadores'],['Atendimento Especializado']
        ] as $item)
        <div class="flex flex-col md:flex-row items-center gap-3 text-center md:text-left">
            <div class="h-11 w-11 shrink-0 grid place-items-center rounded-full border border-bm-med text-bm-yellow">
                <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M11 2l7 3v5c0 5-3.5 8-7 9-3.5-1-7-4-7-9V5l7-3z"/></svg>
            </div>
            <span class="text-xs md:text-sm text-gray-300 font-medium">{{ $item[0] }}</span>
        </div>
        @endforeach
    </div>
</section>
