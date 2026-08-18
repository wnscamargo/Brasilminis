<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Category;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class CategoryController extends Controller
{
    public function index()
    {
        return view('admin.categories', ['categories' => Category::orderBy('group')->orderBy('name')->get()]);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string',
            'group' => 'required|in:miniaturas,colecionaveis,acessorios,vestuario,presentes',
            'description' => 'nullable|string',
        ]);
        $data['slug'] = Str::slug($data['name']);
        Category::create($data);

        return back()->with('success', 'Categoria criada.');
    }

    public function destroy(Category $category)
    {
        $category->delete();

        return back()->with('success', 'Categoria removida.');
    }
}
