# 📦 GUIA COMPLETO - Deploy Sistema de Eventos na VM 177.44.248.118

**Versão:** 1.0.0  
**Data:** 29 de Novembro de 2025  
**Status:** ✅ Pronto para Produção  
**IP da VM:** 177.44.248.118

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [O Que Foi Criado](#o-que-foi-criado)
3. [Como Usar](#como-usar)
4. [Passo a Passo Completo](#passo-a-passo-completo)
5. [Troubleshooting](#troubleshooting)
6. [Referência de Comandos](#referência-de-comandos)

---

## 🎯 Visão Geral

Este projeto é um **Sistema de Eventos Completo** containerizado com Docker contendo:

- **Frontend**: HTML5/JavaScript + Bootstrap (Nginx)
- **Backend Laravel**: PHP 8.2 + Apache (API REST)
- **Backend Python**: Python 3.11 + Flask (Serviços complementares)
- **Database**: MySQL 8.0
- **Cache**: Redis 7
- **Email Testing**: Mailhog
- **Modo Offline**: localStorage com sincronização

**Arquitetura:**
```
┌─────────────────────────────────────────────┐
│              FRONTEND (Nginx)               │
│       http://177.44.248.118:80              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────┐  ┌──────────────────┐│
│  │ Backend Laravel  │  │ Backend Python   ││
│  │ (PHP 8.2)        │  │ (Python 3.11)    ││
│  │ :8000            │  │ :5000            ││
│  └────────┬─────────┘  └────────┬─────────┘│
│           │                     │           │
│           └──────────┬──────────┘           │
│                      │                     │
│  ┌────────────────────────────────────────┐│
│  │      MySQL Database + Redis Cache      ││
│  │         (3306 / 6379)                  ││
│  └────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

---

## 📦 O Que Foi Criado

### Scripts de Deployment

| Arquivo | Descrição | Locação |
|---------|-----------|---------|
| `deploy.sh` | Script principal com 20+ comandos de deploy | Raiz |
| `install.sh` | Instalação automatizada na VM | Raiz |
| `checklist.sh` | Verificações de pré/pós deployment | Raiz |
| `remote_deploy.py` | Interface interativa de deploy (Python) | Raiz |

### Documentação

| Arquivo | Descrição | Locação |
|---------|-----------|---------|
| `REMOTE_DEPLOYMENT.md` | Guia completo de deployment (30 min) | Raiz |
| `QUICK_START_VM.md` | Guia rápido (5 min) | Raiz |
| `DEPLOYMENT_CHECKLIST.md` | Lista de verificação | Raiz |
| `README_OFFLINE.md` | Sistema offline | Raiz |
| `EXECUTIVE_SUMMARY.md` | Resumo executivo | Raiz |

### Docker Files

| Arquivo | Descrição | Serviço |
|---------|-----------|---------|
| `docker-compose.yml` | Orquestração de 4 containers + suporte | Raiz |
| `backend/Dockerfile` | PHP 8.2 Apache | Backend Laravel |
| `backend-python/Dockerfile` | Python 3.11 | Backend Python |
| `frontend/Dockerfile` | Multi-stage Node + Nginx | Frontend |

### Configuração

| Arquivo | Descrição | Locação |
|---------|-----------|---------|
| `backend/.env.production` | Variáveis de produção | backend/ |
| `frontend/default.conf` | Nginx server config | frontend/ |
| `frontend/nginx.conf` | Nginx main config | frontend/ |
| `.env` | Variáveis gerais | Raiz |

---

## 🚀 Como Usar

### Opção 1: Instalação Automatizada (Recomendada)

**Na sua máquina local:**
```bash
# Abra PowerShell ou Terminal
ssh ssh@177.44.248.118
# Senha: FsT#8723S

# Depois, execute na VM:
bash <(curl -fsSL https://bit.ly/instalar-sistema-eventos)
```

**Ou manualmente:**
```bash
# SSH na VM
ssh ssh@177.44.248.118

# Clonar e instalar
git clone https://github.com/brunobarp-pixel/sistema-eventos.git
cd sistema-eventos
bash install.sh

# Deploy
./deploy.sh deploy
```

### Opção 2: Deploy via Script Python (Local)

```bash
# Na sua máquina local
python remote_deploy.py

# Será exibido menu interativo
```

### Opção 3: Verificação Pré-Deployment

```bash
# Na VM
bash checklist.sh

# Escolha opção 1, 2 ou 3 para verificar
```

---

## 📝 Passo a Passo Completo

### Fase 1: Preparação (5 min)

```bash
# 1. SSH na VM
ssh ssh@177.44.248.118

# Senha: FsT#8723S
```

### Fase 2: Instalação (10 min)

```bash
# 2. Dentro da VM, executar instalação
cd ~ && bash <(curl -fsSL https://raw.githubusercontent.com/brunobarp-pixel/sistema-eventos/main/install.sh)

# Ou, se preferir manual:
git clone https://github.com/brunobarp-pixel/sistema-eventos.git
cd sistema-eventos
bash install.sh

# 3. Verificar instalação
docker --version
docker-compose --version
```

### Fase 3: Deploy (15 min)

```bash
# 4. Dentro de ~/projetos/sistema-eventos
./deploy.sh deploy

# Isso faz:
# ✓ Build das imagens (5-8 min)
# ✓ Inicia containers (2-3 min)
# ✓ Migra banco (1-2 min)
# ✓ Limpa caches (1 min)
# ✓ Verifica saúde (automático)
```

### Fase 4: Verificação (5 min)

```bash
# 5. Verificar status
./deploy.sh status

# Deve mostrar 5 containers:
# ✓ database
# ✓ redis
# ✓ backend-laravel
# ✓ backend-python
# ✓ frontend

# 6. Health check
./deploy.sh health

# Deve mostrar todos "online"
```

### Fase 5: Acesso (1 min)

```bash
# Abrir no navegador:
# http://177.44.248.118

# Funcionalidades:
# - http://177.44.248.118/offline.html (Modo Offline)
# - http://177.44.248.118:8025 (Mailhog - emails)
```

---

## 🔍 Troubleshooting

### ❌ Erro: "Connection refused"

**Causa:** Containers não iniciaram corretamente

**Solução:**
```bash
# Ver logs
./deploy.sh logs

# Reiniciar
./deploy.sh restart

# Ou, fazer deploy limpo
./deploy.sh stop
./deploy.sh clean
./deploy.sh deploy
```

### ❌ Erro: "Port already in use"

**Causa:** Porta 80/8000/5000 já está em uso

**Solução:**
```bash
# Encontrar processo
sudo lsof -i :80

# Matar processo
kill -9 [PID]

# Ou, modificar docker-compose.yml
```

### ❌ Erro: "Database connection failed"

**Causa:** MySQL não iniciou ou variáveis de ambiente erradas

**Solução:**
```bash
# Resetar banco
./deploy.sh fresh

# Ou, resetar tudo
./deploy.sh stop
rm -rf backups/
./deploy.sh deploy
```

### ❌ Frontend carrega mas sem CSS/JS

**Causa:** Nginx não serve arquivos estáticos corretamente

**Solução:**
```bash
# Reiniciar frontend
docker-compose restart frontend

# Verificar logs
./deploy.sh logs frontend
```

### ❌ API retorna 502 Bad Gateway

**Causa:** Backend Laravel não está respondendo

**Solução:**
```bash
# Reiniciar Laravel
docker-compose restart backend-laravel

# Ver erro
./deploy.sh logs backend-laravel

# Se persistir, fazer fresh
./deploy.sh fresh
```

---

## 📚 Referência de Comandos

### Deploy
```bash
./deploy.sh deploy          # Deploy completo (recomendado)
./deploy.sh build           # Build das imagens
./deploy.sh start           # Iniciar
./deploy.sh stop            # Parar
./deploy.sh restart         # Reiniciar
./deploy.sh status          # Ver status
```

### Banco de Dados
```bash
./deploy.sh migrate         # Executar migrações
./deploy.sh seed            # Seedar dados
./deploy.sh fresh           # Fresh + seed (DELETA DADOS!)
./deploy.sh backup          # Fazer backup
./deploy.sh restore <file>  # Restaurar backup
```

### Manutenção
```bash
./deploy.sh logs            # Ver todos os logs
./deploy.sh logs <service>  # Ver logs específicos
./deploy.sh health          # Health check
./deploy.sh cache-clear     # Limpar caches
./deploy.sh storage-link    # Link de storage
```

### Executar Comandos
```bash
./deploy.sh exec backend-laravel php artisan tinker
./deploy.sh exec backend-laravel php artisan route:list
./deploy.sh exec database mysql -u root -p sistema_eventos
```

---

## 🔐 Credenciais Padrão

| Serviço | Usuário | Senha | Host |
|---------|---------|-------|------|
| **SSH VM** | ssh | FsT#8723S | 177.44.248.118 |
| **MySQL** | eventos_user | eventos_pass_123 | localhost:3306 |
| **MySQL Root** | root | root_password_123 | localhost:3306 |
| **Redis** | (sem auth) | - | localhost:6379 |
| **Mailhog** | (sem auth) | - | localhost:8025 |

---

## 🌐 URLs da Aplicação

| Página | URL |
|--------|-----|
| **Home** | http://177.44.248.118 |
| **Offline** | http://177.44.248.118/offline.html |
| **Eventos** | http://177.44.248.118/eventos.html |
| **Inscrições** | http://177.44.248.118/inscricoes.html |
| **Presença** | http://177.44.248.118/cadastro.html |
| **Certificados** | http://177.44.248.118/certificados.html |
| **API Status** | http://177.44.248.118/api/status |
| **Mailhog** | http://177.44.248.118:8025 |

---

## 💾 Backup & Restauração

### Backup Manual
```bash
cd ~/projetos/sistema-eventos

# Fazer backup
./deploy.sh backup

# Listar backups
ls -lh backups/
```

### Restaurar Backup
```bash
# Restaurar específico
./deploy.sh restore backup_20251129_143022.sql

# Ou manualmente
docker-compose exec -T database mysql -u eventos_user -p sistema_eventos < backups/backup_20251129_143022.sql
```

---

## 📊 Monitoramento

### Ver Recursos em Tempo Real
```bash
docker stats
```

### Logs Persistentes
```bash
# Laravel
docker-compose exec backend-laravel tail -f storage/logs/laravel.log

# Python
docker-compose exec backend-python tail -f app.log

# Nginx
docker-compose logs -f frontend
```

---

## 🔄 Atualizações

### Atualizar Código
```bash
cd ~/projetos/sistema-eventos

# Buscar atualizações
git pull origin main

# Reconstruir imagens
./deploy.sh build

# Reiniciar
./deploy.sh restart
```

---

## 📞 Suporte Rápido

**Problema com deployment?**
1. Execute: `./deploy.sh logs`
2. Procure por erro nos logs
3. Tente: `./deploy.sh restart`
4. Se persistir: `./deploy.sh fresh`

**Precisa de mais ajuda?**
- Leia: `REMOTE_DEPLOYMENT.md` (guia detalhado)
- Leia: `QUICK_START_VM.md` (guia rápido)
- Use: `./deploy.sh help`

---

## 📅 Checklist Pós-Deploy

- [ ] Acessar http://177.44.248.118
- [ ] Verificar página inicial
- [ ] Testar login
- [ ] Verificar API: http://177.44.248.118/api/status
- [ ] Executar: `./deploy.sh health`
- [ ] Fazer: `./deploy.sh backup`
- [ ] Configurar HTTPS (opcional, veja REMOTE_DEPLOYMENT.md)
- [ ] Configurar firewall (opcional)

---

## 📚 Documentos Complementares

- **REMOTE_DEPLOYMENT.md** - Guia detalhado (30 min)
- **QUICK_START_VM.md** - Guia rápido (5 min)
- **DEPLOYMENT_CHECKLIST.md** - Lista de verificação
- **OFFLINE_QUICK_START.md** - Como usar sistema offline
- **README.md** - Documentação geral do projeto

---

**Última atualização:** 29 de Novembro de 2025  
**Versão:** 1.0.0  
**Status:** ✅ Pronto para Produção  

🚀 **Bom deployment!**
