#!/bin/bash

# =====================================================
# Script de Deploy - Sistema de Eventos em Docker
# =====================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de utilidade
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# =====================================================
# FUNÇÕES PRINCIPAIS
# =====================================================

build_images() {
    print_info "Construindo imagens Docker..."
    
    docker-compose build --no-cache
    
    print_success "Imagens construídas com sucesso!"
}

start_services() {
    print_info "Iniciando serviços..."
    
    docker-compose up -d
    
    print_success "Serviços iniciados!"
    print_info "Aguardando containers estabilizarem..."
    sleep 10
    
    docker-compose ps
}

stop_services() {
    print_warning "Parando serviços..."
    
    docker-compose down
    
    print_success "Serviços parados!"
}

logs_services() {
    docker-compose logs -f
}

logs_specific() {
    local service=$1
    docker-compose logs -f $service
}

database_migrate() {
    print_info "Executando migrações do banco de dados..."
    
    docker-compose exec -T backend-laravel php artisan migrate --force
    
    print_success "Migrações executadas!"
}

database_seed() {
    print_info "Semeando banco de dados..."
    
    docker-compose exec -T backend-laravel php artisan db:seed
    
    print_success "Banco de dados semeado!"
}

database_fresh() {
    print_warning "Limpando e recriando banco de dados..."
    
    docker-compose exec -T backend-laravel php artisan migrate:fresh --seed
    
    print_success "Banco de dados recriado!"
}

cache_clear() {
    print_info "Limpando caches..."
    
    docker-compose exec -T backend-laravel php artisan cache:clear
    docker-compose exec -T backend-laravel php artisan view:clear
    docker-compose exec -T backend-laravel php artisan route:clear
    docker-compose exec -T backend-laravel php artisan config:clear
    
    print_success "Caches limpos!"
}

storage_link() {
    print_info "Criando link de storage..."
    
    docker-compose exec -T backend-laravel php artisan storage:link
    
    print_success "Link de storage criado!"
}

health_check() {
    print_info "Verificando saúde dos serviços..."
    echo ""
    
    # Verificar Frontend
    if curl -s http://localhost:80/health > /dev/null; then
        print_success "Frontend está online"
    else
        print_error "Frontend offline"
    fi
    
    # Verificar API Laravel
    if curl -s http://localhost:8000/api/status > /dev/null; then
        print_success "API Laravel está online"
    else
        print_error "API Laravel offline"
    fi
    
    # Verificar API Python
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        print_success "API Python está online"
    else
        print_error "API Python offline"
    fi
    
    # Verificar Banco de Dados
    if docker-compose exec -T database mysqladmin ping -h localhost > /dev/null 2>&1; then
        print_success "Banco de Dados está online"
    else
        print_error "Banco de Dados offline"
    fi
    
    echo ""
}

status_services() {
    print_info "Status dos serviços:"
    echo ""
    docker-compose ps
    echo ""
    health_check
}

restart_services() {
    print_warning "Reiniciando serviços..."
    
    docker-compose restart
    
    print_success "Serviços reiniciados!"
    sleep 5
    status_services
}

clean_volumes() {
    print_warning "Limpando volumes de dados..."
    print_warning "Isto vai DELETAR todos os dados. Tem certeza? (s/n)"
    read -r response
    
    if [ "$response" = "s" ]; then
        docker-compose down -v
        print_success "Volumes deletados!"
    else
        print_info "Cancelado"
    fi
}

backup_database() {
    print_info "Fazendo backup do banco de dados..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backup_${timestamp}.sql"
    
    docker-compose exec -T database mysqldump \
        -u eventos_user -peventos_pass_123 \
        sistema_eventos > "backups/${backup_file}"
    
    print_success "Backup realizado: backups/${backup_file}"
}

restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Especifique o arquivo de backup: ./deploy.sh restore <arquivo>"
        return 1
    fi
    
    if [ ! -f "backups/${backup_file}" ]; then
        print_error "Arquivo não encontrado: backups/${backup_file}"
        return 1
    fi
    
    print_warning "Restaurando banco de dados de: backups/${backup_file}"
    print_warning "Isto vai SOBRESCREVER os dados. Tem certeza? (s/n)"
    read -r response
    
    if [ "$response" = "s" ]; then
        docker-compose exec -T database mysql \
            -u eventos_user -peventos_pass_123 \
            sistema_eventos < "backups/${backup_file}"
        
        print_success "Banco de dados restaurado!"
    else
        print_info "Cancelado"
    fi
}

exec_command() {
    local service=$1
    shift
    local command=$@
    
    docker-compose exec -T $service $command
}

deploy_full() {
    print_info "==================================="
    print_info "Iniciando deploy completo"
    print_info "==================================="
    echo ""
    
    build_images
    echo ""
    
    stop_services 2>/dev/null || true
    echo ""
    
    start_services
    echo ""
    
    database_migrate
    echo ""
    
    storage_link
    echo ""
    
    cache_clear
    echo ""
    
    status_services
    echo ""
    
    print_success "==================================="
    print_success "Deploy completo concluído!"
    print_success "==================================="
}

# =====================================================
# MENU PRINCIPAL
# =====================================================

show_help() {
    cat << EOF

${BLUE}╔════════════════════════════════════════════════════╗${NC}
${BLUE}║   Sistema de Eventos - Deploy Script (Docker)     ║${NC}
${BLUE}╚════════════════════════════════════════════════════╝${NC}

${GREEN}Comandos disponíveis:${NC}

  Deployment:
    ./deploy.sh deploy          - Deploy completo
    ./deploy.sh build           - Construir imagens Docker
    ./deploy.sh start           - Iniciar containers
    ./deploy.sh stop            - Parar containers
    ./deploy.sh restart         - Reiniciar containers
    ./deploy.sh status          - Verificar status

  Banco de Dados:
    ./deploy.sh migrate         - Executar migrações
    ./deploy.sh seed            - Seedar banco de dados
    ./deploy.sh fresh           - Fresh + seed
    ./deploy.sh backup          - Fazer backup
    ./deploy.sh restore <file>  - Restaurar backup

  Manutenção:
    ./deploy.sh cache-clear     - Limpar caches
    ./deploy.sh storage-link    - Criar link de storage
    ./deploy.sh health          - Verificar saúde
    ./deploy.sh logs            - Ver logs em tempo real
    ./deploy.sh logs <service>  - Ver logs de serviço
    ./deploy.sh clean           - Limpar volumes (⚠️ Deleta dados!)

  Outros:
    ./deploy.sh exec <service> <cmd>  - Executar comando em container
    ./deploy.sh help            - Mostrar esta ajuda

${BLUE}Exemplo de uso:${NC}
    ./deploy.sh deploy          # Deploy completo
    ./deploy.sh logs backend-laravel
    ./deploy.sh exec backend-laravel php artisan tinker

${YELLOW}Versão:${NC} 1.0.0
${YELLOW}Data:${NC} 29 de Novembro de 2025

EOF
}

# =====================================================
# MAIN
# =====================================================

# Verificar se docker-compose está instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose não está instalado!"
    exit 1
fi

# Criar diretório de backups se não existir
mkdir -p backups

# Processar argumentos
case "${1:-help}" in
    deploy)
        deploy_full
        ;;
    build)
        build_images
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        if [ -z "$2" ]; then
            logs_services
        else
            logs_specific "$2"
        fi
        ;;
    status)
        status_services
        ;;
    migrate)
        database_migrate
        ;;
    seed)
        database_seed
        ;;
    fresh)
        database_fresh
        ;;
    cache-clear)
        cache_clear
        ;;
    storage-link)
        storage_link
        ;;
    health)
        health_check
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    clean)
        clean_volumes
        ;;
    exec)
        shift
        exec_command "$@"
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Comando desconhecido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
