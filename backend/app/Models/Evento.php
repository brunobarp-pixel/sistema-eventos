<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Evento extends Model
{
    protected $table = 'eventos';
    
    protected $fillable = [
        'titulo',
        'descricao',
        'data_inicio',
        'data_fim',
        'local',
        'vagas',
        'carga_horaria',  // 🆕 ADICIONADO
        'template_certificado',
        'status'
    ];

    protected $casts = [
        'data_inicio' => 'datetime',
        'data_fim' => 'datetime',
        'vagas' => 'integer',
        'carga_horaria' => 'integer',  // 🆕 ADICIONADO
        'created_at' => 'datetime',
        'updated_at' => 'datetime'
    ];

    public function inscricoes(): HasMany
    {
        return $this->hasMany(Inscricao::class, 'evento_id');
    }

    public function certificados(): HasMany
    {
        return $this->hasMany(Certificado::class, 'evento_id');
    }
}