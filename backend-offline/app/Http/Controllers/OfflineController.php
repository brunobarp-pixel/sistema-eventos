<?php

namespace App\Http\Controllers;

use App\Models\Evento;
use App\Models\Inscricao;
use App\Models\Presenca;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class OfflineController extends Controller
{
    /**
     * Carregar todos os dados necessários para funcionamento offline
     */
    public function carregarDadosOffline(): JsonResponse
    {
        try {
            // Buscar eventos com status: aberto, planejamento, em_andamento
            $eventos = Evento::whereIn('status', ['aberto', 'planejamento', 'em_andamento'])
                ->where('ativo', true)
                ->with([
                    'inscricoes' => function ($query) {
                        $query->with(['usuario', 'presenca']);
                    }
                ])
                ->get();

            // Preparar dados estruturados
            $dadosOffline = [];
            
            foreach ($eventos as $evento) {
                $inscricoes = [];
                $presencas = [];
                
                foreach ($evento->inscricoes as $inscricao) {
                    $inscricoes[] = [
                        'id' => $inscricao->id,
                        'evento_id' => $inscricao->evento_id,
                        'usuario_id' => $inscricao->usuario_id,
                        'usuario_nome' => $inscricao->usuario->nome,
                        'usuario_email' => $inscricao->usuario->email,
                        'usuario_cpf' => $inscricao->usuario->cpf,
                        'status' => $inscricao->status,
                        'presente' => $inscricao->presente,
                        'data_presenca' => $inscricao->data_presenca,
                        'observacoes' => $inscricao->observacoes
                    ];
                    
                    if ($inscricao->presenca) {
                        $presencas[] = [
                            'id' => $inscricao->presenca->id,
                            'inscricao_id' => $inscricao->presenca->inscricao_id,
                            'evento_id' => $inscricao->presenca->evento_id,
                            'usuario_id' => $inscricao->presenca->usuario_id,
                            'data_checkin' => $inscricao->presenca->data_checkin,
                            'data_checkout' => $inscricao->presenca->data_checkout,
                            'tipo_marcacao' => $inscricao->presenca->tipo_marcacao,
                            'observacoes' => $inscricao->presenca->observacoes
                        ];
                    }
                }
                
                $dadosOffline[] = [
                    'evento' => [
                        'id' => $evento->id,
                        'nome' => $evento->nome,
                        'descricao' => $evento->descricao,
                        'data_inicio' => $evento->data_inicio,
                        'data_fim' => $evento->data_fim,
                        'local' => $evento->local,
                        'cidade' => $evento->cidade,
                        'estado' => $evento->estado,
                        'status' => $evento->status,
                        'vagas' => $evento->vagas,
                        'vagas_ocupadas' => $evento->vagas_ocupadas
                    ],
                    'inscricoes' => $inscricoes,
                    'presencas' => $presencas
                ];
            }

            return response()->json([
                'success' => true,
                'data' => $dadosOffline,
                'timestamp' => now()->toISOString()
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'error' => 'Erro ao carregar dados offline: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Sincronizar presenças marcadas offline
     */
    public function sincronizarPresencas(Request $request): JsonResponse
    {
        try {
            $presencas = $request->input('presencas', []);
            $resultados = [];

            foreach ($presencas as $presencaData) {
                try {
                    // Verificar se a inscrição existe
                    $inscricao = Inscricao::find($presencaData['inscricao_id']);
                    
                    if (!$inscricao) {
                        $resultados[] = [
                            'inscricao_id' => $presencaData['inscricao_id'],
                            'sucesso' => false,
                            'erro' => 'Inscrição não encontrada'
                        ];
                        continue;
                    }

                    // Verificar se já existe presença para esta inscrição
                    $presencaExistente = Presenca::where('inscricao_id', $presencaData['inscricao_id'])->first();

                    if ($presencaExistente) {
                        // Atualizar presença existente
                        $presencaExistente->update([
                            'data_checkin' => $presencaData['data_checkin'] ?? now(),
                            'data_checkout' => $presencaData['data_checkout'] ?? null,
                            'tipo_marcacao' => $presencaData['tipo_marcacao'] ?? 'manual',
                            'observacoes' => $presencaData['observacoes'] ?? null
                        ]);

                        $presenca = $presencaExistente;
                    } else {
                        // Criar nova presença
                        $presenca = Presenca::create([
                            'inscricao_id' => $presencaData['inscricao_id'],
                            'evento_id' => $inscricao->evento_id,
                            'usuario_id' => $inscricao->usuario_id,
                            'data_checkin' => $presencaData['data_checkin'] ?? now(),
                            'data_checkout' => $presencaData['data_checkout'] ?? null,
                            'tipo_marcacao' => $presencaData['tipo_marcacao'] ?? 'manual',
                            'observacoes' => $presencaData['observacoes'] ?? null
                        ]);
                    }

                    // Atualizar status da inscrição
                    $inscricao->update([
                        'presente' => true,
                        'data_presenca' => $presencaData['data_checkin'] ?? now()
                    ]);

                    $resultados[] = [
                        'inscricao_id' => $presencaData['inscricao_id'],
                        'presenca_id' => $presenca->id,
                        'sucesso' => true,
                        'acao' => $presencaExistente ? 'atualizada' : 'criada'
                    ];

                } catch (\Exception $e) {
                    $resultados[] = [
                        'inscricao_id' => $presencaData['inscricao_id'] ?? null,
                        'sucesso' => false,
                        'erro' => $e->getMessage()
                    ];
                }
            }

            $sucessos = collect($resultados)->where('sucesso', true)->count();
            $erros = collect($resultados)->where('sucesso', false)->count();

            return response()->json([
                'success' => true,
                'message' => "Sincronização concluída: {$sucessos} sucessos, {$erros} erros",
                'resultados' => $resultados,
                'timestamp' => now()->toISOString()
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'error' => 'Erro na sincronização: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Verificar status de conectividade
     */
    public function statusConectividade(): JsonResponse
    {
        return response()->json([
            'success' => true,
            'online' => true,
            'timestamp' => now()->toISOString()
        ]);
    }
}