<?php

namespace App\Services;

use App\Models\Usuario;
use App\Models\Evento;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

//Bridge/Ponte entre Controllers e Python, responsa pelas tratativas 

class EmailService
{
    private $pythonApiUrl = 'http://sistema-eventos-python:5000';

    /**
     * Envia e-mail de inscrição
     */
    public function enviarEmailInscricao(Usuario $usuario, Evento $evento)
    {
        try {
            $response = Http::timeout(5)->post($this->pythonApiUrl . '/enviar-email-inscricao', [
                'usuario' => [
                    'nome' => $usuario->nome,
                    'email' => $usuario->email
                ],
                'evento' => [
                    'titulo' => $evento->nome,
                    'data_inicio' => $evento->data_inicio ? $evento->data_inicio->format('d/m/Y H:i') : null,
                    'local' => $evento->local
                ]
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            Log::error('Erro ao enviar e-mail de inscrição: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Envia e-mail de cancelamento
     */
    public function enviarEmailCancelamento(Usuario $usuario, Evento $evento)
    {
        try {
            $response = Http::timeout(5)->post($this->pythonApiUrl . '/enviar-email-cancelamento', [
                'usuario' => [
                    'nome' => $usuario->nome,
                    'email' => $usuario->email
                ],
                'evento' => [
                    'titulo' => $evento->nome,
                    'data_inicio' => $evento->data_inicio ? $evento->data_inicio->format('d/m/Y H:i') : null,
                    'local' => $evento->local
                ]
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            Log::error('Erro ao enviar e-mail de cancelamento: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Envia e-mail de check-in
     */
    public function enviarEmailCheckin(Usuario $usuario, Evento $evento)
    {
        try {
            Log::info('EmailService: Preparando email de check-in', [
                'usuario_email' => $usuario->email,
                'evento_nome' => $evento->nome,
                'python_api_url' => $this->pythonApiUrl
            ]);
            
            $payload = [
                'usuario' => [
                    'nome' => $usuario->nome,
                    'email' => $usuario->email
                ],
                'evento' => [
                    'titulo' => $evento->nome,
                    'data_inicio' => $evento->data_inicio ? $evento->data_inicio->format('d/m/Y H:i') : null,
                    'local' => $evento->local
                ]
            ];
            
            Log::info('EmailService: Payload preparado', ['payload' => $payload]);
            
            $response = Http::timeout(5)->post($this->pythonApiUrl . '/enviar-email-checkin', $payload);
            
            Log::info('EmailService: Resposta do backend-python', [
                'status' => $response->status(),
                'successful' => $response->successful(),
                'body' => $response->body()
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            Log::error('EmailService: Erro ao enviar e-mail de check-in', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            return false;
        }
    }

    public function enviarEmailCertificado($usuario, $evento, $certificado)
    {
        try {
            $response = Http::timeout(5)->post($this->pythonApiUrl . '/enviar-email-certificado', [
                'usuario' => [
                    'nome' => $usuario->nome,
                    'email' => $usuario->email
                ],
                'evento' => [
                    'titulo' => $evento->nome,
                    'data_inicio' => $evento->data_inicio ? $evento->data_inicio->format('d/m/Y') : null,
                    'data_fim' => $evento->data_fim ? $evento->data_fim->format('d/m/Y') : null,
                    'local' => $evento->local
                ],
                'certificado' => $certificado
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            Log::error('Erro ao enviar e-mail do certificado: ' . $e->getMessage());
            return false;
        }
    }
}
