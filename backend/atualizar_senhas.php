<?php

require __DIR__.'/vendor/autoload.php';

$app = require_once __DIR__.'/bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\DB;

$novoHashSenha123 = Hash::make('senha123');

echo "Novo hash para 'senha123': $novoHashSenha123\n\n";


$resultado = DB::table('usuarios')->update(['senha' => $novoHashSenha123]);


echo "Usuários atualizados:\n";
$usuarios = DB::table('usuarios')->select('id', 'nome', 'email')->get();

foreach ($usuarios as $usuario) {
    echo "  - {$usuario->nome} ({$usuario->email})\n";
}
