<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class OrderItem extends Model
{
    protected $fillable = [
        'order_id', 'product_id', 'variant_id', 'name', 'slug',
        'image', 'price', 'quantity', 'line_total',
    ];

    public function order()
    {
        return $this->belongsTo(Order::class);
    }
}
