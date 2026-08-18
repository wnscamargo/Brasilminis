<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\User;
use Illuminate\Support\Facades\DB;

class DashboardController extends Controller
{
    public function index()
    {
        $revenue = (float) Order::whereIn('status', ['PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED'])->sum('total');

        $series = Order::selectRaw('DATE(created_at) as date, SUM(total) as revenue')
            ->groupBy('date')->orderBy('date')->take(7)->get();

        return view('admin.dashboard', [
            'totalProducts' => Product::count(),
            'totalOrders' => Order::count(),
            'totalCustomers' => User::where('role', 'client')->count(),
            'revenue' => $revenue,
            'lowStock' => Product::where('stock', '<=', 5)->count(),
            'series' => $series,
            'recentOrders' => Order::latest()->take(5)->get(),
        ]);
    }
}
