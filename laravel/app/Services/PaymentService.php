<?php

namespace App\Services;

use App\Models\Order;

/**
 * Payment gateway abstraction.
 *
 * Currently uses a MOCK driver (simulated approval). The interface is ready for
 * Mercado Pago (PIX / cartão / boleto + webhooks). To go live, implement a
 * MercadoPagoPaymentService and switch config('services.shop.payment_driver').
 */
class PaymentService
{
    public function charge(Order $order): array
    {
        $driver = config('services.shop.payment_driver', 'mock');

        return match ($driver) {
            'mercadopago' => $this->mercadoPago($order),
            default => $this->mock($order),
        };
    }

    protected function mock(Order $order): array
    {
        $order->update(['payment_status' => 'paid_simulated', 'status' => 'PAID']);

        return [
            'provider' => 'mock',
            'method' => $order->payment_method,
            'status' => 'approved',
            'pix_qr' => $order->payment_method === 'pix'
                ? '00020126BR.GOV.BCB.PIX-SIMULATED-'.$order->order_number
                : null,
            'boleto_url' => $order->payment_method === 'boleto'
                ? '#boleto-simulado-'.$order->order_number
                : null,
        ];
    }

    /**
     * Placeholder for the real Mercado Pago integration.
     * Should create a preference / PIX charge and return the checkout data.
     */
    protected function mercadoPago(Order $order): array
    {
        // TODO: integrar SDK Mercado Pago usando config('services.mercadopago.access_token')
        // Criar preference/pagamento, retornar init_point / qr_code / ticket_url,
        // e definir payment_status='pending' até a confirmação via webhook.
        return $this->mock($order);
    }
}
