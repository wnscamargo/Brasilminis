<?php

namespace App\Services;

use App\Models\Coupon;
use App\Models\Order;
use App\Models\OrderStatusHistory;
use App\Models\Product;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class OrderService
{
    public function __construct(protected PaymentService $payments) {}

    public function freeShippingThreshold(): float
    {
        return (float) config('services.shop.free_shipping_threshold', 300);
    }

    public function standardShipping(): float
    {
        return (float) config('services.shop.standard_shipping', 29.90);
    }

    public function resolveCoupon(?string $code, float $subtotal): array
    {
        if (! $code) {
            return [0.0, null];
        }
        $coupon = Coupon::where('code', strtoupper($code))->first();
        if (! $coupon || ! $coupon->isValid()) {
            throw ValidationException::withMessages(['coupon' => 'Cupom inválido ou expirado.']);
        }
        if ($subtotal < (float) $coupon->min_order) {
            throw ValidationException::withMessages([
                'coupon' => 'Pedido mínimo de R$ '.number_format($coupon->min_order, 2, ',', '.').' para este cupom.',
            ]);
        }
        return [$coupon->discountFor($subtotal), $coupon->code];
    }

    public function shippingFor(float $subtotal, float $discount): float
    {
        return ($subtotal - $discount) >= $this->freeShippingThreshold() ? 0.0 : $this->standardShipping();
    }

    /**
     * Create an order from a list of [product_id => quantity], inside a DB
     * transaction with row locking to prevent overselling.
     */
    public function place(int $userId, array $lines, string $paymentMethod, ?string $coupon, ?array $address, string $shippingMethod = 'standard'): array
    {
        return DB::transaction(function () use ($userId, $lines, $paymentMethod, $coupon, $address, $shippingMethod) {
            $items = [];
            $subtotal = 0.0;

            foreach ($lines as $productId => $qty) {
                $qty = (int) $qty;
                if ($qty < 1) {
                    continue;
                }
                /** @var Product $product */
                $product = Product::where('id', $productId)->lockForUpdate()->first();
                if (! $product || ! $product->is_active) {
                    throw ValidationException::withMessages(['cart' => 'Produto indisponível no carrinho.']);
                }
                if ($product->stock < $qty) {
                    throw ValidationException::withMessages(['cart' => "Estoque insuficiente para {$product->name}."]);
                }
                $lineTotal = round($product->price * $qty, 2);
                $subtotal += $lineTotal;
                $items[] = [
                    'product' => $product,
                    'name' => $product->name,
                    'slug' => $product->slug,
                    'image' => $product->main_image,
                    'price' => $product->price,
                    'quantity' => $qty,
                    'line_total' => $lineTotal,
                ];
            }

            if (empty($items)) {
                throw ValidationException::withMessages(['cart' => 'Carrinho vazio.']);
            }

            $subtotal = round($subtotal, 2);
            [$discount, $couponCode] = $this->resolveCoupon($coupon, $subtotal);
            $shipping = $this->shippingFor($subtotal, $discount);
            $total = round($subtotal - $discount + $shipping, 2);

            $order = Order::create([
                'order_number' => 'BM'.random_int(100000, 999999),
                'user_id' => $userId,
                'status' => 'PENDING',
                'payment_method' => $paymentMethod,
                'payment_status' => 'pending',
                'subtotal' => $subtotal,
                'discount' => $discount,
                'shipping' => $shipping,
                'total' => $total,
                'coupon_code' => $couponCode,
                'shipping_method' => $shippingMethod,
                'address' => $address,
            ]);

            foreach ($items as $it) {
                $order->items()->create([
                    'product_id' => $it['product']->id,
                    'name' => $it['name'],
                    'slug' => $it['slug'],
                    'image' => $it['image'],
                    'price' => $it['price'],
                    'quantity' => $it['quantity'],
                    'line_total' => $it['line_total'],
                ]);
                $it['product']->decrement('stock', $it['quantity']);
            }

            OrderStatusHistory::create([
                'order_id' => $order->id,
                'from_status' => null,
                'to_status' => 'PENDING',
                'note' => 'Pedido criado',
            ]);

            $payment = $this->payments->charge($order);

            OrderStatusHistory::create([
                'order_id' => $order->id,
                'from_status' => 'PENDING',
                'to_status' => $order->fresh()->status,
                'note' => 'Pagamento '.($payment['status'] ?? 'processado'),
            ]);

            return [$order->fresh('items'), $payment];
        });
    }

    public function changeStatus(Order $order, string $status, ?int $adminId = null): void
    {
        $from = $order->status;
        $order->update(['status' => $status]);
        OrderStatusHistory::create([
            'order_id' => $order->id,
            'from_status' => $from,
            'to_status' => $status,
            'changed_by' => $adminId,
        ]);
    }
}
