<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    protected $fillable = [
        'order_number', 'user_id', 'status', 'payment_method', 'payment_status',
        'subtotal', 'discount', 'shipping', 'total', 'coupon_code',
        'shipping_method', 'address', 'legacy_id',
    ];

    protected function casts(): array
    {
        return [
            'address' => 'array',
            'subtotal' => 'decimal:2',
            'discount' => 'decimal:2',
            'shipping' => 'decimal:2',
            'total' => 'decimal:2',
        ];
    }

    public const STATUSES = [
        'PENDING', 'AWAITING_PAYMENT', 'PAID', 'PROCESSING',
        'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED',
    ];

    public const STATUS_LABELS = [
        'PENDING' => 'Pendente',
        'AWAITING_PAYMENT' => 'Aguardando pagamento',
        'PAID' => 'Pago',
        'PROCESSING' => 'Em separação',
        'SHIPPED' => 'Enviado',
        'DELIVERED' => 'Entregue',
        'CANCELLED' => 'Cancelado',
        'REFUNDED' => 'Reembolsado',
    ];

    public function items()
    {
        return $this->hasMany(OrderItem::class);
    }

    public function history()
    {
        return $this->hasMany(OrderStatusHistory::class)->latest();
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function statusLabel(): string
    {
        return self::STATUS_LABELS[$this->status] ?? $this->status;
    }
}
