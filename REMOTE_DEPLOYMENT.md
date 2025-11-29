# 🚀 Deployment Remoto - Sistema de Eventos
## Na VM 177.44.248.118

---

## 📋 Sumário Executivo

Este documento fornece instruções completas para implantar o **Sistema de Eventos** em uma máquina virtual Ubuntu/Debian na IP `177.44.248.118` usando Docker.

**Tempo estimado de instalação:** 30-45 minutos  
**Pré-requisitos:** SSH, Docker, Docker Compose  
**Acesso SSH:** `ssh@univates177.44.248.118` (senha: `FsT#8723S`)

---

## 🔧 Pré-requisitos

### Na Máquina Local (Windows/Mac/Linux)
- Git instalado
- SSH client (Windows 10+ têm nativamente)
- Docker Desktop (opcional, apenas para testes locais)

### Na VM 177.44.248.118
- Ubuntu 20.04+ ou Debian 10+
- Docker 20.10+
- Docker Compose 1.29+
- Git
- SSH Server (já deve estar configurado)

---

## 📝 Passo 1: Acessar a VM via SSH

```powershell
# Windows PowerShell
ssh ssh@177.44.248.118

# Ou Mac/Linux Terminal
ssh ssh@177.44.248.118
```

**Senha:** `FsT#8723S`

```bash
# Você deve ver o prompt da VM:
ssh@vm-177:~$
```

---

## 📦 Passo 2: Preparar o Ambiente na VM

### 2.1 Instalar Docker (se não estiver instalado)

```bash
# Atualizar repos
sudo apt update
sudo apt upgrade -y

# Instalar Docker
sudo apt install -y docker.io docker-compose

# Verificar versões
docker --version
docker-compose --version

# Adicionar usuário ao grupo docker (opcional, para não usar sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### 2.2 Verificar Conectividade

```bash
# Testar Docker
docker run hello-world

# Testar Docker Compose
docker-compose --version
```

---

## 🔄 Passo 3: Clonar o Repositório

```bash
# Criar diretório de projetos
mkdir -p ~/projetos
cd ~/projetos

# Clonar o repositório
git clone https://github.com/brunobarp-pixel/sistema-eventos.git
cd sistema-eventos

# Listar arquivos para confirmar
ls -la
```

**Você deve ver:**
```
deploy.sh
docker-compose.yml
backend/
backend-python/
frontend/
docs/
```

---

## 🐳 Passo 4: Configurar Variáveis de Ambiente

### 4.1 Criar arquivo `.env` na raiz

```bash
# Na VM, dentro da pasta sistema-eventos
cat > .env << 'EOF'
# ===== AMBIENTE =====
APP_ENV=production
APP_DEBUG=false

# ===== IP DA VM =====
VM_IP=177.44.248.118

# ===== BANCO DE DADOS =====
DB_HOST=database
DB_PORT=3306
DB_DATABASE=sistema_eventos
DB_USERNAME=eventos_user
DB_PASSWORD=eventos_pass_123
DB_ROOT_PASSWORD=root_password_123

# ===== LARAVEL =====
APP_NAME="Sistema de Eventos"
APP_KEY=
SANCTUM_STATEFUL_DOMAINS=177.44.248.118
SESSION_DOMAIN=177.44.248.118

# ===== REDIS =====
REDIS_HOST=redis
REDIS_PASSWORD=null
REDIS_PORT=6379

# ===== EMAIL (Mailhog) =====
MAIL_DRIVER=smtp
MAIL_HOST=mailhog
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM_ADDRESS=admin@sistema-eventos.local
MAIL_FROM_NAME="Sistema de Eventos"

# ===== URLS =====
API_URL=http://177.44.248.118
FRONTEND_URL=http://177.44.248.118
EOF
```

### 4.2 Copiar .env para backend

```bash
cp .env backend/.env.production
```

---

## ▶️ Passo 5: Executar Deploy Completo

### 5.1 Tornar script executável

```bash
# Na VM, ainda em ~/projetos/sistema-eventos
chmod +x deploy.sh
```

### 5.2 Executar deploy

```bash
# Deploy completo (constrói e inicia tudo)
./deploy.sh deploy
```

**O que esse comando faz:**
1. ✅ Constrói as imagens Docker (frontend, backend Laravel, backend Python, database)
2. ✅ Inicia os 4 containers principais
3. ✅ Aguarda estabilização
4. ✅ Executa migrações do banco de dados
5. ✅ Cria links de storage
6. ✅ Limpa caches
7. ✅ Verifica status de todos os serviços

**Tempo esperado:** 5-10 minutos na primeira execução

---

## ✅ Passo 6: Verificar Status

```bash
# Ver status dos containers
./deploy.sh status

# Você deve ver algo como:
# NAME                COMMAND                  SERVICE             STATUS
# sistema-eventos-database-1         docker-entrypoint.sh mysqld      database   Up 30s (healthy)
# sistema-eventos-redis-1            redis-server --appendonly yes    redis      Up 25s
# sistema-eventos-backend-laravel-1  apache2-foreground               backend-laravel  Up 20s (healthy)
# sistema-eventos-backend-python-1   python app.py                    backend-python   Up 15s
# sistema-eventos-frontend-1         /docker-entrypoint.sh ngin...    frontend   Up 10s
```

---

## 🌐 Passo 7: Acessar a Aplicação

Abra seu navegador e acesse:

### **URL Principal**
```
http://177.44.248.118
```

### **Áreas da Aplicação**
| Funcionalidade | URL | Descrição |
|---|---|---|
| **Home** | http://177.44.248.118 | Página inicial |
| **Login** | http://177.44.248.118/login.html | Autenticação |
| **Eventos** | http://177.44.248.118/eventos.html | Listar eventos |
| **Inscrições** | http://177.44.248.118/inscricoes.html | Gerenciar inscrições |
| **Presença** | http://177.44.248.118/cadastro.html | Registrar presença |
| **Certificados** | http://177.44.248.118/certificados.html | Emitir certificados |
| **Offline** | http://177.44.248.118/offline.html | Modo offline |
| **API** | http://177.44.248.118/api/status | API REST |

### **Ferramentas de Desenvolvimento**
| Ferramenta | URL | Credenciais |
|---|---|---|
| **Mailhog** | http://177.44.248.118:8025 | Sem autenticação |
| **Redis** | localhost:6379 | (interna) |
| **MySQL** | localhost:3306 | root / root_password_123 |

---

## 🛠️ Passo 8: Comandos Úteis

### Ver Logs em Tempo Real
```bash
# Todos os serviços
./deploy.sh logs

# Apenas Laravel
./deploy.sh logs backend-laravel

# Apenas Python
./deploy.sh logs backend-python

# Apenas Frontend
./deploy.sh logs frontend
```

### Executar Comandos Laravel
```bash
# Acessar tinker (shell interativo)
./deploy.sh exec backend-laravel php artisan tinker

# Listar rotas
./deploy.sh exec backend-laravel php artisan route:list

# Criar nova migration
./deploy.sh exec backend-laravel php artisan make:migration nome_da_migration

# Executar específica
./deploy.sh exec backend-laravel php artisan migrate:refresh --seed
```

### Gerenciar Banco de Dados
```bash
# Backup do banco
./deploy.sh backup

# Restaurar backup
./deploy.sh restore backup_20251129_143022.sql

# Limpar e resetar banco
./deploy.sh fresh
```

### Reiniciar Serviços
```bash
# Reiniciar tudo
./deploy.sh restart

# Parar tudo
./deploy.sh stop

# Iniciar novamente
./deploy.sh start
```

### Verificar Saúde
```bash
# Health check dos serviços
./deploy.sh health
```

---

## 📊 Passo 9: Verificar Logs Importantes

### 9.1 Database
```bash
docker-compose logs database | tail -50
```

### 9.2 Laravel API
```bash
docker-compose logs backend-laravel | tail -50
```

### 9.3 Python Backend
```bash
docker-compose logs backend-python | tail -50
```

### 9.4 Frontend Nginx
```bash
docker-compose logs frontend | tail -50
```

---

## 🔒 Passo 10: Configurações de Segurança (Opcional)

### 10.1 Usar HTTPS com Let's Encrypt

```bash
# 1. Instalar Certbot na VM
sudo apt install -y certbot python3-certbot-nginx

# 2. Obter certificado
sudo certbot certonly --standalone -d 177.44.248.118

# 3. Copiar certificados para o projeto
sudo cp /etc/letsencrypt/live/177.44.248.118/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/177.44.248.118/privkey.pem ./certs/
sudo chown $USER:$USER ./certs/*

# 4. Descomentar HTTPS no nginx.conf
# Editar: frontend/default.conf
# Descomentar as linhas de HTTPS
```

### 10.2 Firewall

```bash
# Instalar UFW (se necessário)
sudo apt install -y ufw

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP
sudo ufw allow 80/tcp

# Permitir HTTPS
sudo ufw allow 443/tcp

# Ativar firewall
sudo ufw enable
```

---

## 📈 Passo 11: Monitoramento Contínuo

### 11.1 Ver uso de recursos

```bash
# Em tempo real
docker stats

# Ou verificar status geral
docker-compose ps
```

### 11.2 Configurar logs persistentes

```bash
# Logs estão em:
# - Docker: /var/lib/docker/containers/
# - Laravel: docker exec backend-laravel tail -f storage/logs/laravel.log
# - Python: docker exec backend-python tail -f app.log
```

---

## 🔄 Passo 12: Atualizações e Manutenção

### 12.1 Atualizar código

```bash
# Na VM, dentro do projeto
git pull origin main

# Reconstruir imagens
./deploy.sh build

# Reiniciar
./deploy.sh restart
```

### 12.2 Backup Regular

```bash
# Fazer backup agora
./deploy.sh backup

# Listar backups
ls -lh backups/

# Restaurar específico
./deploy.sh restore backup_YYYYMMDD_HHMMSS.sql
```

---

## ⚠️ Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker-compose logs [service_name]

# Reconstruir container
docker-compose up -d --force-recreate [service_name]
```

### Erro de conexão ao banco
```bash
# Verificar se database está rodando
docker-compose ps database

# Conectar ao database
docker-compose exec database mysql -u root -p sistema_eventos

# Resetar banco
./deploy.sh fresh
```

### Erro 502 Bad Gateway no Frontend
```bash
# Verificar se backend-laravel está rodando
./deploy.sh logs backend-laravel

# Reiniciar backend
docker-compose restart backend-laravel
```

### Porta já em uso
```bash
# Encontrar processo usando porta
sudo lsof -i :80
sudo lsof -i :8000
sudo lsof -i :5000

# Matar processo
kill -9 [PID]

# Ou mudar portas em docker-compose.yml
```

---

## 📞 Suporte e Contato

Se encontrar problemas:

1. **Verifique os logs**: `./deploy.sh logs`
2. **Consulte o troubleshooting acima**
3. **Verifique conectividade**: `./deploy.sh health`
4. **Reinicie tudo**: `./deploy.sh restart`

---

## 📚 Documentação Relacionada

- [`DEPLOYMENT_CHECKLIST.md`](./DEPLOYMENT_CHECKLIST.md) - Lista de verificação
- [`EXECUTIVE_SUMMARY.md`](./EXECUTIVE_SUMMARY.md) - Resumo da aplicação
- [`OFFLINE_QUICK_START.md`](./OFFLINE_QUICK_START.md) - Como usar offline
- [`docker-compose.yml`](./docker-compose.yml) - Configuração dos containers

---

## 📅 Histórico de Deployment

| Data | Versão | Status | IP |
|------|--------|--------|-----|
| 29/11/2025 | 1.0.0 | Pronto | 177.44.248.118 |

---

**Última atualização:** 29 de Novembro de 2025  
**Versão:** 1.0.0  
**Status:** ✅ Pronto para Produção
