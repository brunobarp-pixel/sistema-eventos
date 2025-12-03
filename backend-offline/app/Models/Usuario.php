<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Usuario extends Model
{
    protected $table = 'usuarios';
    
    protected $fillable = [
        'nome',
        'email',
        'cpf',
        'telefone',
        'senha',
        'dados_completos'
    ];

    protected $hidden = [
        'senha'
    ];

    protected $casts = [
        'dados_completos' => 'boolean',
        'created_at' => 'datetime',
        'updated_at' => 'datetime'
    ];

    public function inscricoes(): HasMany
    {
        return $this->hasMany(Inscricao::class, 'usuario_id');
    }
}