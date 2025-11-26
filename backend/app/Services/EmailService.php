<?php

namespace App\Services;

use App\Models\Usuario;
use App\Models\Evento;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class EmailService
{
    private $pythonApiUrl = 'http://127.0.0.1:5000';

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
                    'titulo' => $evento->titulo,
                    'data_inicio' => $evento->data_inicio->format('d/m/Y H:i'),
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
                    'titulo' => $evento->titulo,
                    'data_inicio' => $evento->data_inicio->format('d/m/Y H:i'),
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
            $response = Http::timeout(5)->post($this->pythonApiUrl . '/enviar-email-checkin', [
                'usuario' => [
                    'nome' => $usuario->nome,
                    'email' => $usuario->email
                ],
                'evento' => [
                    'titulo' => $evento->titulo,
                    'data_inicio' => $evento->data_inicio->format('d/m/Y H:i'),
                    'local' => $evento->local
                ]
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            Log::error('Erro ao enviar e-mail de check-in: ' . $e->getMessage());
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
                    'titulo' => $evento->titulo,
                    'data_inicio' => $evento->data_inicio->format('d/m/Y'),
                    'data_fim' => $evento->data_fim->format('d/m/Y'),
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
