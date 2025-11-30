<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Presenca extends Model
{
    protected $table = 'presencas';
    
    protected $fillable = [
        'inscricao_id',
        'evento_id',
        'usuario_id',
        'data_checkin',
        'data_checkout',
        'tipo_marcacao',
        'observacoes'
    ];

    protected $casts = [
        'data_checkin' => 'datetime',
        'data_checkout' => 'datetime'
    ];

    public $timestamps = true;
    
    public function inscricao(): BelongsTo
    {
        return $this->belongsTo(Inscricao::class, 'inscricao_id');
    }

    public function evento(): BelongsTo
    {
        return $this->belongsTo(Evento::class, 'evento_id');
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }
}