<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\EventoController;
use App\Http\Controllers\InscricaoController;
use App\Http\Controllers\PresencaController;
use App\Http\Controllers\CertificadoController;

// ========== ROTAS PÚBLICAS (SEM AUTENTICAÇÃO) ==========

// Status da API
Route::get('/status', function () {
    return response()->json([
        'success' => true,
        'message' => 'API Sistema de Eventos - Online',
        'version' => '1.0.0',
        'timestamp' => now()->toDateTimeString()
    ]);
});

// Autenticação e Cadastro
Route::post('/auth', [AuthController::class, 'login']);
Route::post('/usuarios', [AuthController::class, 'cadastrar']);

// Eventos (visualização pública)
Route::get('/eventos', [EventoController::class, 'listar']);
Route::get('/eventos/{id}', [EventoController::class, 'buscar']);
Route::get('/eventos/{id}/inscritos', [EventoController::class, 'listarInscritos']);

// Validação de Certificado (público)
Route::get('/certificados/{codigo}', [CertificadoController::class, 'validar']);

// ========== ROTAS PROTEGIDAS (REQUEREM AUTENTICAÇÃO) ==========

Route::middleware('auth:sanctum')->group(function () {
    
    // ===== AUTENTICAÇÃO =====
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', [AuthController::class, 'me']);
    
    // ===== USUÁRIOS =====
    Route::get('/usuarios', [AuthController::class, 'index']);
    Route::put('/usuarios/{id}', [AuthController::class, 'completarDados']);
    
    // ===== INSCRIÇÕES =====
    Route::get('/inscricoes', [InscricaoController::class, 'listar']);
    Route::get('/usuarios/{usuarioId}/inscricoes', [InscricaoController::class, 'listarPorUsuario']);
    Route::post('/inscricoes', [InscricaoController::class, 'criar']);
    Route::get('/inscricoes/{id}', [InscricaoController::class, 'buscar']);
    Route::delete('/inscricoes/{id}', [InscricaoController::class, 'cancelar']);
    
    // ===== PRESENÇAS =====
    Route::post('/presencas', [PresencaController::class, 'registrar']);
    
    // ===== CERTIFICADOS =====
    Route::post('/certificados', [CertificadoController::class, 'emitir']);
    Route::get('/certificados/usuario/{usuarioId}', [CertificadoController::class, 'listarPorUsuario']);
    Route::get('/certificados/debug', [CertificadoController::class, 'debug']);
    Route::get('/certificados/{id}/pdf', [CertificadoController::class, 'gerarPDF']);
});