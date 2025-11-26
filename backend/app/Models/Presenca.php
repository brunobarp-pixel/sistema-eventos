<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Presenca extends Model
{
    protected $table = 'presencas';
    
    protected $fillable = [
        'inscricao_id',
        'data_presenca',
        'sincronizado'
    ];

    protected $casts = [
        'data_presenca' => 'datetime',
        'sincronizado' => 'boolean'
    ];

    public $timestamps = false;
    
    // Adicionar created_at
    const CREATED_AT = 'created_at';
    const UPDATED_AT = null;
    
    public function inscricao(): BelongsTo
    {
        return $this->belongsTo(Inscricao::class, 'inscricao_id');
    }
}