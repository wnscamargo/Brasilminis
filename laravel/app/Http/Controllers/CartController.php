<?php

namespace App\Http\Controllers;

use App\Services\CartService;
use Illuminate\Http\Request;

class CartController extends Controller
{
    public function __construct(protected CartService $cart) {}

    public function index()
    {
        return view('shop.cart', ['cart' => $this->cart->current()]);
    }

    public function add(Request $request)
    {
        $data = $request->validate([
            'product_id' => 'required|integer',
            'quantity' => 'nullable|integer|min:1',
        ]);
        $this->cart->add($data['product_id'], $data['quantity'] ?? 1);

        return back()->with('success', 'Produto adicionado ao carrinho.');
    }

    public function update(Request $request, int $item)
    {
        $this->cart->updateQty($item, (int) $request->input('quantity', 1));

        return back();
    }

    public function remove(int $item)
    {
        $this->cart->remove($item);

        return back()->with('success', 'Item removido.');
    }
}
