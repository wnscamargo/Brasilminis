<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Cart extends Model
{
    protected $fillable = ['user_id', 'session_id'];

    public function items()
    {
        return $this->hasMany(CartItem::class);
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function subtotal(): float
    {
        return (float) $this->items->sum(fn ($i) => $i->price * $i->quantity);
    }

    public function count(): int
    {
        return (int) $this->items->sum('quantity');
    }
}
