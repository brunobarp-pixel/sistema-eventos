/**
 * Sistema de Gerenciamento Offline - OfflineManager
 * Gerencia o carregamento de dados, armazenamento local e sincronização
 */

class OfflineManager {
    constructor(config = {}) {
        this.STORAGE_KEYS = {
            USUARIOS: 'sistema_eventos_usuarios',
            EVENTOS: 'sistema_eventos_eventos',
            INSCRICOES: 'sistema_eventos_inscricoes',
            PRESENCAS: 'sistema_eventos_presencas',
            FILA_SINCRONIZACAO: 'sistema_eventos_fila_sync',
            ULTIMA_SYNC: 'sistema_eventos_ultima_sync',
            USER_TOKEN: 'authToken'
        };

        this.API_BASE = config.apiBase || 'http://localhost:8000/api';
        this.OFFLINE_API = config.offlineApi || 'http://localhost:5000';
        this.TIMEOUT = config.timeout || 5000;

        this.isOnline = false;
        this.dados = {
            usuarios: [],
            eventos: [],
            inscricoes: [],
            presencas: [],
            filaSincronizacao: []
        };

        this.callbacks = {
            onStatusChange: config.onStatusChange || (() => {}),
            onDataLoaded: config.onDataLoaded || (() => {}),
            onSyncStart: config.onSyncStart || (() => {}),
            onSyncEnd: config.onSyncEnd || (() => {}),
            onSyncError: config.onSyncError || (() => {}),
            onPresencaRegistrada: config.onPresencaRegistrada || (() => {})
        };
    }

    /**
     * Verificar conexão com internet
     */
    async verificarConexao() {
        const statusAnterior = this.isOnline;
        
        try {
            const response = await Promise.race([
                fetch(`${this.API_BASE}/status`, { 
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${this.getToken()}` }
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout')), this.TIMEOUT)
                )
            ]);

            this.isOnline = response.ok;
        } catch (error) {
            this.isOnline = false;
        }

        if (statusAnterior !== this.isOnline) {
            this.callbacks.onStatusChange(this.isOnline);
            console.log(`[OfflineManager] Status de conexão: ${this.isOnline ? 'ONLINE' : 'OFFLINE'}`);
        }

        return this.isOnline;
    }

    /**
     * Carregar todos os dados necessários do servidor
     */
    async carregarTodosDados() {
        console.log('[OfflineManager] Carregando dados...');
        
        try {
            // Primeiro verificar conexão
            await this.verificarConexao();

            if (!this.isOnline) {
                console.log('[OfflineManager] Modo offline - carregando dados do localStorage');
                this.carregarDadosDoStorage();
                this.callbacks.onDataLoaded(this.dados);
                return this.dados;
            }

            // Se online, carregar do servidor
            const token = this.getToken();
            if (!token) {
                throw new Error('Token de autenticação não encontrado');
            }

            // Carregar em paralelo
            const [usuarios, eventos, inscricoes, presencas] = await Promise.all([
                this.buscarUsuarios(token),
                this.buscarEventos(token),
                this.buscarInscricoes(token),
                this.buscarPresencas(token)
            ]);

            this.dados = {
                usuarios,
                eventos,
                inscricoes,
                presencas,
                filaSincronizacao: this.dados.filaSincronizacao // Manter fila existente
            };

            // Salvar no localStorage
            this.salvarDadosNoStorage();

            console.log('[OfflineManager] Dados carregados com sucesso', {
                usuarios: usuarios.length,
                eventos: eventos.length,
                inscricoes: inscricoes.length,
                presencas: presencas.length
            });

            this.callbacks.onDataLoaded(this.dados);
            return this.dados;

        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar dados:', error);
            this.isOnline = false;
            this.callbacks.onStatusChange(false);
            this.carregarDadosDoStorage();
            return this.dados;
        }
    }

    /**
     * Buscar usuários do servidor
     */
    async buscarUsuarios(token) {
        try {
            const response = await fetch(`${this.API_BASE}/usuarios`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Erro ao buscar usuários');
            const data = await response.json();
            return data.data || [];
        } catch (error) {
            console.error('[OfflineManager] Erro ao buscar usuários:', error);
            return this.dados.usuarios;
        }
    }

    /**
     * Buscar eventos do servidor
     */
    async buscarEventos(token) {
        try {
            const response = await fetch(`${this.API_BASE}/eventos`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Erro ao buscar eventos');
            const data = await response.json();
            return data.data || [];
        } catch (error) {
            console.error('[OfflineManager] Erro ao buscar eventos:', error);
            return this.dados.eventos;
        }
    }

    /**
     * Buscar inscrições do servidor
     */
    async buscarInscricoes(token) {
        try {
            const response = await fetch(`${this.API_BASE}/inscricoes`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Erro ao buscar inscrições');
            const data = await response.json();
            return data.data || [];
        } catch (error) {
            console.error('[OfflineManager] Erro ao buscar inscrições:', error);
            return this.dados.inscricoes;
        }
    }

    /**
     * Buscar presenças do servidor
     */
    async buscarPresencas(token) {
        try {
            const response = await fetch(`${this.API_BASE}/presencas`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Erro ao buscar presenças');
            const data = await response.json();
            return data.data || [];
        } catch (error) {
            console.error('[OfflineManager] Erro ao buscar presenças:', error);
            return this.dados.presencas;
        }
    }

    /**
     * Registrar presença (offline ou online)
     */
    async registrarPresenca(inscricaoId, eventoId) {
        const presenca = {
            id: `temp_${Date.now()}`,
            inscricao_id: inscricaoId,
            evento_id: eventoId,
            data_presenca: new Date().toISOString(),
            sincronizado: false,
            status: 'pendente'
        };

        // Adicionar à lista local
        this.dados.presencas.push(presenca);

        // Adicionar à fila de sincronização
        this.adicionarFilaSincronizacao({
            tipo: 'presenca',
            acao: 'criar',
            dados: presenca,
            timestamp: Date.now()
        });

        // Salvar no localStorage
        this.salvarDadosNoStorage();

        // Notificar
        this.callbacks.onPresencaRegistrada(presenca);

        // Se online, sincronizar imediatamente
        if (this.isOnline) {
            this.sincronizarPresenca(presenca);
        }

        return presenca;
    }

    /**
     * Sincronizar uma presença com o servidor
     */
    async sincronizarPresenca(presenca) {
        try {
            const token = this.getToken();
            
            const response = await fetch(`${this.API_BASE}/presencas`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inscricao_id: presenca.inscricao_id,
                    data_presenca: presenca.data_presenca
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Atualizar ID da presença
                if (data.data && data.data.id) {
                    const index = this.dados.presencas.findIndex(p => p.id === presenca.id);
                    if (index !== -1) {
                        this.dados.presencas[index].id = data.data.id;
                        this.dados.presencas[index].sincronizado = true;
                    }
                }

                // Remover da fila
                this.removerFilaSincronizacao(presenca.id);
                this.salvarDadosNoStorage();

                return true;
            }
        } catch (error) {
            console.error('[OfflineManager] Erro ao sincronizar presença:', error);
        }

        return false;
    }

    /**
     * Adicionar item à fila de sincronização
     */
    adicionarFilaSincronizacao(item) {
        if (!this.dados.filaSincronizacao) {
            this.dados.filaSincronizacao = [];
        }
        this.dados.filaSincronizacao.push(item);
    }

    /**
     * Remover item da fila de sincronização
     */
    removerFilaSincronizacao(itemId) {
        this.dados.filaSincronizacao = this.dados.filaSincronizacao.filter(
            item => item.dados && item.dados.id !== itemId
        );
    }

    /**
     * Sincronizar todos os dados pendentes
     */
    async sincronizarTodos() {
        if (!this.isOnline) {
            throw new Error('Sem conexão com internet. Sincronização não é possível.');
        }

        this.callbacks.onSyncStart();

        try {
            let totalSincronizados = 0;
            const erros = [];

            // Sincronizar presenças
            for (const item of this.dados.filaSincronizacao) {
                if (item.tipo === 'presenca') {
                    try {
                        const sucesso = await this.sincronizarPresenca(item.dados);
                        if (sucesso) {
                            totalSincronizados++;
                        }
                    } catch (error) {
                        erros.push({
                            tipo: item.tipo,
                            mensagem: error.message
                        });
                    }
                }
            }

            // Recarregar dados do servidor para garantir sincronização
            await this.carregarTodosDados();

            this.callbacks.onSyncEnd({
                sucesso: true,
                totalSincronizados,
                erros
            });

            console.log(`[OfflineManager] Sincronização completa: ${totalSincronizados} itens sincronizados`);
            return { totalSincronizados, erros };

        } catch (error) {
            console.error('[OfflineManager] Erro durante sincronização:', error);
            this.callbacks.onSyncError(error);
            throw error;
        }
    }

    /**
     * Salvar dados no localStorage
     */
    salvarDadosNoStorage() {
        try {
            localStorage.setItem(this.STORAGE_KEYS.USUARIOS, JSON.stringify(this.dados.usuarios));
            localStorage.setItem(this.STORAGE_KEYS.EVENTOS, JSON.stringify(this.dados.eventos));
            localStorage.setItem(this.STORAGE_KEYS.INSCRICOES, JSON.stringify(this.dados.inscricoes));
            localStorage.setItem(this.STORAGE_KEYS.PRESENCAS, JSON.stringify(this.dados.presencas));
            localStorage.setItem(this.STORAGE_KEYS.FILA_SINCRONIZACAO, JSON.stringify(this.dados.filaSincronizacao));
            localStorage.setItem(this.STORAGE_KEYS.ULTIMA_SYNC, new Date().toISOString());
            
            console.log('[OfflineManager] Dados salvos no localStorage');
        } catch (error) {
            console.error('[OfflineManager] Erro ao salvar dados no localStorage:', error);
        }
    }

    /**
     * Carregar dados do localStorage
     */
    carregarDadosDoStorage() {
        try {
            this.dados = {
                usuarios: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.USUARIOS)) || [],
                eventos: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.EVENTOS)) || [],
                inscricoes: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.INSCRICOES)) || [],
                presencas: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.PRESENCAS)) || [],
                filaSincronizacao: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.FILA_SINCRONIZACAO)) || []
            };

            console.log('[OfflineManager] Dados carregados do localStorage', {
                usuarios: this.dados.usuarios.length,
                eventos: this.dados.eventos.length,
                inscricoes: this.dados.inscricoes.length,
                presencas: this.dados.presencas.length,
                pendentes: this.dados.filaSincronizacao.length
            });
        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar dados do localStorage:', error);
            this.dados = {
                usuarios: [],
                eventos: [],
                inscricoes: [],
                presencas: [],
                filaSincronizacao: []
            };
        }
    }

    /**
     * Obter token de autenticação
     */
    getToken() {
        return localStorage.getItem(this.STORAGE_KEYS.USER_TOKEN);
    }

    /**
     * Obter informações de uma inscrição
     */
    obterInscricao(inscricaoId) {
        return this.dados.inscricoes.find(i => i.id === inscricaoId);
    }

    /**
     * Obter informações de um usuário
     */
    obterUsuario(usuarioId) {
        return this.dados.usuarios.find(u => u.id === usuarioId);
    }

    /**
     * Obter informações de um evento
     */
    obterEvento(eventoId) {
        return this.dados.eventos.find(e => e.id === eventoId);
    }

    /**
     * Buscar inscrições por evento
     */
    obterInscricoesPorEvento(eventoId, ativo = true) {
        return this.dados.inscricoes.filter(i => 
            i.evento_id === eventoId && (!ativo || i.status === 'ativa')
        );
    }

    /**
     * Buscar presenças já registradas para uma inscrição
     */
    temPresenca(inscricaoId) {
        return this.dados.presencas.some(p => p.inscricao_id === inscricaoId);
    }

    /**
     * Contar presenças por evento
     */
    contarPresencasPorEvento(eventoId) {
        return this.dados.presencas.filter(p => p.evento_id === eventoId).length;
    }

    /**
     * Obter estatísticas
     */
    obterEstatisticas() {
        return {
            totalUsuarios: this.dados.usuarios.length,
            totalEventos: this.dados.eventos.length,
            totalInscricoes: this.dados.inscricoes.length,
            totalPresencas: this.dados.presencas.length,
            totalPendentes: this.dados.filaSincronizacao.length,
            modo: this.isOnline ? 'online' : 'offline',
            ultimaSincronizacao: localStorage.getItem(this.STORAGE_KEYS.ULTIMA_SYNC)
        };
    }

    /**
     * Limpar todos os dados (para teste)
     */
    limparTodosDados() {
        Object.values(this.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        this.dados = {
            usuarios: [],
            eventos: [],
            inscricoes: [],
            presencas: [],
            filaSincronizacao: []
        };
        console.log('[OfflineManager] Todos os dados foram limpos');
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.OfflineManager = OfflineManager;
}
