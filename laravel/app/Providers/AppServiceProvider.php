<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use Illuminate\Support\Facades\View;
use Illuminate\Pagination\Paginator;
use App\Models\Banner;
use App\Models\Category;
use App\Services\CartService;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(CartService::class, fn () => new CartService());
    }

    public function boot(): void
    {
        Paginator::useTailwind();

        // Shared data for header/footer (menu, cart count)
        View::composer('*', function ($view) {
            $cart = app(CartService::class);
            $view->with('globalCartCount', $cart->current()->count());
        });
    }
}
