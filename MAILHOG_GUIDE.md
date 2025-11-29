# MailHog - Sistema de Teste de Emails

## O que é o MailHog?

O MailHog é um serviço para **testar envios de email durante o desenvolvimento** sem enviar emails reais. É uma "caixa postal falsa" que captura todos os emails enviados pela aplicação.

## Como Funciona?

### 1. Portas do MailHog:
- **Porta 1025**: Servidor SMTP (aplicação envia emails aqui)
- **Porta 8025**: Interface web para visualizar emails

### 2. Fluxo de Funcionamento:
```
Aplicação PHP/Laravel → Porta 1025 (SMTP) → MailHog → Porta 8025 (Web UI)
```

### 3. Acessando os Emails:
- **URL**: http://177.44.248.118:8025
- **Visualização**: Interface web simples mostrando todos os emails "enviados"

## Configuração no Sistema

### Laravel (.env):
```bash
MAIL_MAILER=smtp
MAIL_HOST=mailhog
MAIL_PORT=1025
MAIL_USERNAME=test
MAIL_PASSWORD=test
MAIL_ENCRYPTION=null
MAIL_FROM_ADDRESS=noreply@sistemaeventos.com
```

### Python (email_service.py):
```python
SMTP_SERVER = 'mailhog'
SMTP_PORT = 1025
SMTP_USER = 'test'
SMTP_PASSWORD = 'test'
```

## Quando os Emails São Enviados?

1. **Cadastro de Usuário**: Email de boas-vindas
2. **Nova Inscrição**: Confirmação de inscrição
3. **Cancelamento**: Confirmação de cancelamento
4. **Certificado**: Email com link/anexo do certificado
5. **Presença Registrada**: Notificação de presença confirmada

## Como Testar?

### 1. Fazer alguma ação que gere email:
- Cadastrar usuário
- Se inscrever em evento
- Marcar presença
- Gerar certificado

### 2. Verificar no MailHog:
- Abrir: http://177.44.248.118:8025
- Ver lista de emails na interface
- Clicar no email para ver conteúdo completo
- Ver HTML, texto e anexos

## Vantagens do MailHog:

✅ **Seguro**: Não envia emails reais
✅ **Rápido**: Não depende de SMTP externo  
✅ **Visual**: Interface web clara
✅ **Completo**: Mostra HTML, texto e anexos
✅ **Desenvolvimento**: Perfeito para testes

## Interface Web:

A interface mostra:
- **Lista de emails**: Todos os enviados
- **Detalhes**: Remetente, destinatário, assunto, data
- **Conteúdo**: HTML renderizado e código fonte
- **Anexos**: Downloads disponíveis
- **Headers**: Informações técnicas completas

## Exemplo de Uso:

1. Usuário se cadastra no sistema
2. Sistema "envia" email de boas-vindas
3. Email vai para MailHog (não sai do servidor)
4. Desenvolvedor acessa http://177.44.248.118:8025
5. Vê o email como se fosse enviado de verdade
6. Pode testar links, layout, conteúdo

**Resultado**: Email testado sem spam ou problemas reais!