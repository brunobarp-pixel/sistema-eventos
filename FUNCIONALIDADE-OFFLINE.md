# Sistema de Eventos - Funcionalidade Offline

Este documento descreve como usar a nova funcionalidade offline do sistema de eventos.

## ✨ Funcionalidades Implementadas

### 🔧 Backend Offline (Novo Microserviço)
- **Tecnologia**: Laravel 12.0 (mesma versão do backend principal)
- **Porta**: 8081
- **Banco de Dados**: Compartilha o mesmo banco do sistema principal
- **Funcionalidade**: API especializada para carregamento e sincronização de dados offline

### 📱 Frontend Atualizado
- **Página**: `http://177.44.248.118/offline.html`
- **Integração**: Conecta automaticamente com o backend-offline
- **Cache**: Armazena dados no localStorage para funcionamento offline

## 🚀 Como Usar

### 1. Acesso Inicial (COM Internet)
1. Acesse `http://177.44.248.118/offline.html`
2. Faça login com suas credenciais
3. O sistema automaticamente carrega:
   - Eventos com status: 'aberto', 'planejamento', 'em_andamento'
   - Todas as inscrições desses eventos
   - Todas as presenças registradas
   - Dados dos usuários inscritos

### 2. Funcionamento Offline (SEM Internet)
1. Desconecte a internet
2. A interface mostra status "OFFLINE" (barra vermelha)
3. Você pode:
   - Buscar participantes pelos dados em cache
   - Marcar presenças
   - Ver estatísticas dos dados carregados
4. As presenças ficam armazenadas localmente

### 3. Sincronização (COM Internet)
1. Reconecte à internet
2. A interface mostra status "ONLINE" (barra verde)
3. Clique no botão "Sincronizar"
4. Todas as presenças marcadas offline são enviadas ao servidor
5. Sistema confirma quantas foram sincronizadas com sucesso

## 🔄 Fluxo Técnico

### Endpoints do Backend-Offline

#### Carregar Dados
```http
GET /api/offline/dados
```
- Retorna eventos ativos com inscrições e presenças
- Dados são estruturados para fácil cache no frontend

#### Sincronizar Presenças
```http
POST /api/offline/sincronizar-presencas
```
- Recebe array de presenças marcadas offline
- Processa cada presença individualmente
- Retorna resultado detalhado da sincronização

#### Verificar Status
```http
GET /api/offline/status
```
- Health check do serviço
- Usado pelo frontend para detectar conectividade

### Armazenamento Local (Frontend)
- **Eventos**: `localStorage.eventos_cache`
- **Usuários**: `localStorage.offline_usuarios`
- **Inscrições**: `localStorage.offline_inscricoes`
- **Presenças**: `localStorage.offline_presencas`
- **Fila Sync**: `localStorage.presencas_offline`

## 🛠️ Instalação e Configuração

### Via Docker
```bash
# Subir todos os serviços incluindo backend-offline
docker-compose up -d

# Verificar se backend-offline está rodando
curl http://localhost:8081/api/health

# Ver logs do backend-offline
docker logs sistema-eventos-offline
```

Tudo é configurado automaticamente via Docker - não precisa de setup manual.

## 📊 Monitoramento

### Logs do Backend-Offline
```bash
# Via Docker
docker logs sistema-eventos-offline

# Manual
tail -f backend-offline/storage/logs/laravel.log
```

### Verificação de Status
```bash
# Health check
curl http://localhost:8081/api/health

# Status da funcionalidade offline
curl http://localhost:8081/api/offline/status

# Dados disponíveis
curl http://localhost:8081/api/offline/dados
```

## 🔒 Segurança

### CORS
- Configurado para aceitar todas as origens durante desenvolvimento
- Em produção, configure origins específicas em `config/cors.php`

### Autenticação
- Não requer autenticação para endpoints offline
- Usa o mesmo banco de dados do sistema principal
- Validações de integridade nas operações de escrita

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Backend-offline não inicia
```bash
# Verificar status do container
docker ps | grep backend-offline

# Ver logs do container
docker logs sistema-eventos-offline

# Reiniciar serviço
docker-compose restart backend-offline
```

#### 2. Dados não carregam
```bash
# Verificar conexão com banco via container
docker exec sistema-eventos-offline php artisan tinker
>>> \DB::connection()->getPdo()
```

#### 3. CORS errors no frontend
```bash
# Verificar middleware CORS
# Arquivo: backend-offline/app/Http/Middleware/CorsMiddleware.php
```

#### 4. Sincronização falha
- Verificar se backend-offline está rodando na porta 8081
- Verificar logs em `storage/logs/laravel.log`
- Testar endpoint manualmente: `curl -X POST http://localhost:8081/api/offline/sincronizar-presencas`

### URLs de Teste
- **Backend Principal**: http://localhost:8000/api/health
- **Backend Offline**: http://localhost:8081/api/health
- **Frontend**: http://localhost:3000/offline.html
- **Python API**: http://localhost:5000/status

## 📈 Próximos Passos

### Melhorias Sugeridas
1. **Autenticação**: Implementar tokens JWT para segurança
2. **Compressão**: Otimizar tamanho dos dados carregados
3. **Cache Inteligente**: Carregar apenas dados modificados
4. **Validações**: Verificar integridade dos dados antes da sincronização
5. **Retry Logic**: Tentar novamente sincronizações que falharam

### Monitoramento em Produção
1. **Logs Estruturados**: Implementar logging detalhado
2. **Métricas**: Quantidade de dados sincronizados, falhas, etc.
3. **Alertas**: Notificações quando sincronização falha frequentemente