<?php

namespace App\Http\Controllers;

use App\Models\Usuario;
use App\Models\Log;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Validator;

class AuthController extends Controller
{
    /**
     * GET /api/usuarios
     * Lista todos os usuários
     */
    public function index()
    {
        $usuarios = Usuario::all();
        return response()->json([
            'success' => true,
            'data' => $usuarios
        ]);
    }

    /**
     * Registrar um novo usuário
     * POST /api/usuarios
     */
    public function cadastrar(Request $request)
    {
        try {
            // Validação dos dados
            $validator = Validator::make($request->all(), [
                'nome' => 'required|string|max:255',
                'email' => 'required|email|unique:usuarios,email',
                'senha' => 'required|string|min:6',
                'cpf' => 'nullable|string|size:14|unique:usuarios,cpf',
                'telefone' => 'nullable|string|max:20'
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Erro de validação',
                    'errors' => $validator->errors()
                ], 422);
            }

            // Criar usuário
            $usuario = Usuario::create([
                'nome' => $request->nome,
                'email' => $request->email,
                'senha' => Hash::make($request->senha),
                'cpf' => $request->cpf,
                'telefone' => $request->telefone,
                'dados_completos' => !empty($request->cpf) && !empty($request->telefone)
            ]);

            // Registrar log
            $this->registrarLog($request, 'POST', '/api/usuarios', 201, $usuario->id);

            return response()->json([
                'success' => true,
                'message' => 'Usuário cadastrado com sucesso',
                'data' => [
                    'id' => $usuario->id,
                    'nome' => $usuario->nome,
                    'email' => $usuario->email,
                    'dados_completos' => $usuario->dados_completos
                ]
            ], 201);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'POST', '/api/usuarios', 500);
            return response()->json([
                'success' => false,
                'message' => 'Erro ao cadastrar usuário',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Login com Sanctum
     * POST /api/auth
     */
    public function login(Request $request)
    {
        try {
            // Validação
            $validator = Validator::make($request->all(), [
                'email' => 'required|email',
                'senha' => 'required|string'
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Dados inválidos',
                    'errors' => $validator->errors()
                ], 422);
            }

            // Buscar usuário
            $usuario = Usuario::where('email', $request->email)->first();

            // Verificar senha
            if (!$usuario || !Hash::check($request->senha, $usuario->senha)) {
                $this->registrarLog($request, 'POST', '/api/auth', 401);

                return response()->json([
                    'success' => false,
                    'message' => 'Credenciais inválidas'
                ], 401);
            }

            // ✅ GERAR TOKEN SANCTUM
            $token = $usuario->createToken('api-token')->plainTextToken;

            $this->registrarLog($request, 'POST', '/api/auth', 200, $usuario->id);

            return response()->json([
                'success' => true,
                'message' => 'Login realizado com sucesso',
                'data' => [
                    'usuario' => [
                        'id' => $usuario->id,
                        'nome' => $usuario->nome,
                        'email' => $usuario->email,
                        'dados_completos' => $usuario->dados_completos
                    ],
                    'token' => $token
                ]
            ], 200);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'POST', '/api/auth', 500);

            return response()->json([
                'success' => false,
                'message' => 'Erro ao realizar login',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * ✅ NOVO: Logout (revoga token)
     * POST /api/logout
     */
    public function logout(Request $request)
    {
        try {
            // Revogar token atual
            $request->user()->currentAccessToken()->delete();

            $this->registrarLog($request, 'POST', '/api/logout', 200, $request->user()->id);

            return response()->json([
                'success' => true,
                'message' => 'Logout realizado com sucesso'
            ], 200);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Erro ao realizar logout'
            ], 500);
        }
    }

    /**
     * ✅ NOVO: Obter usuário autenticado
     * GET /api/me
     */
    public function me(Request $request)
    {
        return response()->json([
            'success' => true,
            'data' => [
                'id' => $request->user()->id,
                'nome' => $request->user()->nome,
                'email' => $request->user()->email,
                'cpf' => $request->user()->cpf,
                'telefone' => $request->user()->telefone,
                'dados_completos' => $request->user()->dados_completos
            ]
        ]);
    }

    /**
     * Completar dados do usuário
     * PUT /api/usuarios/{id}
     */
    public function completarDados(Request $request, $id)
    {
        try {
            $usuario = Usuario::findOrFail($id);

            // Validação
            $validator = Validator::make($request->all(), [
                'nome' => 'sometimes|string|max:255',
                'cpf' => 'sometimes|string|size:14|unique:usuarios,cpf,' . $id,
                'telefone' => 'sometimes|string|max:20'
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Erro de validação',
                    'errors' => $validator->errors()
                ], 422);
            }

            // Atualizar dados
            if ($request->has('nome')) $usuario->nome = $request->nome;
            if ($request->has('cpf')) $usuario->cpf = $request->cpf;
            if ($request->has('telefone')) $usuario->telefone = $request->telefone;

            // Verificar se dados estão completos
            $usuario->dados_completos = $usuario->verificarDadosCompletos();
            $usuario->save();

            $this->registrarLog($request, 'PUT', '/api/usuarios/' . $id, 200, $usuario->id);

            return response()->json([
                'success' => true,
                'message' => 'Dados atualizados com sucesso',
                'data' => [
                    'id' => $usuario->id,
                    'nome' => $usuario->nome,
                    'email' => $usuario->email,
                    'cpf' => $usuario->cpf,
                    'telefone' => $usuario->telefone,
                    'dados_completos' => $usuario->dados_completos
                ]
            ], 200);
        } catch (\Exception $e) {
            $this->registrarLog($request, 'PUT', '/api/usuarios/' . $id, 500);

            return response()->json([
                'success' => false,
                'message' => 'Erro ao atualizar dados',
                'error' => $e->getMessage()
            ], 500);
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
                'request_body' => json_encode($request->except(['senha', 'password'])),
                'response_status' => $status
            ]);
        } catch (\Exception $e) {
            // Silenciar erro de log para não afetar a requisição principal
        }
    }
}