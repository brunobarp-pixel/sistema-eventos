# Implementação do Sistema Offline - Documentação Completa

## 📋 Visão Geral

O sistema offline foi implementado com dois componentes principais:

1. **OfflineManager** (`frontend/js/offline-manager.js`) - Gerenciador de dados offline
2. **Página Offline** (`frontend/offline.html`) - Interface do sistema offline

## 🎯 Funcionalidades Implementadas

### ✅ Carregamento de Dados
- Ao acessar a página offline, todos os dados são carregados do servidor e armazenados no **localStorage**
- Dados armazenados:
  - Usuários
  - Eventos
  - Inscrições
  - Presenças
  - Fila de sincronização

### ✅ Modo Offline
- Usuário pode registrar presenças sem conexão com a internet
- As presenças ficam armazenadas localmente
- Sistema detecta automaticamente se há conexão

### ✅ Busca de Participantes
- Busca em tempo real por nome, email ou CPF
- Filtra por evento selecionado
- Indica visualmente quem já tem presença registrada

### ✅ Registro de Presença
- Marca presença com um clique
- Armazena localmente se offline
- Sincroniza automaticamente se online

### ✅ Sincronização
- Botão "Sincronizar" para enviar dados para o servidor
- Fila de sincronização gerencia itens pendentes
- Sincronização automática quando conexão é restaurada
- Mostra feedback de sucesso/erro

## 🛠️ Configuração

### 1. Incluir Scripts na Página

O arquivo `offline.html` já possui as inclusões necessárias:

```html
<script src="js/offline-manager.js"></script>
```

### 2. Configurar URL da API

No topo do script em `offline.html`:

```javascript
const API_BASE_URL = 'http://localhost:8000/api'; // Altere conforme seu backend
```

### 3. Token de Autenticação

O sistema usa o token armazenado em `localStorage.authToken`. Certifique-se de que:
- O usuário fez login antes de acessar a página offline
- O token está armazenado no localStorage

## 📊 Estrutura de Dados

### OfflineManager

```javascript
{
    usuarios: [],           // Lista de usuários
    eventos: [],            // Lista de eventos
    inscricoes: [],         // Inscrições ativas
    presencas: [],          // Presenças registradas
    filaSincronizacao: []   // Itens pendentes de sincronização
}
```

### Item de Presença

```javascript
{
    id: "temp_1234567890",
    inscricao_id: 5,
    evento_id: 2,
    data_presenca: "2025-11-29T10:30:00.000Z",
    sincronizado: false,
    status: "pendente"
}
```

### Item na Fila de Sincronização

```javascript
{
    tipo: "presenca",
    acao: "criar",
    dados: { /* presença */ },
    timestamp: 1701265800000
}
```

## 🔌 Endpoints Necessários

O backend já possui todos os endpoints necessários em `backend/routes/api.php`:

### Públicos
- `GET /api/status` - Verificar conexão
- `GET /api/eventos` - Listar eventos
- `POST /api/usuarios` - Criar usuário

### Protegidos (com autenticação)
- `GET /api/usuarios` - Listar usuários
- `GET /api/inscricoes` - Listar inscrições
- `POST /api/inscricoes` - Criar inscrição
- `POST /api/presencas` - Registrar presença

## 🚀 Como Usar

### Para o Atendente

1. **Acesse a página**: Vá para `offline.html`
2. **Carregue os dados**: A página carrega automaticamente ao abrir
3. **Escolha o evento**: Selecione um evento na lista
4. **Busque o participante**: Digite nome, email ou CPF
5. **Registre presença**: Clique no participante e confirme
6. **Sincronize**: Quando online, clique em "Sincronizar"

### Para o Desenvolvedor

#### Carregar dados
```javascript
await offlineManager.carregarTodosDados();
```

#### Registrar presença
```javascript
await offlineManager.registrarPresenca(inscricaoId, eventoId);
```

#### Sincronizar
```javascript
await offlineManager.sincronizarTodos();
```

#### Obter estatísticas
```javascript
const stats = offlineManager.obterEstatisticas();
console.log(stats.totalPresencas); // Número de presenças registradas
console.log(stats.totalPendentes); // Itens aguardando sincronização
```

## 💾 LocalStorage

As chaves usadas no localStorage são:

```javascript
{
    'sistema_eventos_usuarios': [],
    'sistema_eventos_eventos': [],
    'sistema_eventos_inscricoes': [],
    'sistema_eventos_presencas': [],
    'sistema_eventos_fila_sync': [],
    'sistema_eventos_ultima_sync': '2025-11-29T10:30:00.000Z',
    'authToken': 'token_aqui'
}
```

## 🔄 Fluxo de Sincronização

```
Usuário registra presença (Offline)
        ↓
Presença armazenada localmente
        ↓
Adicionada à fila de sincronização
        ↓
Salva no localStorage
        ↓
[Conexão restaurada]
        ↓
Usuário clica em "Sincronizar"
        ↓
Sistema envia presença para servidor
        ↓
Servidor confirma
        ↓
Presença marcada como sincronizada
        ↓
Removida da fila
        ↓
Dados recarregados do servidor
```

## ⚡ Detecção de Conexão

O sistema verifica automaticamente a conexão:
- A cada 5 segundos
- Ao carregar dados
- Antes de sincronizar

Você pode forçar uma verificação:
```javascript
await offlineManager.verificarConexao();
```

## 🎨 Interface

A interface mostra:

- **Status Bar**: Indica se está ONLINE ou OFFLINE
- **Estatísticas**: Total de usuários, inscrições, presenças e pendentes
- **3 Abas**:
  - **Check-in**: Registrar presença
  - **Cadastro Rápido**: Cadastrar novo participante
  - **Inscrição**: Inscrever participante em evento

## 🔐 Autenticação

O token deve estar no localStorage antes de acessar a página:

```javascript
localStorage.setItem('authToken', 'token_do_usuario');
```

Se não houver token válido, o usuário será redirecionado para login.

## ⚠️ Limitações e Considerações

1. **Tamanho do localStorage**: Limitado a ~5-10MB por domínio
   - Com muitos usuários/inscrições, considere paginação

2. **Privacidade**: Dados sensíveis são armazenados no cliente
   - Use HTTPS em produção
   - Considere criptografia para dados sensíveis

3. **Sincronização de Conflitos**: 
   - Sistema assume última atualização como válida
   - Personalize conforme necessário

4. **Browser Compatibility**:
   - localStorage funciona em todos os browsers modernos
   - Falha gracefully se localStorage não estiver disponível

## 🐛 Debugging

### Ver dados no localStorage
```javascript
console.log(JSON.parse(localStorage.getItem('sistema_eventos_presencas')));
```

### Ver fila de sincronização
```javascript
console.log(offlineManager.dados.filaSincronizacao);
```

### Limpar dados (para teste)
```javascript
offlineManager.limparTodosDados();
```

### Ver logs
Abra o console (F12) para ver os logs de debug com prefixo `[OfflineManager]`

## 📱 Responsividade

A interface é responsiva e funciona bem em:
- Desktop
- Tablet
- Celular

## 🔄 Próximos Passos Recomendados

1. **Testar em produção**: Confirme URLs da API
2. **Capacitação**: Treine atendentes sobre o sistema
3. **Monitoramento**: Implemente logs de sincronização
4. **Backup**: Considere exportar dados periodicamente
5. **Cache**: Implemente atualização automática de dados

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique o console (F12) para mensagens de erro
2. Verifique a conexão de internet
3. Limpe o cache do navegador se necessário
4. Recarregue a página

---

**Última atualização**: 29 de Novembro de 2025
**Versão**: 1.0.0
