<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Evento extends Model
{
    protected $table = 'eventos';
    
    protected $fillable = [
        'nome',
        'descricao',
        'conteudo',
        'data_inicio',
        'data_fim',
        'local',
        'cidade',
        'estado',
        'vagas',
        'vagas_ocupadas',
        'imagem',
        'status',
        'ativo',
        'organizador_id'
    ];

    protected $casts = [
        'data_inicio' => 'datetime',
        'data_fim' => 'datetime',
        'vagas' => 'integer',
        'vagas_ocupadas' => 'integer',
        'ativo' => 'boolean',
        'created_at' => 'datetime',
        'updated_at' => 'datetime'
    ];

    public function inscricoes(): HasMany
    {
        return $this->hasMany(Inscricao::class, 'evento_id');
    }
}