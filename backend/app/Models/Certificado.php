<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\SoftDeletes;

class Certificado extends Model
{
    use SoftDeletes;
    
    protected $table = 'certificados';
    
    protected $fillable = [
        'usuario_id',
        'evento_id',
        'inscricao_id',
        'codigo_validacao',
        'data_emissao',
        'arquivo_pdf',
        'enviado_email'
    ];

    protected $casts = [
        'data_emissao' => 'datetime',
        'enviado_email' => 'boolean',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
        'deleted_at' => 'datetime'
    ];

    public $timestamps = true;

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(Usuario::class, 'usuario_id');
    }

    public function evento(): BelongsTo
    {
        return $this->belongsTo(Evento::class, 'evento_id');
    }

    public function inscricao(): BelongsTo
    {
        return $this->belongsTo(Inscricao::class, 'inscricao_id');
    }
}