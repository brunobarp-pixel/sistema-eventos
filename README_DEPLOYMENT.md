# 🚀 README - DEPLOYMENT NA VM 177.44.248.118

> **Leia isto primeiro!** Tudo que você precisa para rodar o Sistema de Eventos na VM.

---

## 📦 Você Recebeu

✅ **4 containers Docker** prontos para rodar  
✅ **4 scripts de deployment** automatizados  
✅ **5+ documentos** de guia passo a passo  
✅ **Sistema offline** com localStorage e sincronização  
✅ **Backup & restauração** automática  

---

## ⚡ Quick Start (30 min)

### Passo 1: SSH
```bash
ssh ssh@177.44.248.118
# Senha: FsT#8723S
```

### Passo 2: Instalar
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/brunobarp-pixel/sistema-eventos/main/install.sh)
```

### Passo 3: Deploy
```bash
# Aguarde a conclusão da instalação, depois:
cd ~/projetos/sistema-eventos
./deploy.sh deploy
```

### Passo 4: Acessar
```
http://177.44.248.118
```

**Pronto!** Sua aplicação está rodando. ✅

---

## 📚 Documentação

| Documento | Tempo | Para Quem |
|-----------|-------|----------|
| **START_HERE.md** ⭐ | 2 min | Leia primeiro |
| **QUICK_START_VM.md** | 5 min | Desenvolvimento rápido |
| **COMPLETE_GUIDE.md** | 15 min | Desenvolvimento completo |
| **REMOTE_DEPLOYMENT.md** | 30 min | Detalhes técnicos |
| **DEPLOYMENT_CHECKLIST.md** | 10 min | Verificações |

---

## 🛠️ Ferramentas

| Ferramenta | Arquivo | Para O Quê |
|-----------|---------|-----------|
| **deploy.sh** | Script shell | Gerenciar containers (principais comandos) |
| **install.sh** | Script shell | Instalar Docker na VM |
| **checklist.sh** | Script shell | Verificar pré/pós deployment |
| **remote_deploy.py** | Script Python | Menu interativo (da sua máquina) |

---

## 🔐 Credenciais

```
SSH VM:
  Host:     177.44.248.118
  User:     ssh
  Password: FsT#8723S

MySQL:
  Host:     localhost:3306
  Database: sistema_eventos
  User:     eventos_user
  Password: eventos_pass_123

MySQL Root:
  User:     root
  Password: root_password_123
```

---

## 🌐 URLs

| URL | Para O Quê |
|-----|-----------|
| http://177.44.248.118 | Aplicação principal |
| http://177.44.248.118/offline.html | Modo offline |
| http://177.44.248.118/api/status | Status da API |
| http://177.44.248.118:8025 | Mailhog (emails) |

---

## 📋 Checklist Rápido

### Antes de Deploy
- [ ] Acessar SSH da VM (177.44.248.118)
- [ ] Executar install.sh
- [ ] Verificar Docker instalado

### Depois de Deploy
- [ ] Acessar http://177.44.248.118
- [ ] Testar página inicial
- [ ] Executar `./deploy.sh health`
- [ ] Fazer `./deploy.sh backup`

---

## 🚨 Troubleshooting

| Problema | Solução |
|----------|---------|
| Erro ao conectar SSH | Verificar IP, porta 22 aberta, firewall |
| Docker não instala | Executar `bash install.sh` de novo |
| Container não inicia | `./deploy.sh logs` para ver erro |
| API retorna 502 | `./deploy.sh restart backend-laravel` |
| Banco não conecta | `./deploy.sh fresh` para resetar |

---

## 📖 Guias por Experiência

### 👶 Iniciante
1. Leia: `START_HERE.md` (2 min)
2. Execute: `bash install.sh` (10 min)
3. Espere: Deploy automático (20 min)
4. Pronto! 🎉

### 👨‍💻 Desenvolvedor
1. Leia: `COMPLETE_GUIDE.md` (15 min)
2. Use: `python remote_deploy.py` (interativo)
3. Customize: Variáveis de ambiente
4. Deploy: `./deploy.sh deploy`

### 🏢 DevOps
1. Estude: `docker-compose.yml`
2. Customize: Todas as configurações
3. Setup: Firewall, SSL/TLS
4. Monitore: `docker stats`

---

## 💾 Backup & Restauração

```bash
# Fazer backup
./deploy.sh backup

# Listar backups
ls -lh backups/

# Restaurar
./deploy.sh restore backup_20251129_143022.sql

# Ou resetar tudo
./deploy.sh fresh
```

---

## 🎯 Comandos Essenciais

```bash
# Iniciar tudo
./deploy.sh deploy

# Ver status
./deploy.sh status

# Ver logs
./deploy.sh logs

# Verificar saúde
./deploy.sh health

# Reiniciar
./deploy.sh restart

# Ver ajuda
./deploy.sh help
```

---

## 🔧 O Que Está Incluído

### Componentes Docker
- ✅ Frontend (Nginx)
- ✅ Backend Laravel (PHP 8.2)
- ✅ Backend Python (Python 3.11)
- ✅ MySQL Database
- ✅ Redis Cache
- ✅ Mailhog Email Testing

### Scripts de Deploy
- ✅ `deploy.sh` - Principal
- ✅ `install.sh` - Instalação
- ✅ `checklist.sh` - Verificações
- ✅ `remote_deploy.py` - Menu interativo

### Documentação
- ✅ 5+ Guias completos
- ✅ Exemplos de comando
- ✅ Troubleshooting
- ✅ Referência técnica

---

## 📊 Arquitetura

```
┌─────────────────────────────────┐
│   USUARIOS NA INTERNET          │
│   http://177.44.248.118         │
└──────────────┬──────────────────┘
               │
         ┌─────▼──────┐
         │  Nginx     │
         │  Frontend  │
         └─────┬──────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
   Laravel API     Python API
   (Port 8000)     (Port 5000)
      │                 │
      └────────┬────────┘
               │
        ┌──────▼──────┐
        │ MySQL + Redis
        │ Database
        └─────────────┘
```

---

## ⏱️ Timeline

| O Quê | Tempo | Status |
|-------|-------|--------|
| SSH na VM | 1 min | Rápido |
| Instalar Docker | 10 min | Automático |
| Build imagens | 8 min | Esperar |
| Deploy containers | 3 min | Esperar |
| Migrar banco | 2 min | Esperar |
| Testar aplicação | 2 min | Manual |
| **TOTAL** | **~30 min** | ✅ **PRONTO** |

---

## 🎁 Bônus

- ✨ Sistema offline com localStorage
- ✨ Sincronização automática
- ✨ Interface Python interativa
- ✨ Checklist automatizado
- ✨ Backup automático
- ✨ Health checks
- ✨ Logging centralizado
- ✨ Pronto para HTTPS

---

## 🚀 Comece Agora!

```bash
# Copie e execute:
ssh ssh@177.44.248.118

# Depois, na VM:
bash <(curl -fsSL https://raw.githubusercontent.com/brunobarp-pixel/sistema-eventos/main/install.sh)

# Em ~30 minutos:
# Acesse: http://177.44.248.118
```

---

## 📞 Suporte Rápido

**Algo deu errado?**
```bash
# 1. Ver logs
./deploy.sh logs

# 2. Reiniciar
./deploy.sh restart

# 3. Verificar saúde
./deploy.sh health

# 4. Se persistir, resetar
./deploy.sh fresh
```

**Precisa de ajuda?**
- Consulte: `REMOTE_DEPLOYMENT.md` (guia detalhado)
- Execute: `./deploy.sh help`

---

## ✅ Status Final

| Componente | Status |
|-----------|--------|
| Código | ✅ Completo |
| Docker | ✅ Pronto |
| Scripts | ✅ Testado |
| Documentação | ✅ Completa |
| Produção | ✅ Pronto |

---

**Data:** 29 de Novembro de 2025  
**Versão:** 1.0.0  
**Status:** ✅ Pronto para Produção  
**VM IP:** 177.44.248.118

---

🎉 **Bem-vindo ao Sistema de Eventos Dockerizado!**

**Próximo passo:** Leia `START_HERE.md` ou execute `bash install.sh` na VM.
