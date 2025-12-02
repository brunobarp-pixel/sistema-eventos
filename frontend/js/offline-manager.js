class OfflineManager {
    constructor(config = {}) {
        this.API_BASE = config.apiBase || 'http://177.44.248.118:8000/api';
        this.OFFLINE_API = config.offlineApi || 'http://177.44.248.118:5000';
        this.timeout = config.timeout || 5000;
        
        this.callbacks = {
            onStatusChange: config.onStatusChange || (() => {}),
            onDataLoaded: config.onDataLoaded || (() => {}),
            onPresencaRegistrada: config.onPresencaRegistrada || (() => {}),
            onSyncStart: config.onSyncStart || (() => {}),
            onSyncEnd: config.onSyncEnd || (() => {}),
            onSyncError: config.onSyncError || (() => {})
        };
        
        this.isOnline = true;
        this.dados = {
            usuarios: [],
            eventos: [],
            inscricoes: [],
            presencas: [],
            filaSincronizacao: []
        };
        
        this.STORAGE_KEYS = {
            USUARIOS: 'offline_usuarios',
            EVENTOS: 'offline_eventos', 
            INSCRICOES: 'offline_inscricoes',
            PRESENCAS: 'offline_presencas',
            FILA_SINCRONIZACAO: 'offline_fila_sync',
            SISTEMA_TOKEN: 'sistema_offline_token'
        };
        
        this.SISTEMA_TOKEN = null;
        this.inicializandoToken = false;
        
        console.log('Inicializado em modo simplificado');
        console.log('Use await offlineManager.inicializar() para configurar tokens automaticamente');
    }

    async inicializar() {
        if (this.inicializandoToken) {
            console.log('Inicialização já em andamento...');
            return false;
        }
        
        try {
            this.inicializandoToken = true;
            console.log('Inicializando sistema offline...');
            
            const token = await this.obterTokenSistema();
            if (token) {
                console.log('Sistema inicializado com token válido');
            } else {
                console.warn('Sistema inicializado sem token - funcionalidade limitada');
            }
            
            if (this.modoOfflineEstatico) {
                await this.carregarDadosOfflineEstatico();
            }
            
            return true;
            
        } catch (error) {
            console.error('Erro na inicialização:', error);
            return false;
        } finally {
            this.inicializandoToken = false;
        }
    }
    

    async obterTokenSistema() {
        try {
            const tokenArmazenado = localStorage.getItem(this.STORAGE_KEYS.SISTEMA_TOKEN);
            if (tokenArmazenado) {
                if (await this.validarToken(tokenArmazenado)) {
                    this.SISTEMA_TOKEN = tokenArmazenado;
                    console.log('Token do sistema recuperado e validado');
                    return tokenArmazenado;
                } else {
                    console.warn('Token armazenado expirado, obtendo novo...');
                    localStorage.removeItem(this.STORAGE_KEYS.SISTEMA_TOKEN);
                }
            }
            
            console.log('Tentando obter token do Laravel...');
            const laravelToken = await this.obterTokenDoLaravel();
            if (laravelToken) {
                this.SISTEMA_TOKEN = laravelToken;
                localStorage.setItem(this.STORAGE_KEYS.SISTEMA_TOKEN, laravelToken);
                console.log('Token obtido do Laravel');
                return laravelToken;
            }
            
            // Fallback para servidor Python
            console.log('Fallback: obtendo token do Python...');
            const pythonToken = await this.obterTokenDoPython();
            if (pythonToken) {
                this.SISTEMA_TOKEN = pythonToken;
                localStorage.setItem(this.STORAGE_KEYS.SISTEMA_TOKEN, pythonToken);
                console.log('Token obtido do Python');
                return pythonToken;
            }
            
            console.error('Falha ao obter token de qualquer fonte');
            return null;
            
        } catch (error) {
            console.error('Erro ao obter token do sistema:', error);
            return null;
        }
    }

    async validarToken(token) {
        try {
            const response = await fetch(`${this.OFFLINE_API}/validar-token`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            return response.ok;
        } catch (error) {
            console.warn('Erro ao validar token:', error);
            return false;
        }
    }

    async obterTokenDoLaravel() {
        try {
            const response = await fetch('http://177.44.248.118:8000/api/auth/sistema-token');
            if (response.ok) {
                const data = await response.json();
                console.log('Token Laravel obtido:', data.user?.name);
                return data.token;
            }
        } catch (error) {
            console.warn('Erro ao obter token do Laravel:', error);
        }
        return null;
    }

    async obterTokenDoPython() {
        try {
            const response = await fetch(`${this.OFFLINE_API}/sistema-token`);
            if (response.ok) {
                const data = await response.json();
                console.log('Token Python obtido:', data.usuario?.nome);
                return data.token;
            }
        } catch (error) {
            console.warn('Erro ao obter token do Python:', error);
        }
        return null;
    }

    async getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (!this.SISTEMA_TOKEN && !this.inicializandoToken) {
            console.log('Token não encontrado, tentando obter');
            await this.obterTokenSistema();
        }
        
        if (this.SISTEMA_TOKEN) {
            headers['Authorization'] = `Bearer ${this.SISTEMA_TOKEN}`;
        } else {
            console.warn('Nenhum token disponível para autenticação');
        }
        
        return headers;
    }

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
            
            console.log(`Status: ${this.isOnline ? 'ONLINE' : 'OFFLINE'}`);
            return this.isOnline;
            
        } catch (error) {
            this.isOnline = false;
            this.callbacks.onStatusChange(false);
            console.log('Status: OFFLINE (erro de conexão)');
            return false;
        }
    }
    
  
    async carregarTodosDados() {
        console.log('Carregando dados...');
        
        try {
            await this.obterTokenSistema();
            
            await this.verificarConexao();
            
            const eventos = await this.carregarEventos();
            
            const dadosLocal = this.carregarDadosDoStorage();
            
            let usuarios = [];
            let inscricoes = [];
            let presencas = [];
            
            if (this.SISTEMA_TOKEN && this.isOnline) {
                try {
                    console.log('Carregando dados com token do sistema...');
                    [usuarios, inscricoes, presencas] = await Promise.all([
                        this.buscarUsuarios(),
                        this.buscarInscricoes(), 
                        this.buscarPresencas()
                    ]);
                } catch (authError) {
                    console.warn('Erro ao carregar dados autenticados:', authError);
                    usuarios = dadosLocal.usuarios || [];
                    inscricoes = dadosLocal.inscricoes || [];
                    presencas = dadosLocal.presencas || [];
                }
            } else {
                console.log('Usando dados do localStorage...');
                usuarios = dadosLocal.usuarios || [];
                inscricoes = dadosLocal.inscricoes || [];
                presencas = dadosLocal.presencas || [];
            }
            
            this.dados = {
                usuarios,
                eventos: eventos.length > 0 ? eventos : dadosLocal.eventos || this.getEventosExemplo(),
                inscricoes,
                presencas,
                filaSincronizacao: dadosLocal.filaSincronizacao || []
            };
            
            this.salvarDadosNoStorage();
            
            console.log('Dados carregados:', {
                usuarios: this.dados.usuarios.length,
                eventos: this.dados.eventos.length,
                inscricoes: this.dados.inscricoes.length,
                presencas: this.dados.presencas.length,
                token: this.SISTEMA_TOKEN ? 'SIM' : 'NEGATUVO'
            });
            
            this.callbacks.onDataLoaded(this.dados);
            return this.dados;
            
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
            
            this.carregarDadosDoStorage();
            
            if (this.dados.eventos.length === 0) {
                this.dados.eventos = this.getEventosExemplo();
            }
            
            this.callbacks.onDataLoaded(this.dados);
            return this.dados;
        }
    }
    
 
    async buscarUsuarios() {
        try {
            const headers = await this.getAuthHeaders();
            const response = await fetch(`${this.OFFLINE_API}/usuarios`, {
                headers: headers
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Usuários carregados:', data.data?.length || 0);
                return data.data || [];
            }
        } catch (error) {
            console.warn('Erro ao buscar usuários:', error);
        }
        return [];
    }

    async buscarInscricoes() {
        try {
            const headers = await this.getAuthHeaders();
            const response = await fetch(`${this.OFFLINE_API}/inscricoes`, {
                headers: headers
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Inscrições carregadas:', data.data?.length || 0);
                return data.data || [];
            }
        } catch (error) {
            console.warn('Erro ao buscar inscrições:', error);
        }
        return [];
    }
    

    async buscarPresencas() {
        try {
            const headers = await this.getAuthHeaders();
            const response = await fetch(`${this.OFFLINE_API}/presencas`, {
                headers: headers
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Presenças carregadas:', data.data?.length || 0);
                return data.data || [];
            }
        } catch (error) {
            console.warn('Erro ao buscar presenças:', error);
        }
        return [];
    }
    
    /**
     * Carregar eventos das APIs
     */
    async carregarEventos() {
        console.log('Carregando eventos...');
        
        try {
            // Tentar Laravel primeiro
            const responseLaravel = await fetch(`${this.API_BASE}/eventos`);
            if (responseLaravel.ok) {
                const dataLaravel = await responseLaravel.json();
                if (dataLaravel && dataLaravel.length > 0) {
                    console.log(`Questao offline: ${dataLaravel.length} eventos do Laravel`);
                    localStorage.setItem('eventos_cache', JSON.stringify(dataLaravel));
                    return dataLaravel;
                }
            }
        } catch (error) {
            console.warn('Laravel falhou:', error.message);
        }
        
        try {
            // Tentar Python MySQL
            const responsePython = await fetch(`${this.OFFLINE_API}/eventos`);
            if (responsePython.ok) {
                const dataPython = await responsePython.json();
                if (dataPython.success && dataPython.data && dataPython.data.length > 0) {
                    console.log(`Questao offline: ${dataPython.data.length} eventos do Python`);
                    localStorage.setItem('eventos_cache', JSON.stringify(dataPython.data));
                    return dataPython.data;
                }
            }
        } catch (error) {
            console.warn('[OfflineManager] Python falhou:', error.message);
        }
        
        const cached = localStorage.getItem('eventos_cache');
        if (cached) {
            const eventos = JSON.parse(cached);
            console.log(`${eventos.length} eventos do cache`);
            return eventos;
        }
        
        console.log('Usando eventos de exemplo');
        return this.getEventosExemplo();
    }
    

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
            
            console.log('Dados do localStorage:', {
                usuarios: dados.usuarios.length,
                eventos: dados.eventos.length,
                inscricoes: dados.inscricoes.length,
                presencas: dados.presencas.length,
                pendentes: dados.filaSincronizacao.length
            });
            
            return dados;
            
        } catch (error) {
            console.error('Erro ao carregar localStorage:', error);
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

    salvarDadosNoStorage() {
        try {
            localStorage.setItem(this.STORAGE_KEYS.USUARIOS, JSON.stringify(this.dados.usuarios));
            localStorage.setItem(this.STORAGE_KEYS.EVENTOS, JSON.stringify(this.dados.eventos));
            localStorage.setItem(this.STORAGE_KEYS.INSCRICOES, JSON.stringify(this.dados.inscricoes));
            localStorage.setItem(this.STORAGE_KEYS.PRESENCAS, JSON.stringify(this.dados.presencas));
            localStorage.setItem(this.STORAGE_KEYS.FILA_SINCRONIZACAO, JSON.stringify(this.dados.filaSincronizacao));
            
            console.log('Dados salvos no localStorage');
        } catch (error) {
            console.error('Erro ao salvar no localStorage:', error);
        }
    }
    

    async marcarPresencaOffline(inscricaoId, eventoId, usuarioId) {
        console.log(`Marcando presença: inscricao=${inscricaoId}, evento=${eventoId}, usuario=${usuarioId}`);
        
        try {
            console.log(`Tentando conectar com: ${this.OFFLINE_API}/presencas`);
            
            const requestBody = {
                inscricao_id: inscricaoId,
                evento_id: eventoId,
                usuario_id: usuarioId
            };
            console.log(`Enviando dados:`, requestBody);
            
            const headers = await this.getAuthHeaders();
            headers['Content-Type'] = 'application/json';
            
            const response = await fetch(`${this.OFFLINE_API}/presencas`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody)
            });
            
            console.log(`Response status: ${response.status}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Presença registrada no servidor:', data);
                
                // Também salvar localmente
                this.adicionarPresencaLocal(inscricaoId, eventoId, usuarioId);
                
                return {
                    success: true,
                    message: 'Presença registrada com sucesso',
                    servidor: true,
                    data: data
                };
            } else {
                const errorText = await response.text();
                console.error(`Erro HTTP ${response.status}:`, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
        } catch (error) {
            console.warn('Servidor indisponível, salvando localmente:', error);
        }
        
        this.adicionarPresencaLocal(inscricaoId, eventoId, usuarioId);
        
        return {
            success: true,
            message: 'Presença salva localmente (será sincronizada quando possível)',
            servidor: false
        };
    }
    

    adicionarPresencaLocal(inscricaoId, eventoId, usuarioId) {
        let presencasOffline = JSON.parse(localStorage.getItem('presencas_offline') || '[]');
        
        const existePresenca = presencasOffline.find(p => p.inscricao_id === inscricaoId);
        if (existePresenca) {
            console.log('Presença já existe localmente');
            return;
        }
        
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
        
        this.dados.presencas.push(novaPresenca);
        
        console.log('Presença salva no localStorage:', novaPresenca);
        
        this.callbacks.onPresencaRegistrada({
            presenca: novaPresenca,
            offline: true
        });
    }
    
  
    async sincronizarPresencas() {
        console.log('Sincronizando presenças...');
        
        const presencasOffline = JSON.parse(localStorage.getItem('presencas_offline') || '[]');
        const presencasNaoSincronizadas = presencasOffline.filter(p => !p.sincronizado);
        
        if (presencasNaoSincronizadas.length === 0) {
            console.log('Nenhuma presença para sincronizar');
            return {
                sucesso: true,
                sincronizadas: 0,
                message: 'Nenhuma presença pendente'
            };
        }
        
        console.log(`Sincronizando ${presencasNaoSincronizadas.length} presenças...`);
        
        let sincronizadas = 0;
        const erros = [];
        
        for (const presenca of presencasNaoSincronizadas) {
            console.log(this.OFFLINE_API)
            try {
                const headers = await this.getAuthHeaders();
                headers['Content-Type'] = 'application/json';
                
                const response = await fetch(`${this.OFFLINE_API}/presencas`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({
                        inscricao_id: presenca.inscricao_id,
                        evento_id: presenca.evento_id,
                        usuario_id: presenca.usuario_id
                    })
                });
                
                if (response.ok) {
                    presenca.sincronizado = true;
                    sincronizadas++;
                    console.log(`Presença ${presenca.inscricao_id} sincronizada`);
                } else {
                    console.warn(`Falha ao sincronizar presença ${presenca.inscricao_id}`);
                    erros.push(presenca.inscricao_id);
                }
                
            } catch (error) {
                console.error(`Erro ao sincronizar presença ${presenca.inscricao_id}:`, error);
                erros.push(presenca.inscricao_id);
            }
        }
        
        localStorage.setItem('presencas_offline', JSON.stringify(presencasOffline));
        
        const resultado = {
            sucesso: true,
            sincronizadas: sincronizadas,
            total: presencasNaoSincronizadas.length,
            erros: erros,
            message: `${sincronizadas} presenças sincronizadas`
        };
        
        console.log(`Sincronização completa:`, resultado);
        
        this.callbacks.onSyncEnd(resultado);
        return resultado;
    }
    

    getUsuarioOffline() {
        let usuario = JSON.parse(localStorage.getItem('usuario_offline_teste') || 'null');
        
        if (!usuario) {
            console.log('Criando usuário de teste...');
            usuario = {
                id: 999,
                nome: "Usuário Offline",
                email: "offline@teste.com",
                cpf: "00000000000",
                telefone: "(51)99999-9999",
                criado_em: new Date().toISOString()
            };
            
            localStorage.setItem('usuario_offline_teste', JSON.stringify(usuario));
            console.log('Usuário de teste criado:', usuario);
        }
        
        return usuario;
    }
    

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

 
    obterEstatisticas() {
        return {
            usuarios: this.dados.usuarios?.length || 0,
            eventos: this.dados.eventos?.length || 0,
            inscricoes: this.dados.inscricoes?.length || 0,
            presencas: this.dados.presencas?.length || 0,
            pendentes: this.dados.filaSincronizacao?.length || 0,
            token: this.SISTEMA_TOKEN ? 'POSITIVO' : 'NEGATIVO'
        };
    }


    obterInscricoesPorEvento(eventoId) {
        if (!this.dados.inscricoes) return [];
        
        return this.dados.inscricoes.filter(inscricao => 
            inscricao.evento_id == eventoId && 
            ['confirmada', 'presente'].includes(inscricao.status)
        );
    }


    obterUsuario(usuarioId) {
        if (!this.dados.usuarios) return null;
        
        return this.dados.usuarios.find(usuario => 
            usuario.id === parseInt(usuarioId)
        );
    }

 
    temPresenca(inscricaoId) {
        if (!this.dados.presencas) return false;
        
        return this.dados.presencas.some(presenca => 
            presenca.inscricao_id === parseInt(inscricaoId)
        );
    }


    obterInscricao(inscricaoId) {
        if (!this.dados.inscricoes) return null;
        
        return this.dados.inscricoes.find(inscricao => 
            inscricao.id === parseInt(inscricaoId)
        );
    }
}

if (typeof window !== 'undefined') {
    window.OfflineManager = OfflineManager;
}