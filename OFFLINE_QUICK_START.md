# 🚀 Sistema Offline - Guia Rápido

## 📝 O que foi implementado?

Um sistema completo de presença offline que permite registrar presenças mesmo sem internet, com sincronização automática quando a conexão for restaurada.

## 📁 Arquivos Criados/Modificados

### Novos arquivos:
1. **`frontend/js/offline-manager.js`** - Gerenciador offline (classe principal)
2. **`frontend/offline.html`** - Interface offline melhorada
3. **`frontend/offline-test.html`** - Painel de testes
4. **`frontend/js/offline-examples.js`** - Exemplos de uso
5. **`OFFLINE_IMPLEMENTATION.md`** - Documentação técnica completa

## 🎯 Funcionalidades Principais

### ✅ Automático
- Detecção automática de conexão (a cada 5 segundos)
- Sincronização automática quando online
- Armazenamento automático em localStorage

### ✅ Presença
- Registrar presença offline
- Busca por nome, email ou CPF
- Indicação visual de quem já tem presença

### ✅ Dados
- Carregamento de eventos, usuários, inscrições
- Armazenamento em localStorage
- Fila de sincronização

### ✅ Sincronização
- Botão para sincronizar manualmente
- Sincronização automática ao detectar conexão
- Feedback de sucesso/erro

## 🚀 Como Usar

### 1. Acessar o Sistema
```
http://seu-dominio/frontend/offline.html
```

### 2. Fluxo de Uso
1. **Página carrega** → Dados são baixados do servidor
2. **Selecione evento** → Filtra participantes
3. **Busque participante** → Por nome/email/CPF
4. **Registre presença** → Funciona offline
5. **Sincronize** → Quando online

### 3. Configuração

Edite em `offline.html`:
```javascript
const API_BASE_URL = 'http://localhost:8000/api'; // Sua API
```

## 🧪 Testar

### Painel de Testes
```
http://seu-dominio/frontend/offline-test.html
```

### Via Console
```javascript
// Inicializar
const manager = new OfflineManager({
    apiBase: 'http://localhost:8000/api'
});

// Carregar dados
await manager.carregarTodosDados();

// Registrar presença
await manager.registrarPresenca(5, 1);

// Ver estatísticas
console.log(manager.obterEstatisticas());

// Sincronizar
await manager.sincronizarTodos();
```

## 📊 Estrutura de Dados

Dados armazenados no localStorage:
```javascript
{
    'sistema_eventos_usuarios': [],      // Usuários
    'sistema_eventos_eventos': [],       // Eventos
    'sistema_eventos_inscricoes': [],    // Inscrições
    'sistema_eventos_presencas': [],     // Presenças
    'sistema_eventos_fila_sync': [],     // Pendentes
    'authToken': 'token_aqui'            // Token
}
```

## 🔄 Fluxo de Sincronização

```
Registra presença (Offline)
         ↓
Armazena localmente
         ↓
Adiciona à fila
         ↓
Ao ficar online
         ↓
Clica sincronizar
         ↓
Envia presença para servidor
         ↓
Servidor confirma
         ↓
Remove da fila
```

## ⚙️ API Endpoints

O sistema usa estes endpoints do Laravel:

```
GET  /api/status             - Verificar conexão
GET  /api/usuarios           - Listar usuários
GET  /api/eventos            - Listar eventos
GET  /api/inscricoes         - Listar inscrições
POST /api/inscricoes         - Criar inscrição
POST /api/presencas          - Registrar presença
```

## 🔐 Requisitos

1. **Token de autenticação** em `localStorage.authToken`
2. **Backend Laravel** rodando em `http://localhost:8000`
3. **Navegador moderno** com suporte a localStorage

## 📱 Interface

### 3 Abas Principais

1. **Check-in**
   - Buscar participante
   - Registrar presença

2. **Cadastro Rápido**
   - Cadastrar novo usuário
   - Apenas nome e email obrigatórios

3. **Inscrição**
   - Inscrever participante em evento
   - Depois pode fazer check-in

### Status Bar

Mostra em tempo real:
- Modo (Online/Offline)
- Botão para verificar conexão
- Botão para sincronizar

## 💾 LocalStorage

Limite recomendado: **5-10 MB**

Para ~1000 usuários e 5000 inscrições:
- Aproximadamente 2-3 MB

Você pode ver o uso:
```javascript
const tamanho = JSON.stringify(localStorage).length;
console.log(`${(tamanho / 1024).toFixed(2)} KB`);
```

## 🐛 Troubleshooting

### Problema: Dados não carregam
**Solução:**
- Verifique URL da API
- Verifique token em localStorage
- Veja o console (F12) para erros

### Problema: Sincronização falha
**Solução:**
- Verifique conexão de internet
- Verifique token ainda é válido
- Aguarde 5 segundos para reconexão

### Problema: LocalStorage cheio
**Solução:**
- Limpe dados antigos
- Implemente paginação
- Use compressão de dados

## 📊 Estatísticas

Comando para ver status:
```javascript
console.log(manager.obterEstatisticas());
```

Retorna:
```javascript
{
    totalUsuarios: 10,
    totalEventos: 3,
    totalInscricoes: 25,
    totalPresencas: 12,
    totalPendentes: 2,        // Aguardando sincronização
    modo: 'offline',
    ultimaSincronizacao: '2025-11-29T10:30:00.000Z'
}
```

## 🔗 Links Úteis

- **Documentação Completa**: `OFFLINE_IMPLEMENTATION.md`
- **Exemplos de Código**: `frontend/js/offline-examples.js`
- **Painel de Testes**: `frontend/offline-test.html`

## 🎓 Exemplo Completo

```javascript
// 1. Inicializar
const manager = new OfflineManager({
    apiBase: 'http://localhost:8000/api'
});

// 2. Carregar dados
await manager.carregarTodosDados();

// 3. Registrar presença
await manager.registrarPresenca(5, 1);

// 4. Quando online
await manager.sincronizarTodos();

// 5. Ver resultado
console.log(manager.obterEstatisticas());
```

## 🚀 Próximos Passos

1. ✅ Testar no navegador (offline-test.html)
2. ✅ Configurar URL da API
3. ✅ Treinar atendentes
4. ✅ Fazer backup de dados
5. ✅ Monitorar logs

## 📞 Suporte

Para problemas:
1. Abra o console (F12)
2. Procure por logs com `[OfflineManager]`
3. Verifique a conexão de internet
4. Recarregue a página

---

**Versão**: 1.0.0  
**Data**: 29 de Novembro de 2025  
**Desenvolvedor**: Sistema Automático
