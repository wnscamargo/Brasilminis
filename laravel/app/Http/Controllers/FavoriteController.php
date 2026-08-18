<?php

namespace App\Http\Controllers;

use App\Models\Favorite;
use App\Models\Product;
use Illuminate\Http\Request;

class FavoriteController extends Controller
{
    public function index(Request $request)
    {
        $products = $request->user()->favoriteProducts()->with('images', 'brand')->get();

        return view('shop.favorites', compact('products'));
    }

    public function toggle(Request $request, Product $product)
    {
        $fav = Favorite::where('user_id', $request->user()->id)->where('product_id', $product->id)->first();
        if ($fav) {
            $fav->delete();
            $msg = 'Removido dos favoritos.';
        } else {
            Favorite::create(['user_id' => $request->user()->id, 'product_id' => $product->id]);
            $msg = 'Adicionado aos favoritos.';
        }

        return back()->with('success', $msg);
    }
}
