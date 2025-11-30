<?php

namespace App\Http\Controllers;

use App\Models\Certificado;
use App\Models\Inscricao;
use App\Models\Usuario;
use App\Models\Evento;
use App\Models\Log;
use App\Services\EmailService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Http;

class CertificadoController extends Controller
{
    /**
     * ✅ NOVO: Gerar e baixar certificado em PDF
     * GET /api/certificados/{id}/pdf
     */
    public function gerarPDF(Request $request, $id)
    {
        try {
            $certificado = Certificado::with('usuario', 'evento')->findOrFail($id);

            // Preparar dados para o gerador de PDF (Python)
            $dadosPDF = [
                'nome_participante' => $certificado->usuario->nome,
                'evento_titulo' => $certificado->evento->titulo,
                'evento_descricao' => $certificado->evento->descricao,
                'data_inicio' => $certificado->evento->data_inicio ? $certificado->evento->data_inicio->format('Y-m-d') : null,
                'data_fim' => $certificado->evento->data_fim ? $certificado->evento->data_fim->format('Y-m-d') : null,
                'local' => $certificado->evento->local,
                'carga_horaria' => $certificado->evento->carga_horaria ?? null,
                'codigo_validacao' => $certificado->codigo_validacao,
                'data_emissao' => $certificado->data_emissao ? $certificado->data_emissao->format('Y-m-d H:i:s') : null
            ];

            // Chamar API Python para gerar PDF
            try {
                $response = Http::timeout(30)->post('http://127.0.0.1:5000/gerar-certificado-pdf', $dadosPDF);

                if ($response->successful()) {
                    $data = $response->json();
                    
                    if ($data['success'] && isset($data['pdf_path'])) {
                        $pdfPath = $data['pdf_path'];
                        
                        // Verificar se o arquivo existe
                        if (file_exists($pdfPath)) {
                            $this->registrarLog($request, 'GET', '/api/certificados/' . $id . '/pdf', 200, $certificado->usuario_id);
                            
                            return response()->download($pdfPath, 
                                'Certificado_' . Str::slug($certificado->evento->titulo) . '.pdf',
                                ['Content-Type' => 'application/pdf']
                            )->deleteFileAfterSend(false); // Manter o arquivo para cache
                        }
                    }
                }
            } catch (\Exception $e) {
                Log::error('Erro ao gerar PDF via Python: ' . $e->getMessage());
            }

            // Se falhar, retornar erro
            return response()->json([
                'success' => false,
                'message' => 'Erro ao gerar certificado PDF. Tente novamente mais tarde.'
            ], 500);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/certificados/' . $id . '/pdf', 404);
            
            return response()->json([
                'success' => false,
                'message' => 'Certificado não encontrado'
            ], 404);
        }
    }

    /**
     * Emitir certificado
     * POST /api/certificados
     */
    public function emitir(Request $request)
    {
        try {
            // Validação
            $validator = Validator::make($request->all(), [
                'usuario_id' => 'required|exists:usuarios,id',
                'evento_id' => 'required|exists:eventos,id'
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Dados inválidos',
                    'errors' => $validator->errors()
                ], 422);
            }

            // Verificar se o usuário participou do evento (tem inscrição e presença)
            $inscricao = Inscricao::where('usuario_id', $request->usuario_id)
                ->where('evento_id', $request->evento_id)
                ->whereIn('status', ['ativa', 'confirmada'])
                ->first();

            if (!$inscricao) {
                return response()->json([
                    'success' => false,
                    'message' => 'Usuário não está inscrito neste evento'
                ], 400);
            }

            // Verificar se existe presença registrada para esta inscrição
            $presenca = \App\Models\Presenca::where('inscricao_id', $inscricao->id)
                ->where('evento_id', $request->evento_id)
                ->where('usuario_id', $request->usuario_id)
                ->first();

            if (!$presenca) {
                return response()->json([
                    'success' => false,
                    'message' => 'É necessário ter presença registrada para emitir o certificado'
                ], 400);
            }

            // Verificar se já existe certificado
            $certificadoExistente = Certificado::where('usuario_id', $request->usuario_id)
                ->where('evento_id', $request->evento_id)
                ->first();

            if ($certificadoExistente) {
                return response()->json([
                    'success' => false,
                    'message' => 'Certificado já foi emitido para este evento',
                    'data' => [
                        'id' => $certificadoExistente->id,
                        'codigo_validacao' => $certificadoExistente->codigo_validacao,
                        'data_emissao' => $certificadoExistente->data_emissao ? $certificadoExistente->data_emissao->format('Y-m-d H:i:s') : null
                    ]
                ], 400);
            }

            // Gerar código único de validação
            $codigoValidacao = $this->gerarCodigoValidacao($request->usuario_id, $request->evento_id);

            // Criar certificado
            $certificado = Certificado::create([
                'usuario_id' => $request->usuario_id,
                'evento_id' => $request->evento_id,
                'inscricao_id' => $inscricao->id,
                'codigo_validacao' => $codigoValidacao,
                'arquivo_pdf' => null,
                'enviado_email' => false,
                'data_emissao' => now()
            ]);

            // Carregar dados
            $certificado->load('usuario', 'evento');

            // ENVIAR E-MAIL COM O CERTIFICADO
            try {
                $emailService = new EmailService();
                $emailService->enviarEmailCertificado(
                    $certificado->usuario, 
                    $certificado->evento, 
                    [
                        'codigo_validacao' => $certificado->codigo_validacao,
                        'data_emissao' => $certificado->data_emissao ? $certificado->data_emissao->format('d/m/Y H:i') : null,
                        'url_validacao' => url('/api/certificados/' . $certificado->codigo_validacao)
                    ]
                );
            } catch (\Exception $e) {
                Log::error('Erro ao enviar e-mail do certificado: ' . $e->getMessage());
            }

            $this->registrarLog($request, 'POST', '/api/certificados', 201, $request->usuario_id);

            return response()->json([
                'success' => true,
                'message' => 'Certificado emitido com sucesso! Verifique seu e-mail.',
                'data' => [
                    'id' => $certificado->id,
                    'codigo_validacao' => $certificado->codigo_validacao,
                    'data_emissao' => $certificado->data_emissao ? $certificado->data_emissao->format('Y-m-d H:i:s') : null,
                    'usuario' => [
                        'nome' => $certificado->usuario->nome,
                        'email' => $certificado->usuario->email
                    ],
                    'evento' => [
                        'titulo' => $certificado->evento->titulo,
                        'data_inicio' => $certificado->evento->data_inicio ? $certificado->evento->data_inicio->format('Y-m-d H:i:s') : null,
                        'data_fim' => $certificado->evento->data_fim ? $certificado->evento->data_fim->format('Y-m-d H:i:s') : null
                    ],
                    'url_validacao' => url('/api/certificados/' . $certificado->codigo_validacao),
                    'url_pdf' => url('/api/certificados/' . $certificado->id . '/pdf')
                ]
            ], 201);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'POST', '/api/certificados', 500);
            
            return response()->json([
                'success' => false,
                'message' => 'Erro ao emitir certificado',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Validar certificado (rota pública)
     * GET /api/certificados/{codigo}
     */
    public function validar(Request $request, $codigo)
    {
        try {
            $certificado = Certificado::where('codigo_validacao', $codigo)
                ->with('usuario', 'evento')
                ->first();

            if (!$certificado) {
                $this->registrarLog($request, 'GET', '/api/certificados/' . $codigo, 404);
                
                return response()->json([
                    'success' => false,
                    'message' => 'Certificado não encontrado',
                    'valido' => false
                ], 404);
            }

            $this->registrarLog($request, 'GET', '/api/certificados/' . $codigo, 200);

            return response()->json([
                'success' => true,
                'message' => 'Certificado válido',
                'valido' => true,
                'data' => [
                    'codigo_validacao' => $certificado->codigo_validacao,
                    'data_emissao' => $certificado->data_emissao ? $certificado->data_emissao->format('d/m/Y H:i:s') : null,
                    'participante' => [
                        'nome' => $certificado->usuario->nome,
                        'cpf' => $certificado->usuario->cpf ? substr($certificado->usuario->cpf, 0, 3) . '.***.***.***' : null
                    ],
                    'evento' => [
                        'titulo' => $certificado->evento->titulo,
                        'descricao' => $certificado->evento->descricao,
                        'data_inicio' => $certificado->evento->data_inicio ? $certificado->evento->data_inicio->format('d/m/Y') : null,
                        'data_fim' => $certificado->evento->data_fim ? $certificado->evento->data_fim->format('d/m/Y') : null,
                        'local' => $certificado->evento->local
                    ]
                ]
            ], 200);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/certificados/' . $codigo, 500);
            
            return response()->json([
                'success' => false,
                'message' => 'Erro ao validar certificado',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Listar certificados de um usuário
     * GET /api/certificados/usuario/{usuarioId}
     */
    public function listarPorUsuario(Request $request, $usuarioId)
    {
        try {
            // DEBUG: Verificar se o usuário existe
            $usuario = Usuario::find($usuarioId);
            if (!$usuario) {
                return response()->json([
                    'success' => false,
                    'message' => 'Usuário não encontrado',
                    'debug' => [
                        'usuario_id' => $usuarioId,
                        'total_usuarios' => Usuario::count(),
                        'usuarios_existentes' => Usuario::pluck('id')->toArray()
                    ]
                ], 404);
            }

            $certificados = Certificado::where('usuario_id', $usuarioId)
                ->with('evento')
                ->orderBy('data_emissao', 'desc')
                ->get();

            $this->registrarLog($request, 'GET', '/api/certificados/usuario/' . $usuarioId, 200, $usuarioId);

            return response()->json([
                'success' => true,
                'message' => 'Certificados recuperados com sucesso',
                'data' => $certificados->map(function($cert) {
                    return [
                        'id' => $cert->id,
                        'codigo_validacao' => $cert->codigo_validacao,
                        'data_emissao' => $cert->data_emissao ? $cert->data_emissao->format('Y-m-d H:i:s') : null,
                        'evento' => [
                            'id' => $cert->evento->id,
                            'titulo' => $cert->evento->nome,
                            'data_inicio' => $cert->evento->data_inicio ? $cert->evento->data_inicio->format('Y-m-d') : null,
                            'data_fim' => $cert->evento->data_fim ? $cert->evento->data_fim->format('Y-m-d') : null
                        ],
                        'url_validacao' => url('/api/certificados/' . $cert->codigo_validacao),
                        'url_pdf' => url('/api/certificados/' . $cert->id . '/pdf')
                    ];
                })
            ], 200);

        } catch (\Exception $e) {
            $this->registrarLog($request, 'GET', '/api/certificados/usuario/' . $usuarioId, 500);
            
            return response()->json([
                'success' => false,
                'message' => 'Erro interno',
                'debug' => [
                    'error' => $e->getMessage(),
                    'line' => $e->getLine(),
                    'file' => basename($e->getFile())
                ]
            ], 500);
        }
    }

    /**
     * Gerar código único de validação
     */
    private function gerarCodigoValidacao($usuarioId, $eventoId)
    {
        // Gerar hash único baseado em usuário, evento e timestamp
        $string = $usuarioId . '-' . $eventoId . '-' . now()->timestamp . '-' . Str::random(10);
        return hash('sha256', $string);
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