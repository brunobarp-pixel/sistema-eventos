<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Inscricao extends Model
{
    protected $table = 'inscricoes';
    
    protected $fillable = [
        'usuario_id',
        'evento_id',
        'status',
        'data_inscricao',
        'sincronizado'
    ];

    protected $casts = [
        'data_inscricao' => 'datetime',
        'sincronizado' => 'boolean',
        'created_at' => 'datetime',
        'updated_at' => 'datetime'
    ];

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }

    public function evento(): BelongsTo
    {
        return $this->belongsTo(Evento::class, 'evento_id');
    }

    public function presenca(): HasOne
    {
        return $this->hasOne(Presenca::class, 'inscricao_id');
    }
}