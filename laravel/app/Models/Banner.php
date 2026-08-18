<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Banner extends Model
{
    protected $fillable = ['title', 'subtitle', 'image', 'cta_text', 'cta_link', 'position', 'active'];

    protected function casts(): array
    {
        return ['active' => 'boolean'];
    }
}
