<?php

namespace App\Services;

use App\Models\Cart;
use App\Models\CartItem;
use App\Models\Product;
use Illuminate\Support\Facades\Auth;

class CartService
{
    protected ?Cart $cart = null;

    public function current(): Cart
    {
        if ($this->cart) {
            return $this->cart;
        }

        if (Auth::check()) {
            $cart = Cart::firstOrCreate(['user_id' => Auth::id()]);
            $this->mergeGuestCart($cart);
        } else {
            $cart = Cart::firstOrCreate(['session_id' => session()->getId()]);
        }

        return $this->cart = $cart->load('items.product.images');
    }

    protected function mergeGuestCart(Cart $userCart): void
    {
        $guest = Cart::where('session_id', session()->getId())->whereNull('user_id')->first();
        if (! $guest || $guest->id === $userCart->id) {
            return;
        }
        foreach ($guest->items as $item) {
            $this->addToCart($userCart, $item->product_id, $item->quantity, $item->price);
        }
        $guest->delete();
    }

    public function add(int $productId, int $qty = 1): void
    {
        $product = Product::active()->findOrFail($productId);
        $this->addToCart($this->current(), $product->id, $qty, (float) $product->price);
        $this->cart = null;
    }

    protected function addToCart(Cart $cart, int $productId, int $qty, float $price): void
    {
        $item = $cart->items()->where('product_id', $productId)->first();
        if ($item) {
            $item->increment('quantity', $qty);
        } else {
            $cart->items()->create([
                'product_id' => $productId,
                'quantity' => $qty,
                'price' => $price,
            ]);
        }
    }

    public function updateQty(int $itemId, int $qty): void
    {
        $qty = max(1, $qty);
        CartItem::where('cart_id', $this->current()->id)->where('id', $itemId)->update(['quantity' => $qty]);
        $this->cart = null;
    }

    public function remove(int $itemId): void
    {
        CartItem::where('cart_id', $this->current()->id)->where('id', $itemId)->delete();
        $this->cart = null;
    }

    public function clear(): void
    {
        $this->current()->items()->delete();
        $this->cart = null;
    }
}
