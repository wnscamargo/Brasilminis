<?php

if (! function_exists('brl')) {
    function brl($value): string
    {
        return 'R$ '.number_format((float) $value, 2, ',', '.');
    }
}

if (! function_exists('badge_class')) {
    function badge_class(string $badge): string
    {
        return [
            'NOVO' => 'bg-bm-blue text-white',
            'LANÇAMENTO' => 'bg-bm-green text-white',
            'PROMOÇÃO' => 'bg-bm-yellow text-bm-black',
            'TREASURE HUNT' => 'bg-gradient-to-r from-green-400 to-emerald-600 text-white',
            'SUPER TH' => 'bg-gradient-to-r from-purple-500 to-pink-500 text-white',
            'PREMIUM' => 'bg-bm-yellow/15 text-bm-yellow border border-bm-yellow/30',
            'EDIÇÃO LIMITADA' => 'bg-bm-med text-white border border-white/20',
            'PRÉ-VENDA' => 'bg-bm-med text-white border border-white/20',
            'FRETE GRÁTIS' => 'bg-bm-green/20 text-bm-green border border-bm-green/30',
        ][$badge] ?? 'bg-bm-med text-white';
    }
}
