<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Log extends Model
{
    protected $table = 'logs';
    
    protected $fillable = [
        'usuario_id',
        'endpoint',
        'metodo',
        'ip_address',
        'user_agent',
        'request_body',
        'response_status'
    ];

    protected $casts = [
        'usuario_id' => 'integer',
        'response_status' => 'integer',
        'created_at' => 'datetime'
    ];

    public $timestamps = false;
}
