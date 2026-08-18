<?php

namespace App\Http\Controllers;

use App\Models\Brand;

class BrandController extends Controller
{
    public function index()
    {
        return view('shop.brands', ['brands' => Brand::orderBy('name')->get()]);
    }
}
