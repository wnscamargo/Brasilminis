<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Banner;
use Illuminate\Http\Request;

class BannerController extends Controller
{
    public function index()
    {
        return view('admin.banners', ['banners' => Banner::orderBy('position')->get()]);
    }

    public function store(Request $request)
    {
        Banner::create($this->validated($request));

        return back()->with('success', 'Banner criado.');
    }

    public function update(Request $request, Banner $banner)
    {
        $banner->update($this->validated($request));

        return back()->with('success', 'Banner atualizado.');
    }

    public function destroy(Banner $banner)
    {
        $banner->delete();

        return back()->with('success', 'Banner removido.');
    }

    protected function validated(Request $request): array
    {
        $data = $request->validate([
            'title' => 'required|string',
            'subtitle' => 'nullable|string',
            'image' => 'required|string',
            'cta_text' => 'nullable|string',
            'cta_link' => 'nullable|string',
            'position' => 'nullable|integer',
            'active' => 'boolean',
        ]);
        $data['active'] = $request->boolean('active');
        $data['position'] = (int) $request->input('position', 0);

        return $data;
    }
}
