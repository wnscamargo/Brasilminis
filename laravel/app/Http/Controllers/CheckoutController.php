<?php

namespace App\Http\Controllers;

use App\Models\Coupon;
use App\Services\CartService;
use App\Services\OrderService;
use Illuminate\Http\Request;

class CheckoutController extends Controller
{
    public function __construct(protected CartService $cart, protected OrderService $orders) {}

    public function index(Request $request)
    {
        $cart = $this->cart->current();
        if ($cart->items->isEmpty()) {
            return redirect()->route('cart')->with('error', 'Seu carrinho está vazio.');
        }

        $subtotal = $cart->subtotal();
        $discount = 0;
        $couponCode = session('coupon');
        if ($couponCode) {
            try {
                [$discount] = $this->orders->resolveCoupon($couponCode, $subtotal);
            } catch (\Throwable $e) {
                session()->forget('coupon');
                $couponCode = null;
            }
        }
        $shipping = $this->orders->shippingFor($subtotal, $discount);

        return view('shop.checkout', [
            'cart' => $cart,
            'subtotal' => $subtotal,
            'discount' => $discount,
            'shipping' => $shipping,
            'total' => $subtotal - $discount + $shipping,
            'coupon' => $couponCode,
            'addresses' => $request->user()->addresses,
        ]);
    }

    public function applyCoupon(Request $request)
    {
        $request->validate(['code' => 'required|string']);
        $subtotal = $this->cart->current()->subtotal();
        try {
            $this->orders->resolveCoupon($request->code, $subtotal);
            session(['coupon' => strtoupper($request->code)]);
            return back()->with('success', 'Cupom aplicado!');
        } catch (\Illuminate\Validation\ValidationException $e) {
            return back()->with('error', $e->validator->errors()->first());
        }
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'payment_method' => 'required|in:pix,card,boleto',
            'recipient' => 'required|string',
            'zip' => 'required|string',
            'street' => 'required|string',
            'number' => 'required|string',
            'district' => 'required|string',
            'city' => 'required|string',
            'state' => 'required|string|max:2',
            'complement' => 'nullable|string',
        ]);

        $cart = $this->cart->current();
        $lines = $cart->items->mapWithKeys(fn ($i) => [$i->product_id => $i->quantity])->all();

        $address = [
            'label' => 'Entrega',
            'recipient' => $data['recipient'],
            'zip' => $data['zip'],
            'street' => $data['street'],
            'number' => $data['number'],
            'complement' => $data['complement'] ?? '',
            'district' => $data['district'],
            'city' => $data['city'],
            'state' => strtoupper($data['state']),
        ];

        try {
            [$order, $payment] = $this->orders->place(
                $request->user()->id,
                $lines,
                $data['payment_method'],
                session('coupon'),
                $address,
            );
        } catch (\Illuminate\Validation\ValidationException $e) {
            return back()->with('error', $e->validator->errors()->first());
        }

        $this->cart->clear();
        session()->forget('coupon');

        return redirect()->route('checkout.success', $order)->with('payment', $payment);
    }

    public function success(\App\Models\Order $order, Request $request)
    {
        abort_unless($order->user_id === $request->user()->id, 403);

        return view('shop.checkout-success', [
            'order' => $order->load('items'),
            'payment' => session('payment'),
        ]);
    }
}
