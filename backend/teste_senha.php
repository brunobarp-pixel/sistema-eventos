<?php
// testar_senha.php

require __DIR__.'/vendor/autoload.php';

$app = require_once __DIR__.'/bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use Illuminate\Support\Facades\Hash;

$senha = 'senha123';
$hash = '$2y$12$LQv3c1yOC38StN7yKCdEJOgP2O8XkMYPzwXxLB3xXqMZY/QMQlcYK';

echo "Senha: $senha\n";
echo "Hash: $hash\n";
echo "Match: " . (Hash::check($senha, $hash) ? 'SIM ✅' : 'NÃO ❌') . "\n";

// Gerar novo hash
$novoHash = Hash::make($senha);
echo "\nNovo hash gerado: $novoHash\n";
echo "Novo hash funciona: " . (Hash::check($senha, $novoHash) ? 'SIM ✅' : 'NÃO ❌') . "\n";

