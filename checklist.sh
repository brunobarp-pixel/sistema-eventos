#!/bin/bash

# =====================================================
# CHECKLIST - Pré e Pós Deployment
# Sistema de Eventos
# =====================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;37m'
NC='\033[0m'

# Contadores
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Funções
check_pass() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}[✗]${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((CHECKS_WARNING++))
}

check_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

check_cmd() {
    local cmd=$1
    local desc=$2
    
    if eval "$cmd" > /dev/null 2>&1; then
        check_pass "$desc"
    else
        check_fail "$desc"
    fi
}

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_footer() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} RESUMO"
    echo -e "${BLUE}║${NC} Passou:   ${GREEN}$CHECKS_PASSED${NC}"
    echo -e "${BLUE}║${NC} Avisos:   ${YELLOW}$CHECKS_WARNING${NC}"
    echo -e "${BLUE}║${NC} Falhas:   ${RED}$CHECKS_FAILED${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ TUDO OK! Pronto para deploy.${NC}"
        return 0
    else
        echo -e "${RED}❌ Existem problemas a resolver.${NC}"
        return 1
    fi
}

# =====================================================
# MENU
# =====================================================

show_menu() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  CHECKLIST - Sistema de Eventos                   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Escolha o que verificar:"
    echo ""
    echo "  1) PRÉ-REQUISITOS (verificar antes de começar)"
    echo "  2) CONFIGURAÇÃO (verificar depois de clonar)"
    echo "  3) DOCKER (verificar Docker na VM)"
    echo "  4) PÓS-DEPLOYMENT (verificar após deploy)"
    echo "  5) TUDO (executar todos os checklist)"
    echo "  6) SAIR"
    echo ""
}

# =====================================================
# CHECKLIST 1: PRÉ-REQUISITOS
# =====================================================

check_prerequisites() {
    print_header "1. PRÉ-REQUISITOS - Verificações Iniciais"
    
    check_info "Verificando conexão com internet..."
    check_cmd "ping -c 1 8.8.8.8 > /dev/null 2>&1" "Conexão com internet"
    
    check_info "Verificando ferramentas necessárias..."
    check_cmd "command -v git" "Git instalado"
    check_cmd "command -v ssh" "SSH client disponível"
    check_cmd "command -v curl" "curl instalado"
    check_cmd "command -v wget" "wget instalado"
    
    check_info "Verificando conectividade SSH..."
    if ssh -o ConnectTimeout=5 ssh@177.44.248.118 "echo OK" > /dev/null 2>&1; then
        check_pass "Conexão SSH com 177.44.248.118"
    else
        check_fail "Conexão SSH com 177.44.248.118"
    fi
    
    check_info "Verificando espaço em disco..."
    local disk_available=$(df ~ | tail -1 | awk '{print $4}')
    if [ $disk_available -gt 2097152 ]; then  # 2GB em KB
        check_pass "Espaço em disco disponível (>2GB)"
    else
        check_warn "Espaço em disco limitado (<2GB)"
    fi
    
    print_footer
}

# =====================================================
# CHECKLIST 2: CONFIGURAÇÃO
# =====================================================

check_configuration() {
    print_header "2. CONFIGURAÇÃO - Arquivos e Estrutura"
    
    check_info "Verificando estrutura do projeto..."
    
    # Verificar arquivos principais
    local project_dir=$(pwd)
    
    if [ -f "$project_dir/docker-compose.yml" ]; then
        check_pass "docker-compose.yml existe"
    else
        check_fail "docker-compose.yml não encontrado"
    fi
    
    if [ -f "$project_dir/deploy.sh" ]; then
        check_pass "deploy.sh existe"
        if [ -x "$project_dir/deploy.sh" ]; then
            check_pass "deploy.sh é executável"
        else
            check_warn "deploy.sh não é executável (chmod +x deploy.sh)"
        fi
    else
        check_fail "deploy.sh não encontrado"
    fi
    
    if [ -d "$project_dir/backend" ]; then
        check_pass "Diretório backend existe"
    else
        check_fail "Diretório backend não encontrado"
    fi
    
    if [ -d "$project_dir/frontend" ]; then
        check_pass "Diretório frontend existe"
    else
        check_fail "Diretório frontend não encontrado"
    fi
    
    if [ -d "$project_dir/backend-python" ]; then
        check_pass "Diretório backend-python existe"
    else
        check_fail "Diretório backend-python não encontrado"
    fi
    
    check_info "Verificando arquivos de configuração..."
    
    if [ -f "$project_dir/.env" ]; then
        check_pass ".env existe"
    else
        check_warn ".env não encontrado (será criado durante install.sh)"
    fi
    
    if [ -f "$project_dir/backend/.env.production" ]; then
        check_pass "backend/.env.production existe"
    else
        check_warn "backend/.env.production não encontrado"
    fi
    
    check_info "Verificando documentação..."
    
    if [ -f "$project_dir/REMOTE_DEPLOYMENT.md" ]; then
        check_pass "REMOTE_DEPLOYMENT.md existe"
    else
        check_fail "REMOTE_DEPLOYMENT.md não encontrado"
    fi
    
    if [ -f "$project_dir/QUICK_START_VM.md" ]; then
        check_pass "QUICK_START_VM.md existe"
    else
        check_fail "QUICK_START_VM.md não encontrado"
    fi
    
    print_footer
}

# =====================================================
# CHECKLIST 3: DOCKER
# =====================================================

check_docker() {
    print_header "3. DOCKER - Verificações de Docker"
    
    check_info "Verificando instalação de Docker..."
    
    check_cmd "command -v docker" "Docker instalado"
    check_cmd "command -v docker-compose" "Docker Compose instalado"
    
    check_info "Verificando versões..."
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        check_info "Docker versão: $docker_version"
    fi
    
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        check_info "Docker Compose versão: $compose_version"
    fi
    
    check_info "Verificando conectividade Docker..."
    check_cmd "docker ps" "Docker daemon respondendo"
    
    check_info "Verificando permissões..."
    if docker ps > /dev/null 2>&1; then
        check_pass "Permissões adequadas para usar Docker"
    else
        check_warn "Sem permissões Docker. Execute: sudo usermod -aG docker \$USER"
    fi
    
    check_info "Testando Docker..."
    if docker run --rm hello-world > /dev/null 2>&1; then
        check_pass "Teste Docker bem-sucedido"
    else
        check_fail "Teste Docker falhou"
    fi
    
    check_info "Verificando docker-compose.yml..."
    if [ -f "docker-compose.yml" ]; then
        if docker-compose config > /dev/null 2>&1; then
            check_pass "docker-compose.yml é válido"
        else
            check_fail "docker-compose.yml tem erros de sintaxe"
        fi
    fi
    
    print_footer
}

# =====================================================
# CHECKLIST 4: PÓS-DEPLOYMENT
# =====================================================

check_post_deployment() {
    print_header "4. PÓS-DEPLOYMENT - Verificação de Serviços"
    
    check_info "Verificando containers..."
    
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps 2>/dev/null | grep -q "frontend"; then
            check_pass "Frontend container existe"
        else
            check_fail "Frontend container não está rodando"
        fi
        
        if docker-compose ps 2>/dev/null | grep -q "backend-laravel"; then
            check_pass "Backend Laravel container existe"
        else
            check_fail "Backend Laravel container não está rodando"
        fi
        
        if docker-compose ps 2>/dev/null | grep -q "backend-python"; then
            check_pass "Backend Python container existe"
        else
            check_fail "Backend Python container não está rodando"
        fi
        
        if docker-compose ps 2>/dev/null | grep -q "database"; then
            check_pass "Database container existe"
        else
            check_fail "Database container não está rodando"
        fi
    fi
    
    check_info "Verificando conectividade de serviços..."
    
    if curl -s http://localhost:80 > /dev/null 2>&1; then
        check_pass "Frontend está respondendo (porta 80)"
    else
        check_warn "Frontend não está respondendo"
    fi
    
    if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
        check_pass "API Laravel está respondendo (porta 8000)"
    else
        check_warn "API Laravel não está respondendo"
    fi
    
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        check_pass "API Python está respondendo (porta 5000)"
    else
        check_warn "API Python não está respondendo"
    fi
    
    check_info "Verificando volumes..."
    
    if docker volume ls 2>/dev/null | grep -q "db_data"; then
        check_pass "Volume de banco de dados existe"
    else
        check_warn "Volume de banco de dados não encontrado"
    fi
    
    check_info "Verificando rede Docker..."
    
    if docker network ls 2>/dev/null | grep -q "sistema-eventos-network"; then
        check_pass "Rede Docker 'sistema-eventos-network' existe"
    else
        check_warn "Rede Docker não encontrada"
    fi
    
    print_footer
}

# =====================================================
# MAIN
# =====================================================

main() {
    while true; do
        show_menu
        
        read -p "Escolha uma opção (1-6): " choice
        
        case $choice in
            1)
                check_prerequisites
                ;;
            2)
                check_configuration
                ;;
            3)
                check_docker
                ;;
            4)
                check_post_deployment
                ;;
            5)
                check_prerequisites
                check_configuration
                check_docker
                check_post_deployment
                ;;
            6)
                echo -e "${GREEN}Até logo!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opção inválida!${NC}"
                ;;
        esac
        
        read -p "Pressione ENTER para continuar..."
    done
}

# Executar
main
