<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Certificado extends Model
{
    protected $table = 'certificados';
    
    protected $fillable = [
        'usuario_id',
        'evento_id',
        'codigo_validacao',
        'data_emissao',
        'url_arquivo'
    ];

    protected $casts = [
        'data_emissao' => 'datetime',
        'created_at' => 'datetime'
    ];

    public $timestamps = false;

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }

    public function evento(): BelongsTo
    {
        return $this->belongsTo(Evento::class, 'evento_id');
    }
}