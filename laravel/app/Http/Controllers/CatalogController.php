<?php

namespace App\Http\Controllers;

use App\Models\Brand;
use App\Models\Category;
use App\Models\Product;
use Illuminate\Http\Request;

class CatalogController extends Controller
{
    public function index(Request $request, ?string $group = null)
    {
        $query = Product::active()->with('images', 'brand');

        if ($group) {
            $query->where('group', $group);
        }
        if ($c = $request->query('category')) {
            $query->whereHas('category', fn ($q) => $q->where('slug', $c));
        }
        if ($b = $request->query('brand')) {
            $query->whereHas('brand', fn ($q) => $q->where('slug', $b));
        }
        if ($badge = $request->query('badge')) {
            $query->badge($badge);
        }
        if ($search = $request->query('search')) {
            $query->search($search);
        }
        if ($request->boolean('on_sale')) {
            $query->onSale();
        }

        $query = match ($request->query('sort', 'recent')) {
            'price_asc' => $query->orderBy('price'),
            'price_desc' => $query->orderByDesc('price'),
            'rating' => $query->orderByDesc('rating'),
            'name' => $query->orderBy('name'),
            default => $query->latest(),
        };

        $products = $query->paginate(24)->withQueryString();

        return view('shop.catalog', [
            'products' => $products,
            'categories' => Category::when($group, fn ($q) => $q->where('group', $group))->orderBy('name')->get(),
            'brands' => Brand::orderBy('name')->get(),
            'group' => $group,
        ]);
    }
}
