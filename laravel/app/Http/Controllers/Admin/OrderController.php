<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\User;
use App\Services\OrderService;
use Illuminate\Http\Request;

class OrderController extends Controller
{
    public function index()
    {
        return view('admin.orders', ['orders' => Order::with('user')->latest()->paginate(30)]);
    }

    public function updateStatus(Request $request, Order $order, OrderService $service)
    {
        $data = $request->validate(['status' => 'required|in:'.implode(',', Order::STATUSES)]);
        $service->changeStatus($order, $data['status'], $request->user()->id);

        return back()->with('success', 'Status atualizado.');
    }

    public function customers()
    {
        $customers = User::where('role', 'client')->withCount('orders')->latest()->paginate(30);

        return view('admin.customers', compact('customers'));
    }
}
