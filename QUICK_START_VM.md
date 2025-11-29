# ⚡ Quick Start - Deploy na VM 177.44.248.118

## 🚀 Instalação em 3 Passos

### Passo 1: Conectar via SSH
```bash
# Windows PowerShell
ssh ssh@177.44.248.118

# Senha: FsT#8723S
```

### Passo 2: Executar instalação automatizada
```bash
# Dentro da VM, execute:
cd ~ && curl -fsSL https://raw.githubusercontent.com/brunobarp-pixel/sistema-eventos/main/install.sh | bash

# Ou, se clonar manualmente:
git clone https://github.com/brunobarp-pixel/sistema-eventos.git
cd sistema-eventos
bash install.sh
```

### Passo 3: Deploy completo
```bash
# Na VM, dentro de ~/projetos/sistema-eventos
./deploy.sh deploy
```

**⏱️ Tempo total:** ~30 minutos (primeira execução)

---

## 📋 Checklist de Deployment

### Pré-Deployment
- [ ] Conectar via SSH (ssh ssh@177.44.248.118)
- [ ] Executar install.sh
- [ ] Verificar Docker: `docker --version`
- [ ] Verificar Docker Compose: `docker-compose --version`

### Durante Deploy
- [ ] Aguardar buildagem das imagens (5-8 min)
- [ ] Aguardar inicialização dos containers (2-3 min)
- [ ] Verificar migrações do BD (1-2 min)
- [ ] Verificar limpeza de caches (1 min)

### Pós-Deployment
- [ ] Acessar http://177.44.248.118
- [ ] Verificar página inicial carrega
- [ ] Testar login
- [ ] Verificar API: http://177.44.248.118/api/status
- [ ] Executar ./deploy.sh health
- [ ] Fazer backup inicial

---

## 🔧 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| Erro de conexão SSH | Verificar IP (177.44.248.118), porta SSH (22), firewall |
| Docker não instalado | Executar: `bash install.sh` |
| Containers não iniciam | `./deploy.sh logs` para ver erro |
| Porta 80 já em uso | `sudo lsof -i :80` para encontrar processo |
| Banco de dados não conecta | `./deploy.sh fresh` para resetar |
| Erro 502 Bad Gateway | `./deploy.sh restart` |

---

## 📱 URLs Principais

| Recurso | URL |
|---------|-----|
| **Aplicação** | http://177.44.248.118 |
| **Offline** | http://177.44.248.118/offline.html |
| **API** | http://177.44.248.118/api |
| **Mailhog** | http://177.44.248.118:8025 |

---

## 💾 Backup & Restauração Rápida

```bash
# Backup
./deploy.sh backup

# Restaurar
./deploy.sh restore backup_20251129_143022.sql

# Fresh reset (limpar tudo)
./deploy.sh fresh
```

---

## 🎯 Próximos Passos

1. **Primeira vez?** Leia [`REMOTE_DEPLOYMENT.md`](./REMOTE_DEPLOYMENT.md)
2. **Mais detalhes?** Veja [`DEPLOYMENT_CHECKLIST.md`](./DEPLOYMENT_CHECKLIST.md)
3. **Python Script?** Use `python remote_deploy.py` na sua máquina local

---

## 📞 Suporte

**Comandos úteis:**

```bash
# Ver status
./deploy.sh status

# Ver logs
./deploy.sh logs

# Verificar saúde
./deploy.sh health

# Executar comando Laravel
./deploy.sh exec backend-laravel php artisan tinker

# SSH na VM
ssh ssh@177.44.248.118
```

---

**Data:** 29 de Novembro de 2025  
**Status:** ✅ Pronto para Produção
