<?php

namespace App\Http\Controllers;

use App\Models\Banner;
use App\Models\Brand;
use App\Models\Product;

class HomeController extends Controller
{
    public function index()
    {
        return view('shop.home', [
            'banner' => Banner::where('active', true)->orderBy('position')->first(),
            'featured' => Product::active()->featured()->with('images', 'brand')->take(8)->get(),
            'launches' => Product::active()->badge('LANÇAMENTO')->with('images', 'brand')->take(4)->get(),
            'sale' => Product::active()->onSale()->with('images', 'brand')->take(4)->get(),
            'brands' => Brand::orderBy('name')->get(),
        ]);
    }
}
