# Arquivo: testar_emails.py

from email_service import (
    enviar_email_inscricao,
    enviar_email_certificado,
    enviar_email_cancelamento,
    enviar_email_checkin
)

print("=== Testes de Envio de E-mail (MODO_TESTE) ===\n")

usuario_teste = {
    "nome": "Usuário de Teste",
    "email": "teste@example.com"
}

evento_teste = {
    "titulo": "Evento de Demonstração",
    "data_inicio": "2025-12-01 14:00",
    "local": "Auditório Central"
}



print("\n🔹 Testando e-mail de INSCRIÇÃO...")
resultado = enviar_email_inscricao(usuario_teste, evento_teste)
print("Resultado:", resultado)

print("\n🔹 Testando e-mail de CANCELAMENTO...")
resultado = enviar_email_cancelamento(usuario_teste, evento_teste)
print("Resultado:", resultado)

print("\n🔹 Testando e-mail de CHECK-IN...")
resultado = enviar_email_checkin(usuario_teste, evento_teste)
print("Resultado:", resultado)

print("\n=== TESTES FINALIZADOS ===")
print("Verifique os HTMLs gerados na pasta 'emails_enviados/'.")
