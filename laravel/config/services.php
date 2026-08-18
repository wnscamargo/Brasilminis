<?php

return [
    'postmark' => [
        'token' => env('POSTMARK_TOKEN'),
    ],
    'resend' => [
        'key' => env('RESEND_KEY'),
    ],
    'mercadopago' => [
        'access_token' => env('MERCADOPAGO_ACCESS_TOKEN'),
        'public_key' => env('MERCADOPAGO_PUBLIC_KEY'),
        'webhook_secret' => env('MERCADOPAGO_WEBHOOK_SECRET'),
    ],
    'shop' => [
        'free_shipping_threshold' => (float) env('FREE_SHIPPING_THRESHOLD', 300),
        'standard_shipping' => (float) env('STANDARD_SHIPPING', 29.90),
        'payment_driver' => env('PAYMENT_DRIVER', 'mock'),
    ],
];
