#!/bin/bash

# =====================================================
# INSTALL.SH - Instalação Completa na VM
# Sistema de Eventos - Deploy Automatizado
# =====================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# =====================================================
# INÍCIO
# =====================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  INSTALAÇÃO - SISTEMA DE EVENTOS                  ║${NC}"
echo -e "${BLUE}║  VM: 177.44.248.118                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# =====================================================
# PASSO 1: Verificar privilégios
# =====================================================

print_step "Verificando privilégios..."

if [ "$EUID" -eq 0 ]; then
   print_warning "Este script deve ser executado como usuário comum, não como root"
   print_step "Continuando de qualquer forma..."
else
   print_success "Executando como usuário comum"
fi

# =====================================================
# PASSO 2: Atualizar sistema
# =====================================================

print_step "Atualizando sistema..."
sudo apt update
sudo apt upgrade -y
print_success "Sistema atualizado"

# =====================================================
# PASSO 3: Instalar dependências
# =====================================================

print_step "Instalando dependências..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip

print_success "Dependências instaladas"

# =====================================================
# PASSO 4: Instalar Docker
# =====================================================

print_step "Verificando Docker..."

if ! command -v docker &> /dev/null; then
    print_warning "Docker não encontrado, instalando..."
    
    # Remover versões antigas
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Instalar Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Adicionar usuário ao grupo docker
    sudo usermod -aG docker $USER
    
    print_success "Docker instalado"
else
    print_success "Docker já está instalado"
fi

# =====================================================
# PASSO 5: Instalar Docker Compose
# =====================================================

print_step "Verificando Docker Compose..."

if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose não encontrado, instalando..."
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose instalado"
else
    print_success "Docker Compose já está instalado"
fi

# =====================================================
# PASSO 6: Verificar versões
# =====================================================

print_step "Verificando versões..."
echo ""
docker --version
docker-compose --version
echo ""
print_success "Versões verificadas"

# =====================================================
# PASSO 7: Preparar diretórios
# =====================================================

print_step "Preparando diretórios..."

mkdir -p ~/projetos
cd ~/projetos

print_success "Diretórios preparados"

# =====================================================
# PASSO 8: Clonar repositório
# =====================================================

if [ -d "sistema-eventos" ]; then
    print_warning "Repositório já existe em ~/projetos/sistema-eventos"
    print_step "Atualizando..."
    cd sistema-eventos
    git pull origin main
else
    print_step "Clonando repositório..."
    git clone https://github.com/brunobarp-pixel/sistema-eventos.git
    cd sistema-eventos
    print_success "Repositório clonado"
fi

# =====================================================
# PASSO 9: Preparar ambiente
# =====================================================

print_step "Preparando arquivo .env..."

if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# ===== AMBIENTE =====
APP_ENV=production
APP_DEBUG=false

# ===== VM IP =====
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
APP_KEY=base64:+DYvgUFYcWK2o/9NvprVP8ZrM3Z8L2n8X3Q9K7L3Z2M=
SANCTUM_STATEFUL_DOMAINS=177.44.248.118
SESSION_DOMAIN=177.44.248.118

# ===== REDIS =====
REDIS_HOST=redis
REDIS_PASSWORD=null
REDIS_PORT=6379

# ===== EMAIL =====
MAIL_DRIVER=smtp
MAIL_HOST=mailhog
MAIL_PORT=1025
MAIL_FROM_ADDRESS=admin@sistema-eventos.local
MAIL_FROM_NAME="Sistema de Eventos"

# ===== URLs =====
API_URL=http://177.44.248.118
FRONTEND_URL=http://177.44.248.118
EOF
    print_success "Arquivo .env criado"
else
    print_success "Arquivo .env já existe"
fi

# =====================================================
# PASSO 10: Copiar .env para backend
# =====================================================

print_step "Copiando .env para backend..."
cp .env backend/.env.production
print_success ".env copiado"

# =====================================================
# PASSO 11: Preparar script deploy
# =====================================================

print_step "Preparando script de deploy..."
chmod +x deploy.sh
print_success "Script de deploy preparado"

# =====================================================
# PASSO 12: Testar Docker
# =====================================================

print_step "Testando Docker..."
docker run --rm hello-world > /dev/null
print_success "Docker funcionando corretamente"

# =====================================================
# CONCLUSÃO
# =====================================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ INSTALAÇÃO COMPLETA!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

print_success "Ambiente preparado com sucesso!"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo ""
echo "  1. Entre no diretório do projeto:"
echo "     cd ~/projetos/sistema-eventos"
echo ""
echo "  2. Execute o deploy completo:"
echo "     ./deploy.sh deploy"
echo ""
echo "  3. Aguarde 5-10 minutos para conclusão"
echo ""
echo "  4. Acesse a aplicação:"
echo "     http://177.44.248.118"
echo ""
echo -e "${BLUE}Documentação:${NC}"
echo "  - REMOTE_DEPLOYMENT.md   (Guia completo)"
echo "  - DEPLOYMENT_CHECKLIST.md (Lista de verificação)"
echo ""
