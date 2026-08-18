<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Product extends Model
{
    use HasFactory;

    protected $fillable = [
        'name', 'slug', 'sku', 'barcode', 'description', 'group',
        'category_id', 'brand_id', 'manufacturer_id',
        'price', 'compare_at_price', 'stock', 'badges',
        'featured', 'is_active', 'rating', 'reviews_count',
        'meta_title', 'meta_description', 'legacy_id',
    ];

    protected function casts(): array
    {
        return [
            'badges' => 'array',
            'price' => 'decimal:2',
            'compare_at_price' => 'decimal:2',
            'featured' => 'boolean',
            'is_active' => 'boolean',
            'rating' => 'decimal:1',
        ];
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    // Relationships
    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    public function brand()
    {
        return $this->belongsTo(Brand::class);
    }

    public function manufacturer()
    {
        return $this->belongsTo(Manufacturer::class);
    }

    public function images()
    {
        return $this->hasMany(ProductImage::class)->orderBy('position');
    }

    public function attributes()
    {
        return $this->hasMany(ProductAttribute::class);
    }

    public function variants()
    {
        return $this->hasMany(ProductVariant::class);
    }

    public function reviews()
    {
        return $this->hasMany(Review::class);
    }

    // Accessors
    public function getMainImageAttribute(): ?string
    {
        return $this->images->first()?->path;
    }

    public function getDiscountPercentAttribute(): int
    {
        if ($this->compare_at_price && $this->compare_at_price > $this->price) {
            return (int) round((1 - $this->price / $this->compare_at_price) * 100);
        }
        return 0;
    }

    // Scopes
    public function scopeActive(Builder $q): Builder
    {
        return $q->where('is_active', true);
    }

    public function scopeFeatured(Builder $q): Builder
    {
        return $q->where('featured', true);
    }

    public function scopeOnSale(Builder $q): Builder
    {
        return $q->whereNotNull('compare_at_price')->whereColumn('compare_at_price', '>', 'price');
    }

    public function scopeSearch(Builder $q, ?string $term): Builder
    {
        if (! $term) {
            return $q;
        }
        return $q->where(function ($sub) use ($term) {
            $sub->where('name', 'like', "%{$term}%")
                ->orWhere('description', 'like', "%{$term}%");
        });
    }

    public function scopeBadge(Builder $q, ?string $badge): Builder
    {
        if (! $badge) {
            return $q;
        }
        return $q->whereJsonContains('badges', $badge);
    }

    public function recomputeRating(): void
    {
        $count = $this->reviews()->count();
        $avg = $count ? round($this->reviews()->avg('rating'), 1) : 0;
        $this->update(['rating' => $avg, 'reviews_count' => $count]);
    }
}
