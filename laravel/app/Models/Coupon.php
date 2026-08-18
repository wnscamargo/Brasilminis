<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Coupon extends Model
{
    protected $fillable = ['code', 'type', 'value', 'min_order', 'active', 'description', 'starts_at', 'ends_at'];

    protected function casts(): array
    {
        return [
            'active' => 'boolean',
            'value' => 'decimal:2',
            'min_order' => 'decimal:2',
            'starts_at' => 'datetime',
            'ends_at' => 'datetime',
        ];
    }

    public function isValid(): bool
    {
        if (! $this->active) {
            return false;
        }
        $now = now();
        if ($this->starts_at && $this->starts_at->gt($now)) {
            return false;
        }
        if ($this->ends_at && $this->ends_at->lt($now)) {
            return false;
        }
        return true;
    }

    public function discountFor(float $subtotal): float
    {
        if ($subtotal < (float) $this->min_order) {
            return 0;
        }
        $discount = $this->type === 'percent'
            ? round($subtotal * (float) $this->value / 100, 2)
            : (float) $this->value;

        return (float) min($discount, $subtotal);
    }
}
