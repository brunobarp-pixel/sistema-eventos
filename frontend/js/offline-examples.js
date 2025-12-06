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


(async () => {
    try {
        const dados = await manager.carregarTodosDados();
        console.log('Dados carregados com sucesso:', dados);
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
})();


(async () => {
    await manager.verificarConexao();
    console.log(`Modo: ${manager.isOnline ? 'ONLINE' : 'OFFLINE'}`);
})();


const stats = manager.obterEstatisticas();
console.log('Estatísticas:', stats);

const usuario = manager.obterUsuario(1);
console.log('Usuário:', usuario);

const evento = manager.obterEvento(1);
console.log('Evento:', evento);

const inscricao = manager.obterInscricao(1);
console.log('Inscrição:', inscricao);

const inscricoesPorEvento = manager.obterInscricoesPorEvento(1, true);
console.log('Inscrições do evento 1:', inscricoesPorEvento);

const temPresenca = manager.temPresenca(1);
console.log('Tem presença:', temPresenca);

const totalPresencas = manager.contarPresencasPorEvento(1);
console.log('Presenças do evento 1:', totalPresencas);


(async () => {
    try {
        const presenca = await manager.registrarPresenca(5, 1);
        console.log('Presença registrada:', presenca);
    } catch (error) {
        console.error('Erro ao registrar presença:', error);
    }
})();


(async () => {
    try {
        if (!manager.isOnline) {
            console.log('Sistema offline - não é possível sincronizar');
            return;
        }

        const resultado = await manager.sincronizarTodos();
        console.log('Sincronização concluída:', resultado);

    } catch (error) {
        console.error('Erro ao sincronizar:', error);
    }
})();


manager.salvarDadosNoStorage();
console.log('Dados salvos no localStorage');

manager.carregarDadosDoStorage();
console.log('Dados carregados do localStorage');

console.log('Dados locais:', manager.dados);

console.log('Fila de sincronização:', manager.dados.filaSincronizacao);


(async () => {
    const inscricoes = manager.obterInscricoesPorEvento(1, true);
    for (const insc of inscricoes.slice(0, 3)) {
        await manager.registrarPresenca(insc.id, insc.evento_id);
    }
    console.log('Múltiplas presenças registradas');
})();

const inscricoesSemPresenca = manager.dados.inscricoes.filter(insc => {
    return !manager.temPresenca(insc.id);
});
console.log('Inscrições sem presença:', inscricoesSemPresenca);

(async () => {
    const stats = manager.obterEstatisticas();
    console.log(`
        Usuários: ${stats.totalUsuarios}
        Eventos: ${stats.totalEventos}
        Inscrições: ${stats.totalInscricoes}
        Presenças: ${stats.totalPresencas}
        Pendentes: ${stats.totalPendentes}
        Modo: ${stats.modo}
        Última sincronização: ${stats.ultimaSincronizacao}
    `);
})();


setInterval(() => {
    console.log(`Itens pendentes: ${manager.dados.filaSincronizacao.length}`);
}, 10000);

setInterval(async () => {
    await manager.verificarConexao();
}, 5000);

//Validar o que o charles comentou sobre este arquivo.