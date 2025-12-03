
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

    async verificarConexao() {
        const statusAnterior = this.isOnline;
        
        try {
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
        }

        return this.isOnline;
    }

    async carregarTodosDados() {
        
        try {
            await this.verificarConexao();

            if (!this.isOnline) {
                this.carregarDadosDoStorage();
                this.callbacks.onDataLoaded(this.dados);
                return this.dados;
            }

            
            const eventos = await this.carregarEventosSemAuth();
            
            this.dados = {
                usuarios: [],
                eventos: eventos || [],
                inscricoes: [],
                presencas: [],
                filaSincronizacao: this.dados.filaSincronizacao || [] 
            };

            const dadosLocal = this.carregarDadosDoStorage();
            if (dadosLocal) {
                this.dados.usuarios = dadosLocal.usuarios || [];
                this.dados.inscricoes = dadosLocal.inscricoes || [];
                this.dados.presencas = dadosLocal.presencas || [];
            }
            
            if (this.dados.eventos.length === 0) {
                this.dados.eventos = this.getEventosExemplo();
            }

            this.salvarDadosNoStorage();

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

    async carregarEventosSemAuth() {
        
        try {
            const responseLaravel = await fetch('http://localhost:8000/api/eventos');
            
            if (responseLaravel.ok) {
                const dataLaravel = await responseLaravel.json();
                
                if (dataLaravel && dataLaravel.length > 0) {
                    localStorage.setItem('eventos_cache', JSON.stringify(dataLaravel));
                    return dataLaravel;
                }
            }
            
            const responsePython = await fetch('http://localhost:5000/eventos');
            
            if (responsePython.ok) {
                const dataPython = await responsePython.json();
                
                if (dataPython.success && dataPython.data && dataPython.data.length > 0) {
                    localStorage.setItem('eventos_cache', JSON.stringify(dataPython.data));
                    return dataPython.data;
                }
            }
            
            const cachedEventos = localStorage.getItem('eventos_cache');
            if (cachedEventos) {
                const eventos = JSON.parse(cachedEventos);
                return eventos;
            }
            
            return this.getEventosExemplo();
            
        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar eventos:', error);
            const cachedEventos = localStorage.getItem('eventos_cache');
            if (cachedEventos) {
                return JSON.parse(cachedEventos);
            }
            return this.getEventosExemplo();
        }
    }


    async buscarEventos() {
        return await this.carregarEventosSemAuth();
    }


    async carregarEventosCompletos(token) {
        try {
            
            const eventos = await this.carregarEventosSemAuth();
            
            const eventosCompletos = await Promise.all(
                eventos.map(async (evento) => {
                    try {
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


    async registrarPresenca(inscricaoId, eventoId) {
        const presenca = {
            id: `temp_${Date.now()}`,
            inscricao_id: inscricaoId,
            evento_id: eventoId,
            data_presenca: new Date().toISOString(),
            sincronizado: false,
            status: 'pendente'
        };

        this.dados.presencas.push(presenca);

        this.adicionarFilaSincronizacao({
            tipo: 'presenca',
            acao: 'criar',
            dados: presenca,
            timestamp: Date.now()
        });

        this.salvarDadosNoStorage();

        this.callbacks.onPresencaRegistrada(presenca);

        if (this.isOnline) {
            this.sincronizarPresenca(presenca);
        }

        return presenca;
    }


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
                
                if (data.data && data.data.id) {
                    const index = this.dados.presencas.findIndex(p => p.id === presenca.id);
                    if (index !== -1) {
                        this.dados.presencas[index].id = data.data.id;
                        this.dados.presencas[index].sincronizado = true;
                    }
                }

                this.removerFilaSincronizacao(presenca.id);
                this.salvarDadosNoStorage();

                return true;
            }
        } catch (error) {
            console.error('[OfflineManager] Erro ao sincronizar presença:', error);
        }

        return false;
    }


    adicionarFilaSincronizacao(item) {
        if (!this.dados.filaSincronizacao) {
            this.dados.filaSincronizacao = [];
        }
        this.dados.filaSincronizacao.push(item);
    }

 
    removerFilaSincronizacao(itemId) {
        this.dados.filaSincronizacao = this.dados.filaSincronizacao.filter(
            item => item.dados && item.dados.id !== itemId
        );
    }


    async sincronizarTodos() {
        if (!this.isOnline) {
            throw new Error('Sem conexão com internet. Sincronização não é possível.');
        }

        this.callbacks.onSyncStart();

        try {
            let totalSincronizados = 0;
            const erros = [];

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


    carregarDadosDoStorage() {
        try {
            const dados = {
                usuarios: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.USUARIOS)) || [],
                eventos: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.EVENTOS)) || [],
                inscricoes: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.INSCRICOES)) || [],
                presencas: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.PRESENCAS)) || [],
                filaSincronizacao: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.FILA_SINCRONIZACAO)) || []
            };

            this.dados = dados;

            console.log('[OfflineManager] Dados carregados do localStorage', {
                usuarios: dados.usuarios.length,
                eventos: dados.eventos.length,
                inscricoes: dados.inscricoes.length,
                presencas: dados.presencas.length,
                pendentes: dados.filaSincronizacao.length
            });
            
            return dados;
        } catch (error) {
            console.error('[OfflineManager] Erro ao carregar dados do localStorage:', error);
            const dadosVazios = {
                usuarios: [],
                eventos: [],
                inscricoes: [],
                presencas: [],
                filaSincronizacao: []
            };
            this.dados = dadosVazios;
            return dadosVazios;
        }
    }


    getToken() {
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

    
    obterInscricao(inscricaoId) {
        return this.dados.inscricoes.find(i => i.id === inscricaoId);
    }

    obterUsuario(usuarioId) {
        return this.dados.usuarios.find(u => u.id === usuarioId);
    }


    obterEvento(eventoId) {
        return this.dados.eventos.find(e => e.id === eventoId);
    }


    obterInscricoesPorEvento(eventoId, ativo = true) {
        return this.dados.inscricoes.filter(i => 
            i.evento_id === eventoId && (!ativo || i.status === 'ativa')
        );
    }


    temPresenca(inscricaoId) {
        return this.dados.presencas.some(p => p.inscricao_id === inscricaoId);
    }

    contarPresencasPorEvento(eventoId) {
        return this.dados.presencas.filter(p => p.evento_id === eventoId).length;
    }


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

            const presencaExistente = this.dados.presencas.find(p => p.inscricao_id === inscricaoId);
            if (presencaExistente) {
                console.warn('[OfflineManager] Presença já registrada para esta inscrição');
                return false;
            }

            this.dados.presencas.push(novaPresenca);

            this.adicionarFilaSincronizacao({
                tipo: 'presenca',
                dados: novaPresenca,
                timestamp: agora
            });

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


    async sincronizarPresencas() {
        console.log('[OfflineManager] Iniciando sincronização de presenças...');
        
        const presencasOffline = JSON.parse(localStorage.getItem('presencas_offline') || '[]');
        const presencasNaoSincronizadas = presencasOffline.filter(p => !p.sincronizado);
        
        if (presencasNaoSincronizadas.length === 0) {
            console.log('[OfflineManager] Nenhuma presença para sincronizar');
            return {
                sucesso: true,
                sincronizadas: 0,
                message: 'Nenhuma presença pendente'
            };
        }
        
        console.log(`[OfflineManager] Sincronizando ${presencasNaoSincronizadas.length} presenças...`);
        
        let sincronizadas = 0;
        const erros = [];
        
        for (const presenca of presencasNaoSincronizadas) {
            try {
                const response = await fetch(`${this.OFFLINE_API}/presencas`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        inscricao_id: presenca.inscricao_id
                    })
                });
                
                if (response.ok) {
                    presenca.sincronizado = true;
                    sincronizadas++;
                    console.log(`[OfflineManager] Presença ${presenca.inscricao_id} sincronizada`);
                } else {
                    console.warn(`[OfflineManager] Falha ao sincronizar presença ${presenca.inscricao_id}`);
                    erros.push(presenca.inscricao_id);
                }
                
            } catch (error) {
                console.error(`[OfflineManager] Erro ao sincronizar presença ${presenca.inscricao_id}:`, error);
                erros.push(presenca.inscricao_id);
            }
        }
        
        localStorage.setItem('presencas_offline', JSON.stringify(presencasOffline));
        
        console.log(`[OfflineManager] Sincronização completa: ${sincronizadas}/${presencasNaoSincronizadas.length}`);
        
        return {
            sucesso: true,
            sincronizadas: sincronizadas,
            total: presencasNaoSincronizadas.length,
            erros: erros,
            message: `${sincronizadas} presenças sincronizadas`
        };
    }


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
    

    criarUsuarioTeste() {
        const usuarioTeste = {
            id: 999,
            nome: "Usuário Offline",
            email: "offline@teste.com",
            cpf: "00000000000",
            telefone: "(51)99999-9999",
            criado_em: new Date().toISOString()
        };
        
        localStorage.setItem('usuario_offline_teste', JSON.stringify(usuarioTeste));
        console.log('[OfflineManager] Usuário de teste criado:', usuarioTeste);
        
        return usuarioTeste;
    }

    getUsuarioOffline() {
        let usuario = JSON.parse(localStorage.getItem('usuario_offline_teste') || 'null');
        
        if (!usuario) {
            console.log('[OfflineManager] Criando usuário de teste para modo offline');
            usuario = this.criarUsuarioTeste();
        }
        
        return usuario;
    }
}

if (typeof window !== 'undefined') {
    window.OfflineManager = OfflineManager;
}


//ver das qustoes do localstorage