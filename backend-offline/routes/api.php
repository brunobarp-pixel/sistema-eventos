<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\OfflineController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

Route::prefix('offline')->group(function () {
    // Carregar dados para funcionamento offline
    Route::get('/dados', [OfflineController::class, 'carregarDadosOffline']);
    
    // Sincronizar presenças marcadas offline
    Route::post('/sincronizar-presencas', [OfflineController::class, 'sincronizarPresencas']);
    
    // Verificar status de conectividade
    Route::get('/status', [OfflineController::class, 'statusConectividade']);
});

// Rotas para buscar dados individuais
Route::get('/presencas', [OfflineController::class, 'buscarPresencas']);
Route::get('/usuarios', [OfflineController::class, 'buscarUsuarios']);
Route::get('/inscricoes', [OfflineController::class, 'buscarInscricoes']);
Route::post('/validar-token', [OfflineController::class, 'validarToken']);

// Health check route
Route::get('/health', function () {
    return response()->json([
        'status' => 'ok',
        'service' => 'backend-offline',
        'timestamp' => now()->toISOString()
    ]);
});