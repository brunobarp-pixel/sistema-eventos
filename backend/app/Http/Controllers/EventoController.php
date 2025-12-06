<?php

namespace App\Http\Controllers;

use App\Models\Evento;
use App\Models\Log;
use Illuminate\Http\Request;

class EventoController extends Controller
{
    /**
     * GET /api/eventos
     */
    public function listar(Request $request)
    {
        try {
            $query = Evento::query();

            // Filtrar por status
            if ($request->has('status')) {
                $query->where('status', $request->status);
            } else {
                // Mostrar todos os eventos para debug
                // $query->where('status', 'aberto');
            }

            // Ordenar por data de início
            $eventos = $query->orderBy('data_inicio', 'asc')->get();

            $this->registrarLog($request, 'GET', '/api/eventos', 200);

            return response()->json([
                'success' => true,
                'message' => 'Eventos recuperados com sucesso',
                'data' => $eventos->map(function($evento) {
                    return [
                        'id' => $evento->id,
                        'titulo' => $evento->nome,
                        'descricao' => $evento->descricao,
                        'data_inicio' => $evento->data_inicio->format('Y-m-d H:i:s'),
                        'data_fim' => $evento->data_fim->format('Y-m-d H:i:s'),
                        'local' => $evento->local,
                        'vagas' => $evento->vagas,
                        'status' => $evento->status,
                        'total_inscritos' => $evento->inscricoes()->where('status', 'confirmada')->count()
                    ];
                })
            ], 200);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/eventos', 500);
            
            return response()->json([
                'success' => false,
                'message' => 'Erro ao buscar eventos',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * GET /api/eventos/{id}
     */
    public function buscar(Request $request, $id)
    {
        try {
            $evento = Evento::findOrFail($id);

            // Contar inscrições ativas
            $totalInscritos = $evento->inscricoes()->where('status', 'confirmada')->count();

            $this->registrarLog($request, 'GET', '/api/eventos/' . $id, 200);

            return response()->json([
                'success' => true,
                'message' => 'Evento encontrado',
                'data' => [
                    'id' => $evento->id,
                    'titulo' => $evento->nome,
                    'descricao' => $evento->descricao,
                    'data_inicio' => $evento->data_inicio->format('Y-m-d H:i:s'),
                    'data_fim' => $evento->data_fim->format('Y-m-d H:i:s'),
                    'local' => $evento->local,
                    'vagas' => $evento->vagas,
                    'vagas_disponiveis' => max(0, $evento->vagas - $totalInscritos),
                    'status' => $evento->status,
                    'carga_horaria' => $evento->carga_horaria ?? null,
                    'total_inscritos' => $totalInscritos
                ]
            ], 200);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/eventos/' . $id, 404);
            
            return response()->json([
                'success' => false,
                'message' => 'Evento não encontrado',
                'error' => $e->getMessage()
            ], 404);
        }
    }

    /**
     * GET /api/eventos/{id}/inscritos
     */
    public function listarInscritos(Request $request, $id)
    {
        try {
            $evento = Evento::findOrFail($id);

            $inscritos = $evento->inscricoes()
                ->where('status', 'confirmada')
                ->with(['usuario'])
                ->orderBy('data_inscricao', 'desc')
                ->get();

            $this->registrarLog($request, 'GET', '/api/eventos/' . $id . '/inscritos', 200);

            return response()->json([
                'success' => true,
                'message' => 'Inscritos do evento recuperados com sucesso',
                'data' => $inscritos->map(function($inscricao) {
                    return [
                        'inscricao_id' => $inscricao->id,
                        'usuario_id' => $inscricao->usuario_id,
                        'nome' => $inscricao->usuario->nome,
                        'email' => $inscricao->usuario->email,
                        'cpf' => $inscricao->usuario->cpf,
                        'telefone' => $inscricao->usuario->telefone ?? null,
                        'data_inscricao' => $inscricao->data_inscricao->format('Y-m-d H:i:s'),
                        'status' => $inscricao->status,
                        'tem_presenca' => $inscricao->presencas()->exists()
                    ];
                })
            ], 200);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/eventos/' . $id . '/inscritos', 404);
            
            return response()->json([
                'success' => false,
                'message' => 'Erro ao buscar inscritos do evento',
                'error' => $e->getMessage()
            ], 404);
        }
    }

    /**
     * Registrar log de acesso
     */
    private function registrarLog(Request $request, $metodo, $endpoint, $status, $usuarioId = null)
    {
        try {
            Log::create([
                'usuario_id' => $usuarioId,
                'endpoint' => $endpoint,
                'metodo' => $metodo,
                'ip_address' => $request->ip(),
                'user_agent' => $request->userAgent(),
                'request_body' => json_encode($request->all()),
                'response_status' => $status
            ]);
        } catch (\Exception $e) {
            // Silenciar erro
        }
    }
}