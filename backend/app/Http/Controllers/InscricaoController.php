<?php

namespace App\Http\Controllers;

use App\Models\Inscricao;
use App\Models\Evento;
use App\Models\Usuario;
use App\Services\EmailService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\Log;

class InscricaoController extends Controller
{
    /**
     * GET /api/inscricoes
     */
    public function listar(Request $request)
    {
        try {
            $query = Inscricao::with(['usuario', 'evento', 'presenca']);

            // Filtrar por usuário
            if ($request->has('usuario_id')) {
                $query->where('usuario_id', $request->usuario_id);
            }

            // Filtrar por evento
            if ($request->has('evento_id')) {
                $query->where('evento_id', $request->evento_id);
            }

            // Filtrar por status
            if ($request->has('status')) {
                $query->where('status', $request->status);
            }

            // Filtrar apenas com presença
            if ($request->has('com_presenca') && $request->com_presenca) {
                $query->whereHas('presenca');
            }

            $inscricoes = $query->orderBy('created_at', 'desc')->get();

            $this->registrarLog($request, 'GET', '/api/inscricoes', 200);

            return response()->json([
                'success' => true,
                'message' => 'Inscrições recuperadas com sucesso',
                'data' => $inscricoes->map(function ($inscricao) {
                    return [
                        'id' => $inscricao->id,
                        'usuario_id' => $inscricao->usuario_id,
                        'evento_id' => $inscricao->evento_id,
                        'status' => $inscricao->status,
                        'created_at' => $inscricao->created_at->format('Y-m-d H:i:s'),
                        'usuario' => $inscricao->usuario ? [
                            'id' => $inscricao->usuario->id,
                            'nome' => $inscricao->usuario->nome,
                            'email' => $inscricao->usuario->email
                        ] : null,
                        'evento' => $inscricao->evento ? [
                            'id' => $inscricao->evento->id,
                            'titulo' => $inscricao->evento->nome,
                            'data_inicio' => $inscricao->evento->data_inicio ? $inscricao->evento->data_inicio->format('Y-m-d H:i:s') : null,
                            'data_fim' => $inscricao->evento->data_fim ? $inscricao->evento->data_fim->format('Y-m-d H:i:s') : null,
                            'local' => $inscricao->evento->local
                        ] : null,
                        'possui_presenca' => $inscricao->presenca !== null,
                        'presenca' => $inscricao->presenca ? [
                            'data_presenca' => $inscricao->presenca->data_presenca ? $inscricao->presenca->data_presenca->format('Y-m-d H:i:s') : null
                        ] : null
                    ];
                })
            ], 200);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/inscricoes', 500);
            return response()->json([
                'success' => false,
                'message' => 'Erro ao buscar inscrições',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * GET /api/usuarios/{usuarioId}/inscricoes
     */
    public function listarPorUsuario(Request $request, $usuarioId)
    {
        try {
            $usuario = Usuario::findOrFail($usuarioId);

            $inscricoes = Inscricao::where('usuario_id', $usuarioId)
                ->with(['evento', 'presenca'])
                ->orderBy('created_at', 'desc')
                ->get();

            $this->registrarLog($request, 'GET', '/api/usuarios/' . $usuarioId . '/inscricoes', 200, $usuarioId);

            return response()->json([
                'success' => true,
                'message' => 'Inscrições do usuário recuperadas com sucesso',
                'data' => $inscricoes->map(function ($inscricao) {
                    return [
                        'id' => $inscricao->id,
                        'status' => $inscricao->status,
                        'data_inscricao' => $inscricao->created_at ? $inscricao->created_at->format('Y-m-d H:i:s') : null,
                        'evento' => [
                            'id' => $inscricao->evento->id,
                            'titulo' => $inscricao->evento->nome,
                            'data_inicio' => $inscricao->evento->data_inicio ? $inscricao->evento->data_inicio->format('Y-m-d H:i:s') : null,
                            'data_fim' => $inscricao->evento->data_fim ? $inscricao->evento->data_fim->format('Y-m-d H:i:s') : null,
                            'local' => $inscricao->evento->local
                        ],
                        'possui_presenca' => $inscricao->presenca !== null,
                        'data_presenca' => $inscricao->presenca && $inscricao->presenca->data_presenca ? $inscricao->presenca->data_presenca->format('Y-m-d H:i:s') : null
                    ];
                })
            ], 200);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/usuarios/' . $usuarioId . '/inscricoes', 404);
            return response()->json([
                'success' => false,
                'message' => 'Usuário não encontrado'
            ], 404);
        }
    }

    public function criar(Request $request)
    {
        try {
            $validator = Validator::make($request->all(), [
                'evento_id' => 'required|integer'
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Dados inválidos',
                    'errors' => $validator->errors()
                ], 422);
            }

            // Pegar usuário autenticado
            $usuario = $request->user();
            if (!$usuario) {
                return response()->json([
                    'success' => false,
                    'message' => 'Usuário não autenticado'
                ], 401);
            }

            // Verificar se evento existe e está ativo
            $evento = Evento::find($request->evento_id);
            if (!$evento) {
                return response()->json([
                    'success' => false,
                    'message' => 'Evento não encontrado'
                ], 404);
            }

            if ($evento->status !== 'aberto') {
                return response()->json([
                    'success' => false,
                    'message' => 'Evento não está disponível para inscrições'
                ], 400);
            }

            // Verificar vagas
            $totalInscritos = Inscricao::where('evento_id', $evento->id)
                ->where('status', 'confirmada')
                ->count();

            if ($totalInscritos >= $evento->vagas) {
                return response()->json([
                    'success' => false,
                    'message' => 'Não há vagas disponíveis para este evento'
                ], 400);
            }

            // Verificar se usuário já está inscrito neste evento (qualquer status)
            $inscricaoExistente = Inscricao::where('usuario_id', $usuario->id)
                ->where('evento_id', $request->evento_id)
                ->first();

            if ($inscricaoExistente) {
                if ($inscricaoExistente->status === 'confirmada') {
                    return response()->json([
                        'success' => false,
                        'message' => 'Você já está inscrito neste evento'
                    ], 400);
                } elseif ($inscricaoExistente->status === 'cancelada') {
                    // Reativar inscrição cancelada
                    $inscricaoExistente->status = 'confirmada';
                    $inscricaoExistente->data_inscricao = now();
                    $inscricaoExistente->save();
                    $inscricao = $inscricaoExistente;
                    $mensagem = 'Inscrição reativada com sucesso! Verifique seu e-mail.';
                } else {
                    // Para outros status, atualizar para confirmada
                    $inscricaoExistente->status = 'confirmada';
                    $inscricaoExistente->data_inscricao = now();
                    $inscricaoExistente->save();
                    $inscricao = $inscricaoExistente;
                    $mensagem = 'Inscrição atualizada com sucesso! Verifique seu e-mail.';
                }
            } else {
                // Criar nova inscrição
                $usuarioId = $request->has('usuario_id') ? $request->usuario_id : $usuario->id;
                
                $inscricao = Inscricao::create([
                    'usuario_id' => $usuarioId,
                    'evento_id' => $request->evento_id,
                    'status' => 'confirmada',
                    'data_inscricao' => now()
                ]);
                $mensagem = 'Inscrição realizada com sucesso! Verifique seu e-mail.';
            }

            try {
                $usuarioInscricao = Usuario::findOrFail($usuarioId);
                
                $emailService = new EmailService();
                $emailService->enviarEmailInscricao($usuarioInscricao, $evento);
            } catch (\Exception $e) {
                Log::error('Erro ao enviar email de inscrição: ' . $e->getMessage());
            }

            $this->registrarLog($request, 'POST', '/api/inscricoes', 201, $usuario->id);

            return response()->json([
                'success' => true,
                'message' => $mensagem,
                'data' => [
                    'id' => $inscricao->id,
                    'usuario' => [
                        'id' => $usuario->id,
                        'nome' => $usuario->nome,
                        'email' => $usuario->email
                    ],
                    'evento' => [
                        'id' => $evento->id,
                        'titulo' => $evento->nome,
                        'data_inicio' => $evento->data_inicio->format('Y-m-d H:i:s')
                    ],
                    'status' => $inscricao->status,
                    'data_inscricao' => $inscricao->created_at->format('Y-m-d H:i:s')
                ]
            ], 201);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'POST', '/api/inscricoes', 500);

            Log::error('Erro ao criar inscrição: ' . $e->getMessage());
            Log::error('Stack trace: ' . $e->getTraceAsString());

            return response()->json([
                'success' => false,
                'message' => 'Erro ao criar inscrição',
                'error' => $e->getMessage(),
                'debug' => [
                    'file' => $e->getFile(),
                    'line' => $e->getLine()
                ]
            ], 500);
        }
    }
    public function buscar(Request $request, $id)
    {
        try {
            $inscricao = Inscricao::with(['usuario', 'evento', 'presenca'])->findOrFail($id);

            $this->registrarLog($request, 'GET', '/api/inscricoes/' . $id, 200);

            return response()->json([
                'success' => true,
                'message' => 'Inscrição encontrada',
                'data' => [
                    'id' => $inscricao->id,
                    'usuario' => ['id' => $inscricao->usuario->id, 'nome' => $inscricao->usuario->nome, 'email' => $inscricao->usuario->email],
                    'evento' => ['id' => $inscricao->evento->id, 'titulo' => $inscricao->evento->nome, 'data_inicio' => $inscricao->evento->data_inicio->format('Y-m-d H:i:s'), 'local' => $inscricao->evento->local],
                    'status' => $inscricao->status,
                    'data_inscricao' => $inscricao->created_at->format('Y-m-d H:i:s'),
                    'possui_presenca' => $inscricao->presenca !== null,
                    'data_presenca' => $inscricao->presenca ? $inscricao->presenca->data_presenca->format('Y-m-d H:i:s') : null
                ]
            ], 200);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/inscricoes/' . $id, 404);
            return response()->json(['success' => false, 'message' => 'Inscrição não encontrada'], 404);
        }
    }

    public function cancelar(Request $request, $id)
    {
        try {
            $inscricao = Inscricao::with(['usuario', 'evento'])->findOrFail($id);

            if ($inscricao->status === 'cancelada') {
                return response()->json(['success' => false, 'message' => 'Inscrição já está cancelada'], 400);
            }

            $presenca = \App\Models\Presenca::where('inscricao_id', $inscricao->id)->first();

            if ($presenca) {
                return response()->json(['success' => false, 'message' => 'Não é possível cancelar inscrição com presença registrada'], 400);
            }

            $inscricao->status = 'cancelada';
            $inscricao->save();

            try {
                $emailService = new EmailService();
                $emailService->enviarEmailCancelamento($inscricao->usuario, $inscricao->evento);
            } catch (\Exception $e) {
                Log::error('Erro ao enviar email de cancelamento: ' . $e->getMessage());
            }

            $this->registrarLog($request, 'DELETE', '/api/inscricoes/' . $id, 200, $inscricao->usuario_id);

            return response()->json([
                'success' => true,
                'message' => 'Inscrição cancelada com sucesso. Um e-mail de confirmação foi enviado.',
                'data' => ['id' => $inscricao->id, 'status' => $inscricao->status]
            ], 200);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'DELETE', '/api/inscricoes/' . $id, 500);
            return response()->json(['success' => false, 'message' => 'Erro ao cancelar inscrição', 'error' => $e->getMessage()], 500);
        }
    }

    private function registrarLog(Request $request, $metodo, $endpoint, $status, $usuarioId = null)
    {
        try {
            Log::info([
                'usuario_id' => $usuarioId,
                'endpoint' => $endpoint,
                'metodo' => $metodo,
                'ip_address' => $request->ip(),
                'user_agent' => $request->userAgent(),
                'request_body' => json_encode($request->all()),
                'response_status' => $status
            ]);
        } catch (\Exception $e) {
        }
    }
}
