/**
 * Exemplo de uso do OfflineManager
 * Coloque este código no console para testar
 */

// ============================================
// 1. INICIALIZAR O GERENCIADOR
// ============================================

const manager = new OfflineManager({
    apiBase: 'http://localhost:8000/api',
    timeout: 5000,
    onStatusChange: (online) => {
        console.log(`Status: ${online ? 'ONLINE' : 'OFFLINE'}`);
    },
    onDataLoaded: (dados) => {
        console.log('Dados carregados:', dados);
    },
    onPresencaRegistrada: (presenca) => {
        console.log('Presença registrada:', presenca);
    },
    onSyncStart: () => {
        console.log('Iniciando sincronização...');
    },
    onSyncEnd: (resultado) => {
        console.log('Sincronização concluída:', resultado);
    },
    onSyncError: (erro) => {
        console.error('Erro de sincronização:', erro);
    }
});

// ============================================
// 2. CARREGAR DADOS
// ============================================

// Carregar todos os dados do servidor
(async () => {
    try {
        const dados = await manager.carregarTodosDados();
        console.log('Dados carregados com sucesso:', dados);
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
})();

// ============================================
// 3. VERIFICAR CONEXÃO
// ============================================

// Verificar se está online
(async () => {
    await manager.verificarConexao();
    console.log(`Modo: ${manager.isOnline ? 'ONLINE' : 'OFFLINE'}`);
})();

// ============================================
// 4. OBTER INFORMAÇÕES
// ============================================

// Obter estatísticas
const stats = manager.obterEstatisticas();
console.log('Estatísticas:', stats);
// Output:
// {
//   totalUsuarios: 10,
//   totalEventos: 3,
//   totalInscricoes: 25,
//   totalPresencas: 12,
//   totalPendentes: 2,
//   modo: 'offline',
//   ultimaSincronizacao: '2025-11-29T10:30:00.000Z'
// }

// Obter um usuário
const usuario = manager.obterUsuario(1);
console.log('Usuário:', usuario);

// Obter um evento
const evento = manager.obterEvento(1);
console.log('Evento:', evento);

// Obter uma inscrição
const inscricao = manager.obterInscricao(1);
console.log('Inscrição:', inscricao);

// Obter inscrições de um evento
const inscricoesPorEvento = manager.obterInscricoesPorEvento(1, true);
console.log('Inscrições do evento 1:', inscricoesPorEvento);

// Verificar se tem presença para uma inscrição
const temPresenca = manager.temPresenca(1);
console.log('Tem presença:', temPresenca);

// Contar presenças de um evento
const totalPresencas = manager.contarPresencasPorEvento(1);
console.log('Presenças do evento 1:', totalPresencas);

// ============================================
// 5. REGISTRAR PRESENÇA (OFFLINE)
// ============================================

// Registrar presença (funciona offline)
(async () => {
    try {
        const presenca = await manager.registrarPresenca(5, 1);
        console.log('Presença registrada:', presenca);
    } catch (error) {
        console.error('Erro ao registrar presença:', error);
    }
})();

// ============================================
// 6. SINCRONIZAR DADOS
// ============================================

// Sincronizar (apenas quando online)
(async () => {
    try {
        if (!manager.isOnline) {
            console.log('Sistema offline - não é possível sincronizar');
            return;
        }

        const resultado = await manager.sincronizarTodos();
        console.log('Sincronização concluída:', resultado);
        // Output:
        // {
        //   totalSincronizados: 2,
        //   erros: []
        // }
    } catch (error) {
        console.error('Erro ao sincronizar:', error);
    }
})();

// ============================================
// 7. MANIPULAR DADOS LOCAIS
// ============================================

// Salvar dados no localStorage
manager.salvarDadosNoStorage();
console.log('Dados salvos no localStorage');

// Carregar dados do localStorage
manager.carregarDadosDoStorage();
console.log('Dados carregados do localStorage');

// Ver dados completos
console.log('Dados locais:', manager.dados);

// Visualizar fila de sincronização
console.log('Fila de sincronização:', manager.dados.filaSincronizacao);

// ============================================
// 8. LIMPAR DADOS (APENAS PARA TESTE)
// ============================================

// ⚠️ ATENÇÃO: Isso vai apagar TODOS os dados
// manager.limparTodosDados();

// ============================================
// 9. CASOS DE USO PRÁTICOS
// ============================================

// Caso 1: Registrar múltiplas presenças
(async () => {
    const inscricoes = manager.obterInscricoesPorEvento(1, true);
    for (const insc of inscricoes.slice(0, 3)) {
        await manager.registrarPresenca(insc.id, insc.evento_id);
    }
    console.log('Múltiplas presenças registradas');
})();

// Caso 2: Buscar participante não marcado
const inscricoesSemPresenca = manager.dados.inscricoes.filter(insc => {
    return !manager.temPresenca(insc.id);
});
console.log('Inscrições sem presença:', inscricoesSemPresenca);

// Caso 3: Gerar relatório
(async () => {
    const stats = manager.obterEstatisticas();
    console.log(`
        RELATÓRIO OFFLINE
        =================
        Usuários: ${stats.totalUsuarios}
        Eventos: ${stats.totalEventos}
        Inscrições: ${stats.totalInscricoes}
        Presenças: ${stats.totalPresencas}
        Pendentes: ${stats.totalPendentes}
        Modo: ${stats.modo}
        Última sincronização: ${stats.ultimaSincronizacao}
    `);
})();

// ============================================
// 10. MONITORAR MUDANÇAS
// ============================================

// Observar fila de sincronização
setInterval(() => {
    console.log(`Itens pendentes: ${manager.dados.filaSincronizacao.length}`);
}, 10000);

// Verificar conexão periodicamente
setInterval(async () => {
    await manager.verificarConexao();
}, 5000);

// ============================================
// NOTAS IMPORTANTES
// ============================================

/*
1. O token deve estar em localStorage.authToken
2. A URL da API deve estar correta na configuração
3. Todos os dados são armazenados em localStorage
4. A sincronização só funciona quando online
5. O localStorage tem limite de ~5-10MB
6. Use o console (F12) para ver os logs
7. Limpe dados apenas para testes
8. A fila de sincronização persiste após recarregar a página
*/
