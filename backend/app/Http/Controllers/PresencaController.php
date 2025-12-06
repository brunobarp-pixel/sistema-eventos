<?php

namespace App\Http\Controllers;

use App\Models\Presenca;
use App\Models\Inscricao;
use App\Models\Log;
use App\Services\EmailService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class PresencaController extends Controller
{
    public function registrar(Request $request)
    {
        try {
            $validator = Validator::make($request->all(), [
                'inscricao_id' => 'required|exists:inscricoes,id'
            ]);

            if ($validator->fails()) {
                return response()->json(['success' => false, 'message' => 'Dados inválidos', 'errors' => $validator->errors()], 422);
            }

            $inscricao = Inscricao::findOrFail($request->inscricao_id);

            if ($inscricao->status !== 'confirmada') {
                return response()->json(['success' => false, 'message' => 'Inscrição não confirmada'], 400);
            }

            $presencaExistente = Presenca::where('inscricao_id', $inscricao->id)->first();
            if ($presencaExistente) {
                return response()->json([
                    'success' => false,
                    'message' => 'Presença já registrada',
                    'data' => ['data_presenca' => $presencaExistente->data_presenca->format('Y-m-d H:i:s')]
                ], 400);
            }

            $presenca = Presenca::create([
                'inscricao_id' => $inscricao->id,
                'evento_id' => $inscricao->evento_id,
                'usuario_id' => $inscricao->usuario_id,
                'data_checkin' => now(),
                'tipo_marcacao' => 'presencial'
            ]);

            $inscricao = Inscricao::with('usuario', 'evento')->find($inscricao->id);

            try {
                \Illuminate\Support\Facades\Log::info('Iniciando envio de email de check-in', [
                    'usuario_id' => $inscricao->usuario->id,
                    'usuario_nome' => $inscricao->usuario->nome,
                    'usuario_email' => $inscricao->usuario->email,
                    'evento_id' => $inscricao->evento->id,
                    'evento_nome' => $inscricao->evento->nome
                ]);
                
                $emailService = new EmailService();
                $resultado = $emailService->enviarEmailCheckin($inscricao->usuario, $inscricao->evento);
                
                if ($resultado) {
                    \Illuminate\Support\Facades\Log::info('Email de check-in enviado com sucesso');
                } else {
                    \Illuminate\Support\Facades\Log::warning('Email de check-in retornou false');
                }
            } catch (\Exception $e) {
                \Illuminate\Support\Facades\Log::error('Erro ao enviar email de check-in', [
                    'usuario_id' => $inscricao->usuario->id ?? 'N/A',
                    'evento_id' => $inscricao->evento->id ?? 'N/A',
                    'error' => $e->getMessage(),
                    'trace' => $e->getTraceAsString()
                ]);
            }

            $this->registrarLog($request, 'POST', '/api/presencas', 201, $inscricao->usuario_id);

            return response()->json([
                'success' => true,
                'message' => 'Presença registrada com sucesso',
                'data' => [
                    'id' => $presenca->id,
                    'inscricao_id' => $inscricao->id,
                    'usuario' => ['id' => $inscricao->usuario->id, 'nome' => $inscricao->usuario->nome, 'email' => $inscricao->usuario->email],
                    'evento' => ['id' => $inscricao->evento->id, 'titulo' => $inscricao->evento->titulo],
                    'data_presenca' => optional($presenca->data_presenca)->format('Y-m-d H:i:s')
                ]
            ], 201);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'POST', '/api/presencas', 500);
            return response()->json(['success' => false, 'message' => 'Erro', 'error' => $e->getMessage()], 500);
        }
    }

    private function registrarLog(Request $request, $metodo, $endpoint, $status, $usuarioId = null)
    {
        try {
            Log::create([
                'usuario_id' => $usuarioId,
                'endpoint' => $endpoint,
                'metodo' => $metodo,
                'ip_address' => $request->ip(),
                'user_agent' => $request->userAgent(),
                'request_body' => json_encode($request->except(['senha', 'password'])),
                'response_status' => $status
            ]);
        } catch (\Exception $e) {}
    }
}