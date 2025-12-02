<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Laravel\Sanctum\HasApiTokens;

class Usuario extends Model
{
    use HasApiTokens; 
    
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

    public function certificados(): HasMany
    {
        return $this->hasMany(Certificado::class, 'usuario_id');
    }

    public function verificarDadosCompletos(): bool
    {
        return !empty($this->nome) && 
               !empty($this->email) && 
               !empty($this->cpf) && 
               !empty($this->telefone);
    }
}