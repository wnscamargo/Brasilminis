<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\HomeController;
use App\Http\Controllers\CatalogController;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\CartController;
use App\Http\Controllers\CheckoutController;
use App\Http\Controllers\FavoriteController;
use App\Http\Controllers\BrandController;
use App\Http\Controllers\ContactController;
use App\Http\Controllers\Account\AccountController;
use App\Http\Controllers\Auth\RegisteredUserController;
use App\Http\Controllers\Auth\AuthenticatedSessionController;
use App\Http\Controllers\Auth\PasswordResetLinkController;
use App\Http\Controllers\Auth\NewPasswordController;
use App\Http\Controllers\Admin;

// ---------- Storefront ----------
Route::get('/', [HomeController::class, 'index'])->name('home');
Route::get('/produtos', [CatalogController::class, 'index'])->name('catalog');
Route::get('/grupo/{group}', [CatalogController::class, 'index'])->name('catalog.group');
Route::get('/marcas', [BrandController::class, 'index'])->name('brands');
Route::get('/contato', [ContactController::class, 'index'])->name('contact');
Route::post('/contato', [ContactController::class, 'send'])->name('contact.send');
Route::get('/produto/{product}', [ProductController::class, 'show'])->name('product');

// Cart
Route::get('/carrinho', [CartController::class, 'index'])->name('cart');
Route::post('/carrinho', [CartController::class, 'add'])->name('cart.add');
Route::patch('/carrinho/{item}', [CartController::class, 'update'])->name('cart.update');
Route::delete('/carrinho/{item}', [CartController::class, 'remove'])->name('cart.remove');

// ---------- Auth (guest) ----------
Route::middleware('guest')->group(function () {
    Route::get('/cadastro', [RegisteredUserController::class, 'create'])->name('register');
    Route::post('/cadastro', [RegisteredUserController::class, 'store']);
    Route::get('/login', [AuthenticatedSessionController::class, 'create'])->name('login');
    Route::post('/login', [AuthenticatedSessionController::class, 'store']);
    Route::get('/recuperar-senha', [PasswordResetLinkController::class, 'create'])->name('password.request');
    Route::post('/recuperar-senha', [PasswordResetLinkController::class, 'store'])->name('password.email');
    Route::get('/reset-password/{token}', [NewPasswordController::class, 'create'])->name('password.reset');
    Route::post('/reset-password', [NewPasswordController::class, 'store'])->name('password.store');
});

Route::post('/logout', [AuthenticatedSessionController::class, 'destroy'])
    ->middleware('auth')->name('logout');

// ---------- Authenticated customer ----------
Route::middleware('auth')->group(function () {
    // Product reviews
    Route::post('/produto/{product}/avaliar', [ProductController::class, 'storeReview'])->name('product.review');

    // Favorites
    Route::get('/favoritos', [FavoriteController::class, 'index'])->name('favorites');
    Route::post('/favoritos/{product}', [FavoriteController::class, 'toggle'])->name('favorites.toggle');

    // Checkout
    Route::get('/checkout', [CheckoutController::class, 'index'])->name('checkout');
    Route::post('/checkout/cupom', [CheckoutController::class, 'applyCoupon'])->name('checkout.coupon');
    Route::post('/checkout', [CheckoutController::class, 'store'])->name('checkout.store');
    Route::get('/pedido/{order}/sucesso', [CheckoutController::class, 'success'])->name('checkout.success');

    // Account
    Route::prefix('conta')->name('account.')->group(function () {
        Route::get('/', [AccountController::class, 'orders'])->name('orders');
        Route::get('/pedido/{order}', [AccountController::class, 'showOrder'])->name('order');
        Route::get('/dados', [AccountController::class, 'profile'])->name('profile');
        Route::put('/dados', [AccountController::class, 'updateProfile'])->name('profile.update');
        Route::get('/senha', [AccountController::class, 'password'])->name('password');
        Route::put('/senha', [AccountController::class, 'updatePassword'])->name('password.update');
        Route::get('/enderecos', [AccountController::class, 'addresses'])->name('addresses');
        Route::post('/enderecos', [AccountController::class, 'storeAddress'])->name('addresses.store');
        Route::delete('/enderecos/{address}', [AccountController::class, 'deleteAddress'])->name('addresses.delete');
    });
});

// ---------- Admin ----------
Route::middleware(['auth', 'admin'])->prefix('admin')->name('admin.')->group(function () {
    Route::get('/', [Admin\DashboardController::class, 'index'])->name('dashboard');

    Route::get('/produtos', [Admin\ProductController::class, 'index'])->name('products.index');
    Route::get('/produtos/novo', [Admin\ProductController::class, 'create'])->name('products.create');
    Route::post('/produtos', [Admin\ProductController::class, 'store'])->name('products.store');
    Route::get('/produtos/{product}/editar', [Admin\ProductController::class, 'edit'])->name('products.edit');
    Route::put('/produtos/{product}', [Admin\ProductController::class, 'update'])->name('products.update');
    Route::delete('/produtos/{product}', [Admin\ProductController::class, 'destroy'])->name('products.destroy');

    Route::get('/categorias', [Admin\CategoryController::class, 'index'])->name('categories.index');
    Route::post('/categorias', [Admin\CategoryController::class, 'store'])->name('categories.store');
    Route::delete('/categorias/{category}', [Admin\CategoryController::class, 'destroy'])->name('categories.destroy');

    Route::get('/marcas', [Admin\BrandController::class, 'index'])->name('brands.index');
    Route::post('/marcas', [Admin\BrandController::class, 'store'])->name('brands.store');
    Route::delete('/marcas/{brand}', [Admin\BrandController::class, 'destroy'])->name('brands.destroy');

    Route::get('/pedidos', [Admin\OrderController::class, 'index'])->name('orders.index');
    Route::put('/pedidos/{order}/status', [Admin\OrderController::class, 'updateStatus'])->name('orders.status');
    Route::get('/clientes', [Admin\OrderController::class, 'customers'])->name('customers.index');

    Route::get('/banners', [Admin\BannerController::class, 'index'])->name('banners.index');
    Route::post('/banners', [Admin\BannerController::class, 'store'])->name('banners.store');
    Route::put('/banners/{banner}', [Admin\BannerController::class, 'update'])->name('banners.update');
    Route::delete('/banners/{banner}', [Admin\BannerController::class, 'destroy'])->name('banners.destroy');
});
