#!/usr/bin/env python3
"""
Deploy Remoto - Sistema de Eventos
Script para facilitar deploy na VM 177.44.248.118
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_banner():
    """Exibe banner de boas-vindas"""
    print(f"""
{Colors.CYAN}╔════════════════════════════════════════════════════════════╗{Colors.END}
{Colors.CYAN}║{Colors.END}  {Colors.BOLD}Sistema de Eventos - Deploy Remoto{Colors.END}
{Colors.CYAN}║{Colors.END}  {Colors.GREEN}VM: 177.44.248.118{Colors.END}
{Colors.CYAN}╚════════════════════════════════════════════════════════════╝{Colors.END}
    """)

def print_info(msg):
    """Imprime mensagem informativa"""
    print(f"{Colors.BLUE}ℹ  {msg}{Colors.END}")

def print_success(msg):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_warning(msg):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠  {msg}{Colors.END}")

def print_error(msg):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def run_command(cmd, description=None, show_output=True):
    """Executa comando e retorna status"""
    if description:
        print_info(description)
    
    try:
        if show_output:
            result = subprocess.run(cmd, shell=True, check=True)
        else:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao executar: {cmd}")
        return False

def ssh_command(cmd, host="ssh@177.44.248.118"):
    """Executa comando via SSH"""
    ssh_cmd = f'ssh {host} "{cmd}"'
    return run_command(ssh_cmd, show_output=True)

def setup_menu():
    """Menu de configuração inicial"""
    print(f"\n{Colors.BOLD}1. CONFIGURAÇÃO INICIAL{Colors.END}")
    print(f"""
Opções:
  1) Verificar pré-requisitos locais
  2) Verificar conectividade SSH
  3) Verificar Docker na VM
  4) Voltar
    """)
    
    choice = input(f"{Colors.CYAN}Escolha uma opção (1-4): {Colors.END}").strip()
    
    if choice == "1":
        check_prerequisites()
    elif choice == "2":
        check_ssh_connectivity()
    elif choice == "3":
        check_remote_docker()
    elif choice == "4":
        return
    else:
        print_error("Opção inválida!")

def check_prerequisites():
    """Verifica pré-requisitos locais"""
    print_info("Verificando pré-requisitos locais...")
    
    # Verificar Git
    if run_command("git --version", show_output=False):
        print_success("Git instalado")
    else:
        print_error("Git não está instalado")
    
    # Verificar SSH
    if run_command("ssh -V", show_output=False):
        print_success("SSH client disponível")
    else:
        print_error("SSH client não está disponível")

def check_ssh_connectivity():
    """Verifica conectividade SSH"""
    print_info("Testando conectividade SSH com 177.44.248.118...")
    
    cmd = 'ssh -o ConnectTimeout=5 ssh@177.44.248.118 "echo OK"'
    if run_command(cmd, show_output=False):
        print_success("Conexão SSH funcionando!")
    else:
        print_error("Não conseguiu conectar via SSH")
        print_warning("Verifique:")
        print("  - IP: 177.44.248.118")
        print("  - Usuário: ssh")
        print("  - Porta SSH padrão (22) está aberta")

def check_remote_docker():
    """Verifica Docker na VM"""
    print_info("Verificando Docker na VM...")
    
    cmd = 'ssh ssh@177.44.248.118 "docker --version && docker-compose --version"'
    if run_command(cmd, show_output=False):
        print_success("Docker e Docker Compose estão instalados na VM!")
    else:
        print_error("Docker não está instalado ou não está acessível")

def deploy_menu():
    """Menu de deployment"""
    print(f"\n{Colors.BOLD}2. DEPLOYMENT{Colors.END}")
    print(f"""
Opções:
  1) Deploy Completo (recomendado na 1ª vez)
  2) Build apenas (reconstruir imagens)
  3) Start (iniciar containers)
  4) Stop (parar containers)
  5) Restart (reiniciar tudo)
  6) Status dos containers
  7) Health Check
  8) Voltar
    """)
    
    choice = input(f"{Colors.CYAN}Escolha uma opção (1-8): {Colors.END}").strip()
    
    if choice == "1":
        deploy_full()
    elif choice == "2":
        remote_deploy("build")
    elif choice == "3":
        remote_deploy("start")
    elif choice == "4":
        remote_deploy("stop")
    elif choice == "5":
        remote_deploy("restart")
    elif choice == "6":
        remote_deploy("status")
    elif choice == "7":
        remote_deploy("health")
    elif choice == "8":
        return
    else:
        print_error("Opção inválida!")

def deploy_full():
    """Deploy completo"""
    print_warning("Isso vai levar alguns minutos...")
    print_info("Iniciando deploy completo na VM...")
    
    cmd = 'ssh ssh@177.44.248.118 "cd ~/projetos/sistema-eventos && ./deploy.sh deploy"'
    run_command(cmd)

def remote_deploy(action):
    """Executa ação de deploy remoto"""
    cmd = f'ssh ssh@177.44.248.118 "cd ~/projetos/sistema-eventos && ./deploy.sh {action}"'
    run_command(cmd)

def database_menu():
    """Menu de banco de dados"""
    print(f"\n{Colors.BOLD}3. BANCO DE DADOS{Colors.END}")
    print(f"""
Opções:
  1) Executar migrações
  2) Seedar banco de dados
  3) Fresh (limpar e resetar)
  4) Backup
  5) Restaurar backup
  6) Listar backups
  7) Conectar ao MySQL
  8) Voltar
    """)
    
    choice = input(f"{Colors.CYAN}Escolha uma opção (1-8): {Colors.END}").strip()
    
    if choice == "1":
        remote_deploy("migrate")
    elif choice == "2":
        remote_deploy("seed")
    elif choice == "3":
        remote_deploy("fresh")
    elif choice == "4":
        remote_deploy("backup")
    elif choice == "5":
        list_backups()
        backup_name = input("Nome do backup para restaurar: ").strip()
        if backup_name:
            cmd = f'ssh ssh@177.44.248.118 "cd ~/projetos/sistema-eventos && ./deploy.sh restore {backup_name}"'
            run_command(cmd)
    elif choice == "6":
        list_backups()
    elif choice == "7":
        connect_mysql()
    elif choice == "8":
        return
    else:
        print_error("Opção inválida!")

def list_backups():
    """Lista backups disponíveis"""
    print_info("Backups disponíveis:")
    cmd = 'ssh ssh@177.44.248.118 "ls -lh ~/projetos/sistema-eventos/backups/"'
    run_command(cmd)

def connect_mysql():
    """Conecta ao MySQL via SSH"""
    print_warning("Você será conectado ao MySQL. Digite 'exit' para sair.")
    host = "ssh@177.44.248.118"
    password = "eventos_pass_123"
    
    cmd = f'ssh {host} "docker-compose -f ~/projetos/sistema-eventos/docker-compose.yml exec database mysql -u eventos_user -p{password} sistema_eventos"'
    run_command(cmd)

def logs_menu():
    """Menu de logs"""
    print(f"\n{Colors.BOLD}4. LOGS E MONITORAMENTO{Colors.END}")
    print(f"""
Opções:
  1) Logs de todos os serviços
  2) Logs do Frontend
  3) Logs do Backend Laravel
  4) Logs do Backend Python
  5) Logs do Banco de Dados
  6) Status dos containers
  7) Monitoramento de recursos (stats)
  8) Voltar
    """)
    
    choice = input(f"{Colors.CYAN}Escolha uma opção (1-8): {Colors.END}").strip()
    
    if choice == "1":
        remote_deploy("logs")
    elif choice == "2":
        remote_deploy("logs frontend")
    elif choice == "3":
        remote_deploy("logs backend-laravel")
    elif choice == "4":
        remote_deploy("logs backend-python")
    elif choice == "5":
        remote_deploy("logs database")
    elif choice == "6":
        remote_deploy("status")
    elif choice == "7":
        cmd = 'ssh ssh@177.44.248.118 "cd ~/projetos/sistema-eventos && docker stats"'
        run_command(cmd)
    elif choice == "8":
        return
    else:
        print_error("Opção inválida!")

def access_menu():
    """Menu de acesso"""
    print(f"\n{Colors.BOLD}5. ACESSO À APLICAÇÃO{Colors.END}")
    print(f"""
URLs da Aplicação:
  - Homepage:       http://177.44.248.118
  - Offline:        http://177.44.248.118/offline.html
  - API Status:     http://177.44.248.118/api/status
  - Mailhog:        http://177.44.248.118:8025

SSH da VM:
  ssh ssh@177.44.248.118
  Password: FsT#8723S

Próximas ações:
  1) Abrir aplicação no navegador
  2) Conectar via SSH
  3) Voltar
    """)
    
    choice = input(f"{Colors.CYAN}Escolha uma opção (1-3): {Colors.END}").strip()
    
    if choice == "1":
        print_info("Abrindo navegador...")
        os.system("start http://177.44.248.118")
    elif choice == "2":
        print_info("Conectando via SSH...")
        os.system("ssh ssh@177.44.248.118")
    elif choice == "3":
        return
    else:
        print_error("Opção inválida!")

def help_menu():
    """Menu de ajuda"""
    print(f"""
{Colors.BOLD}6. AJUDA E DOCUMENTAÇÃO{Colors.END}

Recursos disponíveis:

{Colors.BOLD}Documentação:{Colors.END}
  - REMOTE_DEPLOYMENT.md     Guia completo de deployment
  - DEPLOYMENT_CHECKLIST.md  Lista de verificação
  - README.md                Documentação geral
  - docker-compose.yml       Configuração dos containers

{Colors.BOLD}Scripts:{Colors.END}
  - deploy.sh                Script principal de deploy (na VM)
  - remote_deploy.py         Este script

{Colors.BOLD}Dúvidas Frequentes:{Colors.END}

Q: Como resetar o banco de dados?
R: Use "3. Banco de Dados" > "Fresh"

Q: Como ver logs de erro?
R: Use "4. Logs" > selecione o serviço

Q: Como fazer backup?
R: Use "3. Banco de Dados" > "Backup"

Q: Como conectar ao SSH?
R: ssh ssh@177.44.248.118 (senha: FsT#8723S)

Q: A aplicação não carrega, o que faço?
R: 1) Verifique "4. Logs"
   2) Execute "Health Check"
   3) Reinicie com "2. Deployment" > "Restart"
    """)

def main():
    """Menu principal"""
    while True:
        print_banner()
        print(f"""
{Colors.BOLD}MENU PRINCIPAL{Colors.END}

  1) Verificar Pré-requisitos
  2) Deployment
  3) Banco de Dados
  4) Logs e Monitoramento
  5) Acessar Aplicação
  6) Ajuda
  7) Sair

        """)
        
        choice = input(f"{Colors.CYAN}Escolha uma opção (1-7): {Colors.END}").strip()
        
        if choice == "1":
            setup_menu()
        elif choice == "2":
            deploy_menu()
        elif choice == "3":
            database_menu()
        elif choice == "4":
            logs_menu()
        elif choice == "5":
            access_menu()
        elif choice == "6":
            help_menu()
            input("\nPressione ENTER para continuar...")
        elif choice == "7":
            print_success("Até logo!")
            sys.exit(0)
        else:
            print_error("Opção inválida!")
        
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operação cancelada.{Colors.END}")
        sys.exit(0)
