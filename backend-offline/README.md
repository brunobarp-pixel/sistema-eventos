# Backend Offline - Sistema de Eventos

Microserviço Laravel para funcionalidade offline do sistema de eventos.

## Configuração

### Configuração via Docker (Recomendado)

O backend-offline é executado automaticamente via Docker Compose junto com os outros serviços:

```bash
# Subir todos os serviços
docker-compose up -d

# Ou apenas o backend-offline
docker-compose up backend-offline
```

**Configuração Automática**: 
- Dependências instaladas automaticamente
- Arquivo .env configurado automaticamente
- Chave da aplicação gerada automaticamente
- Conecta no mesmo banco de dados dos outros serviços

## Endpoints da API

### Base URL: `http://localhost:8081/api`

#### 1. Carregar Dados para Offline
```http
GET /offline/dados
```

Retorna todos os eventos com status 'aberto', 'planejamento' ou 'em_andamento', incluindo suas inscrições e presenças.

**Resposta:**
```json
{
  "success": true,
  "data": [
    {
      "evento": {
        "id": 1,
        "nome": "Evento Teste",
        "status": "aberto",
        ...
      },
      "inscricoes": [...],
      "presencas": [...]
    }
  ],
  "timestamp": "2025-12-03T20:00:00.000Z"
}
```

#### 2. Sincronizar Presenças
```http
POST /offline/sincronizar-presencas
```

**Payload:**
```json
{
  "presencas": [
    {
      "inscricao_id": 1,
      "evento_id": 1,
      "usuario_id": 1,
      "data_checkin": "2025-12-03T20:00:00.000Z",
      "tipo_marcacao": "manual",
      "observacoes": null
    }
  ]
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Sincronização concluída: 1 sucessos, 0 erros",
  "resultados": [
    {
      "inscricao_id": 1,
      "presenca_id": 5,
      "sucesso": true,
      "acao": "criada"
    }
  ],
  "timestamp": "2025-12-03T20:00:00.000Z"
}
```

#### 3. Verificar Status
```http
GET /offline/status
```

**Resposta:**
```json
{
  "success": true,
  "online": true,
  "timestamp": "2025-12-03T20:00:00.000Z"
}
```

#### 4. Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "ok",
  "service": "backend-offline",
  "timestamp": "2025-12-03T20:00:00.000Z"
}
```

## Fluxo de Funcionamento

### 1. Carregamento Inicial (Online)
- Usuário acessa `http://177.44.248.118/offline.html`
- Frontend faz chamada para `/api/offline/dados`
- Dados são salvos no localStorage do navegador
- Eventos com status 'aberto', 'planejamento' ou 'em_andamento' são carregados
- Inscrições e presenças relacionadas são incluídas

### 2. Funcionamento Offline
- Usuário desconecta da internet
- Frontend continua funcionando com dados do localStorage
- Presenças marcadas são armazenadas localmente
- Interface indica status offline

### 3. Sincronização (Online)
- Usuário conecta novamente à internet
- Clica no botão "Sincronizar"
- Frontend envia todas as presenças pendentes para `/api/offline/sincronizar-presencas`
- Backend processa e salva no banco de dados
- Frontend recebe confirmação da sincronização

## Verificação do Serviço

```bash
# Verificar se está rodando
curl http://localhost:8081/api/health

# Ver logs
docker logs sistema-eventos-offline
```

## Desenvolvimento

### Estrutura de Arquivos
```
backend-offline/
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   └── OfflineController.php
│   │   └── Middleware/
│   │       └── CorsMiddleware.php
│   └── Models/
│       ├── Evento.php
│       ├── Inscricao.php
│       ├── Presenca.php
│       └── Usuario.php
├── config/
├── routes/
│   └── api.php
├── .env.example
├── composer.json
├── Dockerfile
└── start.sh
```

### Logs
Os logs são gerados automaticamente pelo Laravel e podem ser encontrados em `storage/logs/`

### Troubleshooting

1. **Erro de conexão com banco**: Verifique as configurações no `.env`
2. **CORS errors**: O middleware está configurado para aceitar todas as origens
3. **Porta ocupada**: Altere a porta no comando de execução
4. **Dados não carregando**: Verifique se o banco possui dados dos eventos