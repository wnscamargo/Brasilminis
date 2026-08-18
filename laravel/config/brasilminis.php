<?php

return [
    'logo_header' => env('BM_LOGO_HEADER', 'https://static.prod-images.emergentagent.com/jobs/2d012ce5-70bf-425e-88f8-05a40f9c01ee/images/8b98c77a1247ca88c24e650d4638147cdf835d95c6364f87e60335ef37a48264.jpeg'),
    'logo_emblem' => env('BM_LOGO_EMBLEM', 'https://static.prod-images.emergentagent.com/jobs/2d012ce5-70bf-425e-88f8-05a40f9c01ee/images/972271557c7ccee63b81cb7ef5bb0ef1cbdb9480f6647c66231007439f3b95bd.jpeg'),

    'menu' => [
        ['label' => 'Início', 'route' => 'home'],
        ['label' => 'Miniaturas', 'route' => 'catalog.group', 'param' => 'miniaturas'],
        ['label' => 'Colecionáveis', 'route' => 'catalog.group', 'param' => 'colecionaveis'],
        ['label' => 'Acessórios', 'route' => 'catalog.group', 'param' => 'acessorios'],
        ['label' => 'Vestuário', 'route' => 'catalog.group', 'param' => 'vestuario'],
        ['label' => 'Presentes', 'route' => 'catalog.group', 'param' => 'presentes'],
        ['label' => 'Marcas', 'route' => 'brands'],
        ['label' => 'Contato', 'route' => 'contact'],
    ],

    'group_labels' => [
        'miniaturas' => 'Miniaturas',
        'colecionaveis' => 'Colecionáveis',
        'acessorios' => 'Acessórios',
        'vestuario' => 'Vestuário',
        'presentes' => 'Presentes',
    ],

    'badges' => ['NOVO', 'LANÇAMENTO', 'PROMOÇÃO', 'TREASURE HUNT', 'SUPER TH', 'PREMIUM', 'EDIÇÃO LIMITADA', 'PRÉ-VENDA', 'FRETE GRÁTIS'],
];
