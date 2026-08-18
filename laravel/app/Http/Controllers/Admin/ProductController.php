<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Brand;
use App\Models\Category;
use App\Models\Product;
use App\Models\ProductImage;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class ProductController extends Controller
{
    public function index(Request $request)
    {
        $products = Product::with('category', 'brand', 'images')
            ->when($request->query('q'), fn ($q, $s) => $q->where('name', 'like', "%{$s}%"))
            ->latest()->paginate(20)->withQueryString();

        return view('admin.products.index', compact('products'));
    }

    public function create()
    {
        return view('admin.products.form', [
            'product' => new Product(['badges' => [], 'is_active' => true, 'group' => 'miniaturas']),
            'categories' => Category::orderBy('name')->get(),
            'brands' => Brand::orderBy('name')->get(),
        ]);
    }

    public function edit(Product $product)
    {
        return view('admin.products.form', [
            'product' => $product->load('images'),
            'categories' => Category::orderBy('name')->get(),
            'brands' => Brand::orderBy('name')->get(),
        ]);
    }

    public function store(Request $request)
    {
        $product = Product::create($this->validated($request));
        $this->syncImages($product, $request);

        return redirect()->route('admin.products.index')->with('success', 'Produto criado.');
    }

    public function update(Request $request, Product $product)
    {
        $product->update($this->validated($request, $product->id));
        $this->syncImages($product, $request);

        return redirect()->route('admin.products.index')->with('success', 'Produto atualizado.');
    }

    public function destroy(Product $product)
    {
        $product->delete();

        return back()->with('success', 'Produto removido.');
    }

    protected function validated(Request $request, ?int $id = null): array
    {
        $data = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'price' => 'required|numeric|min:0',
            'compare_at_price' => 'nullable|numeric|min:0',
            'category_id' => 'nullable|exists:categories,id',
            'brand_id' => 'nullable|exists:brands,id',
            'group' => 'required|in:miniaturas,colecionaveis,acessorios,vestuario,presentes',
            'stock' => 'required|integer|min:0',
            'badges' => 'nullable|array',
            'featured' => 'boolean',
            'is_active' => 'boolean',
            'sku' => 'nullable|string',
        ]);
        $data['slug'] = Str::slug($data['name']).($id ? '' : '-'.Str::random(4));
        $data['featured'] = $request->boolean('featured');
        $data['is_active'] = $request->boolean('is_active');
        $data['badges'] = $request->input('badges', []);

        return $data;
    }

    protected function syncImages(Product $product, Request $request): void
    {
        $urls = collect(preg_split('/[\n,]+/', (string) $request->input('images', '')))
            ->map(fn ($u) => trim($u))->filter()->values();

        if ($urls->isEmpty()) {
            return;
        }
        $product->images()->delete();
        foreach ($urls as $i => $url) {
            $product->images()->create(['path' => $url, 'position' => $i]);
        }
    }
}
