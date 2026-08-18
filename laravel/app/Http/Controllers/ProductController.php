<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Models\Review;
use Illuminate\Http\Request;

class ProductController extends Controller
{
    public function show(Product $product)
    {
        $product->load('images', 'brand', 'category', 'attributes', 'variants', 'reviews.user');

        $related = Product::active()
            ->where('id', '!=', $product->id)
            ->where(function ($q) use ($product) {
                $q->where('category_id', $product->category_id)
                  ->orWhere('brand_id', $product->brand_id);
            })
            ->with('images', 'brand')
            ->take(4)->get();

        return view('shop.product', compact('product', 'related'));
    }

    public function storeReview(Request $request, Product $product)
    {
        $data = $request->validate([
            'rating' => 'required|integer|min:1|max:5',
            'comment' => 'nullable|string|max:2000',
        ]);

        Review::updateOrCreate(
            ['product_id' => $product->id, 'user_id' => $request->user()->id],
            ['rating' => $data['rating'], 'comment' => $data['comment'] ?? '', 'approved' => true],
        );

        $product->recomputeRating();

        return back()->with('success', 'Avaliação enviada com sucesso!');
    }
}
