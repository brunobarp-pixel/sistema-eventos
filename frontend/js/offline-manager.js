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

        this.API_BASE = config.apiBase || 'http://backend-laravel/api';
        this.OFFLINE_API = config.offlineApi || 'http://backend-python:5000';
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
            // Usar endpoint simples sem autenticação
            const response = await Promise.race([
                fetch(`${this.API_BASE.replace('/api', '')}/`, { 
                    method: 'GET'
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

            // Se online, carregar eventos sem exigir autenticação
            console.log('[OfflineManager] Sistema online - carregando eventos...');
            
            const eventos = await this.carregarEventosSemAuth();
            
            // Inicializar dados básicos
            this.dados = {
                usuarios: [],
                eventos: eventos || [],
                inscricoes: [],
                presencas: [],
                filaSincronizacao: this.dados.filaSincronizacao || [] // Manter fila existente
            };

            // Tentar carregar dados do localStorage para complementar
            const dadosLocal = this.carregarDadosDoStorage();
            if (dadosLocal) {
                this.dados.usuarios = dadosLocal.usuarios || [];
                this.dados.inscricoes = dadosLocal.inscricoes || [];
                this.dados.presencas = dadosLocal.presencas || [];
            }

            // Salvar no localStorage
            this.salvarDadosNoStorage();

            console.log('[OfflineManager] Dados carregados com sucesso', {
                usuarios: this.dados.usuarios.length,
                eventos: this.dados.eventos.length,
                inscricoes: this.dados.inscricoes.length,
                presencas: this.dados.presencas.length
            });

            this.callbacks.onDataLoaded(this.dados);
            return this.dados;

        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar dados:', error);
            this.isOnline = false;
            this.callbacks.onStatusChange(false);
            this.carregarDadosDoStorage();
            this.callbacks.onDataLoaded(this.dados);
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
     * Buscar eventos sem autenticação (públicos)
     */
    async carregarEventosSemAuth() {
        console.log('[OfflineManager] Carregando eventos sem autenticação...');
        
        try {
            // 1. Tentar Laravel primeiro (público)
            console.log('[OfflineManager] Tentando Laravel...');
            const responseLaravel = await fetch('http://localhost:8000/api/eventos');
            
            if (responseLaravel.ok) {
                const dataLaravel = await responseLaravel.json();
                
                if (dataLaravel && dataLaravel.length > 0) {
                    console.log(`[OfflineManager] ✅ ${dataLaravel.length} eventos carregados do Laravel`);
                    // Salvar no localStorage para offline
                    localStorage.setItem('eventos_cache', JSON.stringify(dataLaravel));
                    return dataLaravel;
                }
            }
            
            // 2. Tentar Python MySQL
            console.log('[OfflineManager] Laravel falhou, tentando Python MySQL...');
            const responsePython = await fetch('http://localhost:5000/eventos');
            
            if (responsePython.ok) {
                const dataPython = await responsePython.json();
                
                if (dataPython.success && dataPython.data && dataPython.data.length > 0) {
                    console.log(`[OfflineManager] ✅ ${dataPython.data.length} eventos carregados do Python MySQL`);
                    // Salvar no localStorage para offline
                    localStorage.setItem('eventos_cache', JSON.stringify(dataPython.data));
                    return dataPython.data;
                }
            }
            
            // 3. Usar cache localStorage se tudo falhar
            console.log('[OfflineManager] APIs falharam, usando cache localStorage...');
            const cachedEventos = localStorage.getItem('eventos_cache');
            if (cachedEventos) {
                const eventos = JSON.parse(cachedEventos);
                console.log(`[OfflineManager] ✅ ${eventos.length} eventos carregados do localStorage`);
                return eventos;
            }
            
            // 4. Dados de exemplo como último recurso
            console.log('[OfflineManager] Usando dados de exemplo...');
            return this.getEventosExemplo();
            
        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar eventos:', error);
            // Tentar cache local se há erro de rede
            const cachedEventos = localStorage.getItem('eventos_cache');
            if (cachedEventos) {
                return JSON.parse(cachedEventos);
            }
            return this.getEventosExemplo();
        }
    }

    /**
     * Buscar eventos do servidor
     */
    /**
     * Buscar eventos do servidor
     */
    async buscarEventos() {
        console.log('[OfflineManager] Buscando eventos...');
        return await this.carregarEventosSemAuth();
    }

    /**
     * Carregar eventos com todos os inscritos para modo offline
     */
    async carregarEventosCompletos(token) {
        try {
            console.log('[OfflineManager] Carregando eventos completos com inscritos...');
            
            // Buscar eventos
            const eventos = await this.carregarEventosSemAuth();
            
            // Para cada evento, buscar os inscritos ativos
            const eventosCompletos = await Promise.all(
                eventos.map(async (evento) => {
                    try {
                        // Tentar Laravel primeiro
                        let response = null;
                        if (token) {
                            try {
                                response = await fetch(`${this.API_BASE}/eventos/${evento.id}/inscritos`, {
                                    headers: { 'Authorization': `Bearer ${token}` }
                                });
                            } catch (error) {
                                console.warn(`[OfflineManager] Laravel falhou para evento ${evento.id}, tentando Python`);
                            }
                        }
                        
                        // Fallback para Python
                        if (!response || !response.ok) {
                            try {
                                response = await fetch(`${this.OFFLINE_API}/eventos-offline/${evento.id}/inscritos`);
                            } catch (error) {
                                console.warn(`[OfflineManager] Python também falhou para evento ${evento.id}`);
                            }
                        }
                        
                        if (response && response.ok) {
                            const data = await response.json();
                            evento.inscritos = data.data || [];
                        } else {
                            evento.inscritos = [];
                        }
                        
                        console.log(`[OfflineManager] Evento ${evento.nome || evento.titulo}: ${evento.inscritos.length} inscritos`);
                        return evento;
                    } catch (error) {
                        console.error(`[OfflineManager] Erro ao buscar inscritos do evento ${evento.id}:`, error);
                        evento.inscritos = [];
                        return evento;
                    }
                })
            );

            return eventosCompletos;
        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar eventos completos:', error);
            return this.dados.eventos || [];
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
        // Tentar várias formas de obter o token
        const possiveisTokens = [
            localStorage.getItem(this.STORAGE_KEYS.USER_TOKEN),
            localStorage.getItem('authToken'),
            localStorage.getItem('token'),
            sessionStorage.getItem('authToken'),
            sessionStorage.getItem('token')
        ];
        
        const token = possiveisTokens.find(t => t && t.length > 10);
        
        if (!token) {
            console.warn('[OfflineManager] Nenhum token encontrado. Tentativas:', possiveisTokens);
        }
        
        return token;
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

    /**
     * Marcar presença offline
     */
    async marcarPresencaOffline(inscricaoId, eventoId, usuarioId) {
        try {
            const agora = new Date().toISOString();
            const presencaId = `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            const novaPresenca = {
                id: presencaId,
                inscricao_id: inscricaoId,
                evento_id: eventoId,
                usuario_id: usuarioId,
                data_presenca: agora,
                sincronizado: false,
                offline: true
            };

            // Verificar se já existe presença para esta inscrição
            const presencaExistente = this.dados.presencas.find(p => p.inscricao_id === inscricaoId);
            if (presencaExistente) {
                console.warn('[OfflineManager] Presença já registrada para esta inscrição');
                return false;
            }

            // Adicionar à lista local
            this.dados.presencas.push(novaPresenca);

            // Adicionar à fila de sincronização
            this.adicionarFilaSincronizacao({
                tipo: 'presenca',
                dados: novaPresenca,
                timestamp: agora
            });

            // Salvar no localStorage
            this.salvarDadosNoStorage();

            console.log('[OfflineManager] Presença marcada offline:', {
                inscricaoId,
                eventoId,
                usuarioId,
                presencaId
            });

            this.callbacks.onPresencaRegistrada({
                presenca: novaPresenca,
                offline: true
            });

            return true;
        } catch (error) {
            console.error('[OfflineManager] Erro ao marcar presença offline:', error);
            return false;
        }
    }

    /**
     * Sincronizar todas as presenças offline
     */
    async sincronizarPresencas() {
        if (!this.isOnline) {
            console.warn('[OfflineManager] Não é possível sincronizar - sistema offline');
            return { sucesso: false, erro: 'Sistema offline' };
        }

        const token = this.getToken();
        if (!token) {
            console.warn('[OfflineManager] Token não encontrado');
            return { sucesso: false, erro: 'Token não encontrado' };
        }

        const presencasOffline = this.dados.filaSincronizacao.filter(item => 
            item.tipo === 'presenca' && !item.dados.sincronizado
        );

        if (presencasOffline.length === 0) {
            console.log('[OfflineManager] Nenhuma presença para sincronizar');
            return { sucesso: true, sincronizadas: 0 };
        }

        console.log(`[OfflineManager] Sincronizando ${presencasOffline.length} presenças...`);
        this.callbacks.onSyncStart();

        let sucesso = 0;
        let erros = 0;
        const resultados = [];

        for (const item of presencasOffline) {
            const presenca = item.dados;
            
            try {
                // Sincronizar presença
                const response = await fetch(`${this.API_BASE}/presencas`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        inscricao_id: presenca.inscricao_id,
                        data_presenca: presenca.data_presenca
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    // Atualizar presença local
                    const index = this.dados.presencas.findIndex(p => p.id === presenca.id);
                    if (index !== -1) {
                        this.dados.presencas[index] = {
                            ...this.dados.presencas[index],
                            id: data.data.id,
                            sincronizado: true,
                            offline: false
                        };
                    }

                    // Gerar certificado automaticamente
                    await this.gerarCertificadoAutomatico(presenca.inscricao_id, presenca.evento_id, presenca.usuario_id);

                    resultados.push({
                        presenca: presenca.id,
                        sucesso: true,
                        certificado: true
                    });

                    sucesso++;
                } else {
                    console.error(`[OfflineManager] Erro ao sincronizar presença ${presenca.id}:`, response.statusText);
                    resultados.push({
                        presenca: presenca.id,
                        sucesso: false,
                        erro: response.statusText
                    });
                    erros++;
                }
            } catch (error) {
                console.error(`[OfflineManager] Erro ao sincronizar presença ${presenca.id}:`, error);
                resultados.push({
                    presenca: presenca.id,
                    sucesso: false,
                    erro: error.message
                });
                erros++;
            }
        }

        // Remover itens sincronizados da fila
        this.dados.filaSincronizacao = this.dados.filaSincronizacao.filter(item => 
            !(item.tipo === 'presenca' && resultados.some(r => r.presenca === item.dados.id && r.sucesso))
        );

        // Salvar dados atualizados
        this.salvarDadosNoStorage();

        const resultado = {
            sucesso: erros === 0,
            sincronizadas: sucesso,
            erros: erros,
            total: presencasOffline.length,
            detalhes: resultados
        };

        console.log('[OfflineManager] Sincronização concluída:', resultado);
        this.callbacks.onSyncEnd(resultado);

        return resultado;
    }

    /**
     * Gerar certificado automaticamente após marcar presença
     */
    async gerarCertificadoAutomatico(inscricaoId, eventoId, usuarioId) {
        try {
            console.log(`[OfflineManager] Gerando certificado automático - Inscrição: ${inscricaoId}, Evento: ${eventoId}, Usuário: ${usuarioId}`);
            
            const response = await fetch(`${this.OFFLINE_API}/gerar-certificado`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inscricao_id: inscricaoId,
                    evento_id: eventoId,
                    usuario_id: usuarioId
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[OfflineManager] Certificado gerado com sucesso:', data);
                return true;
            } else {
                console.error('[OfflineManager] Erro ao gerar certificado:', response.statusText);
                return false;
            }
        } catch (error) {
            console.error('[OfflineManager] Erro ao gerar certificado automático:', error);
            return false;
        }
    }
    
    getEventosExemplo() {
        return [
            {
                id: 1,
                nome: "Workshop Laravel Offline",
                titulo: "Workshop Laravel Offline", 
                descricao: "Introdução ao desenvolvimento com Laravel",
                data_inicio: "2025-12-15 09:00:00",
                data_fim: "2025-12-15 17:00:00", 
                local: "Laboratório 1",
                vagas: 30,
                status: "aberto",
                total_inscritos: 5
            },
            {
                id: 2,
                nome: "Palestra Docker Offline",
                titulo: "Palestra Docker Offline",
                descricao: "Containerização com Docker",
                data_inicio: "2025-12-20 14:00:00", 
                data_fim: "2025-12-20 16:00:00",
                local: "Auditório",
                vagas: 50,
                status: "aberto",
                total_inscritos: 12
            },
            {
                id: 3,
                nome: "Curso JavaScript Offline",
                titulo: "Curso JavaScript Offline",
                descricao: "JavaScript moderno e frameworks",
                data_inicio: "2026-01-10 08:00:00",
                data_fim: "2026-01-12 18:00:00",
                local: "Sala 201", 
                vagas: 25,
                status: "aberto",
                total_inscritos: 8
            }
        ];
    }
    
    /**
     * Cria usuário de teste para funcionalidade offline
     */
    criarUsuarioTeste() {
        const usuarioTeste = {
            id: 999,
            nome: "Usuário Offline",
            email: "offline@teste.com",
            cpf: "00000000000",
            telefone: "(51)99999-9999",
            criado_em: new Date().toISOString()
        };
        
        // Salvar no localStorage
        localStorage.setItem('usuario_offline_teste', JSON.stringify(usuarioTeste));
        console.log('[OfflineManager] Usuário de teste criado:', usuarioTeste);
        
        return usuarioTeste;
    }
    
    /**
     * Obter usuário para operações offline
     */
    getUsuarioOffline() {
        let usuario = JSON.parse(localStorage.getItem('usuario_offline_teste') || 'null');
        
        if (!usuario) {
            console.log('[OfflineManager] Criando usuário de teste para modo offline');
            usuario = this.criarUsuarioTeste();
        }
        
        return usuario;
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.OfflineManager = OfflineManager;
}
