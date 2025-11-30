/**
 * OfflineManager Simplificado
 * Sistema offline que funciona apenas com localStorage + MySQL
 * Sem SQLite, sem dependências complexas
 */
class OfflineManager {
    constructor(config = {}) {
        this.API_BASE = config.apiBase || 'http://localhost:8000/api';
        this.OFFLINE_API = config.offlineApi || 'http://localhost:5000';
        this.timeout = config.timeout || 5000;
        
        // Callbacks
        this.callbacks = {
            onStatusChange: config.onStatusChange || (() => {}),
            onDataLoaded: config.onDataLoaded || (() => {}),
            onPresencaRegistrada: config.onPresencaRegistrada || (() => {}),
            onSyncStart: config.onSyncStart || (() => {}),
            onSyncEnd: config.onSyncEnd || (() => {}),
            onSyncError: config.onSyncError || (() => {})
        };
        
        // Estado
        this.isOnline = true;
        this.dados = {
            usuarios: [],
            eventos: [],
            inscricoes: [],
            presencas: [],
            filaSincronizacao: []
        };
        
        // Chaves do localStorage
        this.STORAGE_KEYS = {
            USUARIOS: 'offline_usuarios',
            EVENTOS: 'offline_eventos', 
            INSCRICOES: 'offline_inscricoes',
            PRESENCAS: 'offline_presencas',
            FILA_SINCRONIZACAO: 'offline_fila_sync',
            SISTEMA_TOKEN: 'sistema_offline_token'
        };
        
        // Token fixo do sistema para autenticação
        this.SISTEMA_TOKEN = null;
        
        console.log('[OfflineManager] Inicializado em modo simplificado');
    }
    
    /**
     * Obter token do sistema para autenticação
     */
    async obterTokenSistema() {
        try {
            // Verificar se já tem token armazenado
            const tokenArmazenado = localStorage.getItem(this.STORAGE_KEYS.SISTEMA_TOKEN);
            if (tokenArmazenado) {
                this.SISTEMA_TOKEN = tokenArmazenado;
                console.log('[OfflineManager] 🔑 Token do sistema recuperado do localStorage');
                return tokenArmazenado;
            }
            
            // Obter novo token do servidor Python
            console.log('[OfflineManager] 🔑 Obtendo token do sistema...');
            const response = await fetch(`${this.OFFLINE_API}/sistema-token`);
            
            if (response.ok) {
                const data = await response.json();
                this.SISTEMA_TOKEN = data.token;
                
                // Armazenar token
                localStorage.setItem(this.STORAGE_KEYS.SISTEMA_TOKEN, data.token);
                
                console.log('[OfflineManager] ✅ Token do sistema obtido:', data.usuario.nome);
                return data.token;
            } else {
                console.warn('[OfflineManager] ⚠️ Falha ao obter token do sistema');
                return null;
            }
            
        } catch (error) {
            console.error('[OfflineManager] ❌ Erro ao obter token do sistema:', error);
            return null;
        }
    }
    
    /**
     * Obter headers com autenticação
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.SISTEMA_TOKEN) {
            headers['Authorization'] = `Bearer ${this.SISTEMA_TOKEN}`;
        }
        
        return headers;
    }
    
    /**
     * Verificar conexão com as APIs
     */
    async verificarConexao() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(`${this.OFFLINE_API}/status`, {
                signal: controller.signal,
                method: 'GET'
            });
            
            clearTimeout(timeoutId);
            
            this.isOnline = response.ok;
            this.callbacks.onStatusChange(this.isOnline);
            
            console.log(`[OfflineManager] Status: ${this.isOnline ? 'ONLINE' : 'OFFLINE'}`);
            return this.isOnline;
            
        } catch (error) {
            this.isOnline = false;
            this.callbacks.onStatusChange(false);
            console.log('[OfflineManager] Status: OFFLINE (erro de conexão)');
            return false;
        }
    }
    
    /**
     * Carregar todos os dados necessários
     */
    async carregarTodosDados() {
        console.log('[OfflineManager] 🔄 Carregando dados...');
        
        try {
            // Obter token do sistema primeiro
            await this.obterTokenSistema();
            
            // Verificar conexão
            await this.verificarConexao();
            
            // Carregar eventos (sem exigir autenticação)
            const eventos = await this.carregarEventos();
            
            // Carregar dados do localStorage
            const dadosLocal = this.carregarDadosDoStorage();
            
            // Se temos token, tentar carregar dados autenticados
            let usuarios = [];
            let inscricoes = [];
            let presencas = [];
            
            if (this.SISTEMA_TOKEN && this.isOnline) {
                try {
                    console.log('[OfflineManager] 🔑 Carregando dados com token do sistema...');
                    [usuarios, inscricoes, presencas] = await Promise.all([
                        this.buscarUsuarios(),
                        this.buscarInscricoes(), 
                        this.buscarPresencas()
                    ]);
                } catch (authError) {
                    console.warn('[OfflineManager] ⚠️ Erro ao carregar dados autenticados:', authError);
                    // Usar dados do localStorage como fallback
                    usuarios = dadosLocal.usuarios || [];
                    inscricoes = dadosLocal.inscricoes || [];
                    presencas = dadosLocal.presencas || [];
                }
            } else {
                console.log('[OfflineManager] 💾 Usando dados do localStorage...');
                usuarios = dadosLocal.usuarios || [];
                inscricoes = dadosLocal.inscricoes || [];
                presencas = dadosLocal.presencas || [];
            }
            
            // Combinar dados
            this.dados = {
                usuarios,
                eventos: eventos.length > 0 ? eventos : dadosLocal.eventos || this.getEventosExemplo(),
                inscricoes,
                presencas,
                filaSincronizacao: dadosLocal.filaSincronizacao || []
            };
            
            // Salvar no localStorage
            this.salvarDadosNoStorage();
            
            console.log('[OfflineManager] ✅ Dados carregados:', {
                usuarios: this.dados.usuarios.length,
                eventos: this.dados.eventos.length,
                inscricoes: this.dados.inscricoes.length,
                presencas: this.dados.presencas.length,
                token: this.SISTEMA_TOKEN ? '✅' : '❌'
            });
            
            this.callbacks.onDataLoaded(this.dados);
            return this.dados;
            
        } catch (error) {
            console.error('[OfflineManager] ❌ Erro ao carregar dados:', error);
            
            // Fallback para localStorage
            this.carregarDadosDoStorage();
            
            // Se não há dados, usar exemplos
            if (this.dados.eventos.length === 0) {
                this.dados.eventos = this.getEventosExemplo();
            }
            
            this.callbacks.onDataLoaded(this.dados);
            return this.dados;
        }
    }
    
    /**
     * Buscar usuários com autenticação
     */
    async buscarUsuarios() {
        try {
            const response = await fetch(`${this.OFFLINE_API}/usuarios`, {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[OfflineManager] 👥 Usuários carregados:', data.data?.length || 0);
                return data.data || [];
            }
        } catch (error) {
            console.warn('[OfflineManager] Erro ao buscar usuários:', error);
        }
        return [];
    }
    
    /**
     * Buscar inscrições com autenticação
     */
    async buscarInscricoes() {
        try {
            const response = await fetch(`${this.OFFLINE_API}/inscricoes`, {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[OfflineManager] 📝 Inscrições carregadas:', data.data?.length || 0);
                return data.data || [];
            }
        } catch (error) {
            console.warn('[OfflineManager] Erro ao buscar inscrições:', error);
        }
        return [];
    }
    
    /**
     * Buscar presenças com autenticação
     */
    async buscarPresencas() {
        try {
            const response = await fetch(`${this.OFFLINE_API}/presencas`, {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[OfflineManager] ✋ Presenças carregadas:', data.data?.length || 0);
                return data.data || [];
            }
        } catch (error) {
            console.warn('[OfflineManager] Erro ao buscar presenças:', error);
        }
        return [];
    }
    
    /**
     * Carregar eventos das APIs
     */
    async carregarEventos() {
        console.log('[OfflineManager] 📋 Carregando eventos...');
        
        try {
            // Tentar Laravel primeiro
            const responseLaravel = await fetch(`${this.API_BASE}/eventos`);
            if (responseLaravel.ok) {
                const dataLaravel = await responseLaravel.json();
                if (dataLaravel && dataLaravel.length > 0) {
                    console.log(`[OfflineManager] ✅ ${dataLaravel.length} eventos do Laravel`);
                    localStorage.setItem('eventos_cache', JSON.stringify(dataLaravel));
                    return dataLaravel;
                }
            }
        } catch (error) {
            console.warn('[OfflineManager] Laravel falhou:', error.message);
        }
        
        try {
            // Tentar Python MySQL
            const responsePython = await fetch(`${this.OFFLINE_API}/eventos`);
            if (responsePython.ok) {
                const dataPython = await responsePython.json();
                if (dataPython.success && dataPython.data && dataPython.data.length > 0) {
                    console.log(`[OfflineManager] ✅ ${dataPython.data.length} eventos do Python`);
                    localStorage.setItem('eventos_cache', JSON.stringify(dataPython.data));
                    return dataPython.data;
                }
            }
        } catch (error) {
            console.warn('[OfflineManager] Python falhou:', error.message);
        }
        
        // Tentar cache localStorage
        const cached = localStorage.getItem('eventos_cache');
        if (cached) {
            const eventos = JSON.parse(cached);
            console.log(`[OfflineManager] ✅ ${eventos.length} eventos do cache`);
            return eventos;
        }
        
        console.log('[OfflineManager] ⚠️ Usando eventos de exemplo');
        return this.getEventosExemplo();
    }
    
    /**
     * Carregar dados do localStorage
     */
    carregarDadosDoStorage() {
        try {
            const dados = {
                usuarios: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.USUARIOS) || '[]'),
                eventos: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.EVENTOS) || '[]'),
                inscricoes: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.INSCRICOES) || '[]'),
                presencas: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.PRESENCAS) || '[]'),
                filaSincronizacao: JSON.parse(localStorage.getItem(this.STORAGE_KEYS.FILA_SINCRONIZACAO) || '[]')
            };
            
            this.dados = dados;
            
            console.log('[OfflineManager] 💾 Dados do localStorage:', {
                usuarios: dados.usuarios.length,
                eventos: dados.eventos.length,
                inscricoes: dados.inscricoes.length,
                presencas: dados.presencas.length,
                pendentes: dados.filaSincronizacao.length
            });
            
            return dados;
            
        } catch (error) {
            console.error('[OfflineManager] ❌ Erro ao carregar localStorage:', error);
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
            
            console.log('[OfflineManager] 💾 Dados salvos no localStorage');
        } catch (error) {
            console.error('[OfflineManager] ❌ Erro ao salvar no localStorage:', error);
        }
    }
    
    /**
     * Marcar presença offline
     */
    async marcarPresencaOffline(inscricaoId, eventoId, usuarioId) {
        console.log(`[OfflineManager] ✋ Marcando presença: inscricao=${inscricaoId}, evento=${eventoId}`);
        
        try {
            // Tentar registrar no servidor primeiro
            const response = await fetch(`${this.OFFLINE_API}/presencas`, {
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
                console.log('[OfflineManager] ✅ Presença registrada no servidor:', data);
                
                // Também salvar localmente
                this.adicionarPresencaLocal(inscricaoId, eventoId, usuarioId);
                
                return {
                    success: true,
                    message: 'Presença registrada com sucesso',
                    servidor: true
                };
            }
        } catch (error) {
            console.warn('[OfflineManager] ⚠️ Servidor indisponível, salvando localmente:', error);
        }
        
        // Se falhou no servidor, salvar apenas localmente
        this.adicionarPresencaLocal(inscricaoId, eventoId, usuarioId);
        
        return {
            success: true,
            message: 'Presença salva localmente (será sincronizada quando possível)',
            servidor: false
        };
    }
    
    /**
     * Adicionar presença ao localStorage
     */
    adicionarPresencaLocal(inscricaoId, eventoId, usuarioId) {
        let presencasOffline = JSON.parse(localStorage.getItem('presencas_offline') || '[]');
        
        // Verificar se já existe
        const existePresenca = presencasOffline.find(p => p.inscricao_id === inscricaoId);
        if (existePresenca) {
            console.log('[OfflineManager] ⚠️ Presença já existe localmente');
            return;
        }
        
        // Adicionar nova presença
        const novaPresenca = {
            id: `offline_${Date.now()}`,
            inscricao_id: inscricaoId,
            evento_id: eventoId,
            usuario_id: usuarioId,
            data_presenca: new Date().toISOString(),
            sincronizado: false
        };
        
        presencasOffline.push(novaPresenca);
        localStorage.setItem('presencas_offline', JSON.stringify(presencasOffline));
        
        // Atualizar dados em memória
        this.dados.presencas.push(novaPresenca);
        
        console.log('[OfflineManager] ✅ Presença salva no localStorage:', novaPresenca);
        
        this.callbacks.onPresencaRegistrada({
            presenca: novaPresenca,
            offline: true
        });
    }
    
    /**
     * Sincronizar presenças offline
     */
    async sincronizarPresencas() {
        console.log('[OfflineManager] 🔄 Sincronizando presenças...');
        
        const presencasOffline = JSON.parse(localStorage.getItem('presencas_offline') || '[]');
        const presencasNaoSincronizadas = presencasOffline.filter(p => !p.sincronizado);
        
        if (presencasNaoSincronizadas.length === 0) {
            console.log('[OfflineManager] ✅ Nenhuma presença para sincronizar');
            return {
                sucesso: true,
                sincronizadas: 0,
                message: 'Nenhuma presença pendente'
            };
        }
        
        console.log(`[OfflineManager] 📤 Sincronizando ${presencasNaoSincronizadas.length} presenças...`);
        
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
                        inscricao_id: presenca.inscricao_id,
                        evento_id: presenca.evento_id,
                        usuario_id: presenca.usuario_id
                    })
                });
                
                if (response.ok) {
                    presenca.sincronizado = true;
                    sincronizadas++;
                    console.log(`[OfflineManager] ✅ Presença ${presenca.inscricao_id} sincronizada`);
                } else {
                    console.warn(`[OfflineManager] ⚠️ Falha ao sincronizar presença ${presenca.inscricao_id}`);
                    erros.push(presenca.inscricao_id);
                }
                
            } catch (error) {
                console.error(`[OfflineManager] ❌ Erro ao sincronizar presença ${presenca.inscricao_id}:`, error);
                erros.push(presenca.inscricao_id);
            }
        }
        
        // Atualizar localStorage
        localStorage.setItem('presencas_offline', JSON.stringify(presencasOffline));
        
        const resultado = {
            sucesso: true,
            sincronizadas: sincronizadas,
            total: presencasNaoSincronizadas.length,
            erros: erros,
            message: `${sincronizadas} presenças sincronizadas`
        };
        
        console.log(`[OfflineManager] ✅ Sincronização completa:`, resultado);
        
        this.callbacks.onSyncEnd(resultado);
        return resultado;
    }
    
    /**
     * Obter usuário de teste para operações offline
     */
    getUsuarioOffline() {
        let usuario = JSON.parse(localStorage.getItem('usuario_offline_teste') || 'null');
        
        if (!usuario) {
            console.log('[OfflineManager] 👤 Criando usuário de teste...');
            usuario = {
                id: 999,
                nome: "Usuário Offline",
                email: "offline@teste.com",
                cpf: "00000000000",
                telefone: "(51)99999-9999",
                criado_em: new Date().toISOString()
            };
            
            localStorage.setItem('usuario_offline_teste', JSON.stringify(usuario));
            console.log('[OfflineManager] ✅ Usuário de teste criado:', usuario);
        }
        
        return usuario;
    }
    
    /**
     * Eventos de exemplo para fallback
     */
    getEventosExemplo() {
        return [
            {
                id: 1,
                nome: "Workshop Laravel",
                titulo: "Workshop Laravel", 
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
                nome: "Palestra Docker",
                titulo: "Palestra Docker",
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
                nome: "Curso JavaScript",
                titulo: "Curso JavaScript",
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
     * Obter estatísticas dos dados carregados
     */
    obterEstatisticas() {
        return {
            usuarios: this.dados.usuarios?.length || 0,
            eventos: this.dados.eventos?.length || 0,
            inscricoes: this.dados.inscricoes?.length || 0,
            presencas: this.dados.presencas?.length || 0,
            pendentes: this.dados.filaSincronizacao?.length || 0,
            token: this.SISTEMA_TOKEN ? '✅' : '❌'
        };
    }

    /**
     * Obter inscrições por evento
     */
    obterInscricoesPorEvento(eventoId) {
        if (!this.dados.inscricoes) return [];
        
        return this.dados.inscricoes.filter(inscricao => 
            inscricao.evento_id == eventoId && 
            ['confirmada', 'presente'].includes(inscricao.status)
        );
    }

    /**
     * Obter usuário por ID
     */
    obterUsuario(usuarioId) {
        if (!this.dados.usuarios) return null;
        
        return this.dados.usuarios.find(usuario => 
            usuario.id === parseInt(usuarioId)
        );
    }

    /**
     * Verificar se já existe presença para uma inscrição
     */
    temPresenca(inscricaoId) {
        if (!this.dados.presencas) return false;
        
        return this.dados.presencas.some(presenca => 
            presenca.inscricao_id === parseInt(inscricaoId)
        );
    }

    /**
     * Obter inscrição por ID
     */
    obterInscricao(inscricaoId) {
        if (!this.dados.inscricoes) return null;
        
        return this.dados.inscricoes.find(inscricao => 
            inscricao.id === parseInt(inscricaoId)
        );
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.OfflineManager = OfflineManager;
}