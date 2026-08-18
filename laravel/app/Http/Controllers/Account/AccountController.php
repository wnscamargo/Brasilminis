<?php

namespace App\Http\Controllers\Account;

use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rule;

class AccountController extends Controller
{
    public function orders(Request $request)
    {
        $orders = $request->user()->orders()->with('items')->latest()->get();

        return view('account.orders', compact('orders'));
    }

    public function showOrder(Request $request, Order $order)
    {
        abort_unless($order->user_id === $request->user()->id, 403);

        return view('account.order', ['order' => $order->load('items', 'history')]);
    }

    public function profile(Request $request)
    {
        return view('account.profile');
    }

    public function updateProfile(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:255',
            'phone' => 'nullable|string|max:30',
            'newsletter' => 'boolean',
        ]);
        $request->user()->update($data + ['newsletter' => $request->boolean('newsletter')]);

        return back()->with('success', 'Dados atualizados.');
    }

    public function password(Request $request)
    {
        return view('account.password');
    }

    public function updatePassword(Request $request)
    {
        $data = $request->validate([
            'current_password' => 'required|current_password',
            'new_password' => 'required|min:6|confirmed',
        ]);
        $request->user()->update(['password' => Hash::make($data['new_password'])]);

        return back()->with('success', 'Senha atualizada.');
    }

    public function addresses(Request $request)
    {
        return view('account.addresses', ['addresses' => $request->user()->addresses]);
    }

    public function storeAddress(Request $request)
    {
        $data = $request->validate([
            'label' => 'nullable|string',
            'recipient' => 'required|string',
            'street' => 'required|string',
            'number' => 'required|string',
            'complement' => 'nullable|string',
            'district' => 'required|string',
            'city' => 'required|string',
            'state' => 'required|string|max:2',
            'zip' => 'required|string|max:12',
        ]);
        $data['label'] = $data['label'] ?? 'Casa';
        $data['is_default'] = $request->user()->addresses()->count() === 0;
        $request->user()->addresses()->create($data);

        return back()->with('success', 'Endereço salvo.');
    }

    public function deleteAddress(Request $request, int $address)
    {
        $request->user()->addresses()->where('id', $address)->delete();

        return back()->with('success', 'Endereço removido.');
    }
}
