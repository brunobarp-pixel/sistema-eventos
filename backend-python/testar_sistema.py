"""
Script de Testes Automatizados
Sistema de Eventos - Validação Completa
"""

import requests
import json
from datetime import datetime
import time

# URLs das APIs
LARAVEL_API = 'http://127.0.0.1:8000/api'
FLASK_API = 'http://127.0.0.1:5000'

# Cores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(texto):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"{texto}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(texto):
    print(f"{Colors.GREEN}✓ {texto}{Colors.END}")

def print_error(texto):
    print(f"{Colors.RED}✗ {texto}{Colors.END}")

def print_info(texto):
    print(f"{Colors.YELLOW}ℹ {texto}{Colors.END}")

def testar_conexao():
    print_header("TESTE 1: Verificando Conexões")
    # Laravel
    try:
        response = requests.get(f'{LARAVEL_API}/status', timeout=5)
        if response.status_code == 200:
            print_success("Laravel API está online (porta 8000)")
        else:
            print_error(f"Laravel retornou status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Laravel não está respondendo: {str(e)}")
        return False

    # Flask
    try:
        response = requests.get(f'{FLASK_API}/status', timeout=5)
        if response.status_code == 200:
            print_success("Flask API está online (porta 5000)")
        else:
            print_error(f"Flask retornou status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Flask não está respondendo: {str(e)}")
        return False

    return True

def testar_listar_eventos():
    print_header("TESTE 2: Listar Eventos")
    try:
        response = requests.get(f'{LARAVEL_API}/eventos')
        data = response.json()
        if data.get('success'):
            eventos = data['data']
            print_success(f"Encontrados {len(eventos)} eventos")
            for evento in eventos[:3]:
                print(f"   • {evento['titulo']} - {evento['local']}")
            return eventos
        else:
            print_error("Erro ao buscar eventos")
            return []
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return []

def testar_detalhes_evento(evento_id):
    print_header(f"TESTE 3: Ver Detalhes do Evento {evento_id}")
    try:
        response = requests.get(f'{LARAVEL_API}/eventos/{evento_id}')
        data = response.json()
        if data.get('success'):
            evento = data['data']
            print_success("Detalhes do evento recuperados")
            print(f"   Título: {evento['titulo']}")
            print(f"   Local: {evento['local']}")
            print(f"   Vagas disponíveis: {evento.get('vagas_disponiveis', evento.get('vagas', 'N/A'))}")
            return evento
        else:
            print_error("Erro ao buscar detalhes")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_cadastro_usuario(numero):
    """
    Agora esta função retorna uma tupla:
    (response_obj, usuario_data_dict_or_None)
    """
    print_header(f"TESTE 4: Cadastrar Participante {numero}")

    usuario_data = {
        'nome': f'Participante {numero}',
        'email': f'poiuy{numero}@teste.com',
        'senha': 'senha123',
        'cpf': f'{numero:03d}.456.456-00',
        'telefone': f'(51) 4242{numero:04d}'
    }

    try:
        response = requests.post(f'{LARAVEL_API}/usuarios', json=usuario_data, timeout=10)
        try:
            data = response.json()
        except ValueError:
            data = None

        if data and data.get('success'):
            print_success(f"Participante {numero} cadastrado com sucesso")
            print(f"   ID: {data['data']['id']}")
            print(f"   Nome: {data['data']['nome']}")
            return response, data['data']
        else:
            # Mostrar resposta bruta para diagnóstico
            print_error(f"Erro ao cadastrar: {data['message'] if data and 'message' in data else 'Erro de validação ou resposta inválida'}")
            print_info(f"Resposta bruta do servidor: {response.text}")
            return response, None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None, None

def testar_login(email, senha):
    print_header("TESTE 5: Realizar Login")
    try:
        response = requests.post(f'{LARAVEL_API}/auth', json={'email': email, 'senha': senha}, timeout=10)
        data = response.json()
        if data.get('success'):
            print_success("Login realizado com sucesso")
            print(f"   Usuário: {data['data']['usuario']['nome']}")
            print(f"   Token: {data['data']['token'][:20]}...")
            return data['data']
        else:
            print_error(f"Erro no login: {data.get('message')}")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_inscricao(usuario_id, evento_id):
    print_header(f"TESTE 6: Inscrever Usuário {usuario_id} no Evento {evento_id}")
    try:
        response = requests.post(f'{LARAVEL_API}/inscricoes', json={'usuario_id': usuario_id, 'evento_id': evento_id}, timeout=10)
        data = response.json()
        if data.get('success'):
            print_success("Inscrição realizada com sucesso")
            print(f"   ID da Inscrição: {data['data']['id']}")
            return data['data']
        else:
            print_error(f"Erro na inscrição: {data.get('message')}")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_presenca(inscricao_id):
    print_header(f"TESTE 7: Registrar Presença (Inscrição {inscricao_id})")
    try:
        response = requests.post(f'{LARAVEL_API}/presencas', json={'inscricao_id': inscricao_id}, timeout=10)
        try:
            data = response.json()
        except ValueError:
            data = None

        if data and data.get('success'):
            print_success("Presença registrada com sucesso")
            print(f"   ID da Presença: {data['data']['id']}")
            return data['data']
        else:
            print_error(f"Erro ao registrar presença: {data.get('message') if data else 'Resposta inválida'}")
            print_info(f"Resposta bruta do servidor: {response.text}")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_consulta_inscricao(inscricao_id):
    print_header(f"TESTE 8: Consultar Inscrição {inscricao_id}")
    try:
        response = requests.get(f'{LARAVEL_API}/inscricoes/{inscricao_id}', timeout=10)
        data = response.json()
        if data.get('success'):
            print_success("Inscrição encontrada")
            print(f"   Status: {data['data']['status']}")
            print(f"   Possui presença: {data['data'].get('possui_presenca')}")
            return data['data']
        else:
            print_error("Erro ao consultar inscrição")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_sistema_offline():
    print_header("TESTE 9: Sistema Offline")
    print_info("Cadastrando participante 3 (offline)...")
    try:
        response = requests.post(f'{FLASK_API}/usuarios', json={
            'nome': 'Participante 3 Offline',
            'email': 'participante3@teste.com',
            'cpf': '111.222.333-44',
            'telefone': '(51) 88888-8888'
        }, timeout=10)
        data = response.json()
        if data.get('success'):
            print_success("Participante cadastrado offline")
            usuario_offline_id = data['data']['id']
            print_info("Criando inscrição offline...")
            response = requests.post(f'{FLASK_API}/inscricoes', json={'usuario_id': usuario_offline_id, 'evento_id': 1}, timeout=10)
            data = response.json()
            if data.get('success'):
                print_success("Inscrição criada offline")
                inscricao_offline_id = data['data']['id']
                print_info("Registrando presença offline...")
                response = requests.post(f'{FLASK_API}/presencas', json={'inscricao_id': inscricao_offline_id}, timeout=10)
                data = response.json()
                if data.get('success'):
                    print_success("Presença registrada offline")
                    return True
        return False
    except Exception as e:
        print_error(f"Erro no sistema offline: {str(e)}")
        return False

def testar_dados_pendentes():
    print_header("TESTE 10: Dados Pendentes de Sincronização")
    try:
        response = requests.get(f'{FLASK_API}/dados-pendentes', timeout=10)
        data = response.json()
        if data.get('success'):
            total = data['data']['total_pendente']
            print_success(f"Total de dados pendentes: {total}")
            print(f"   • Usuários: {len(data['data']['usuarios'])}")
            print(f"   • Inscrições: {len(data['data']['inscricoes'])}")
            print(f"   • Presenças: {len(data['data']['presencas'])}")
            return data['data']
        else:
            print_error("Erro ao consultar dados pendentes")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_certificado(usuario_id, evento_id):
    print_header("TESTE 11: Emitir Certificado")
    try:
        response = requests.post(f'{LARAVEL_API}/certificados', json={'usuario_id': usuario_id, 'evento_id': evento_id}, timeout=10)
        data = response.json()
        if data.get('success'):
            print_success("Certificado emitido com sucesso")
            print(f"   Código: {data['data']['codigo_validacao'][:20]}...")
            return data['data']
        else:
            print_error(f"Erro ao emitir certificado: {data.get('message')}")
            return None
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return None

def testar_validacao_certificado(codigo):
    print_header("TESTE 12: Validar Certificado")
    try:
        response = requests.get(f'{LARAVEL_API}/certificados/{codigo}', timeout=10)
        data = response.json()
        if data.get('success') and data.get('valido'):
            print_success("Certificado válido!")
            print(f"   Participante: {data['data']['participante']['nome']}")
            print(f"   Evento: {data['data']['evento']['titulo']}")
            return True
        else:
            print_error("Certificado inválido")
            return False
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return False

def testar_cancelamento(inscricao_id):
    print_header(f"TESTE 13: Cancelar Inscrição {inscricao_id}")
    try:
        response = requests.delete(f'{LARAVEL_API}/inscricoes/{inscricao_id}', timeout=10)
        data = response.json()
        if data.get('success'):
            print_success("Inscrição cancelada com sucesso")
            return True
        else:
            print_error(f"Erro ao cancelar: {data.get('message')}")
            return False
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return False

# ==========================================
# ROTEIRO COMPLETO DE TESTES
# ==========================================

def executar_testes_completos():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     TESTES AUTOMATIZADOS - SISTEMA DE EVENTOS             ║")
    print("║                                                           ║")
    print("║  Este script valida todos os endpoints e funcionalidades ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    participante1 = None
    participante2 = None
    evento = None
    inscricao1 = None
    inscricao2 = None
    certificado = None

    if not testar_conexao():
        print_error("\n❌ Servidores não estão rodando! Execute:")
        print("   Terminal 1: php artisan serve")
        print("   Terminal 2: python app.py")
        return

    eventos = testar_listar_eventos()
    if eventos:
        evento = eventos[0]
    else:
        print_error("Nenhum evento encontrado!")
        return

    testar_detalhes_evento(evento['id'])

    # Etapa 4: Cadastrar participante 1
    response_r, participante1 = testar_cadastro_usuario(1)
    if response_r is not None:
        print("Resposta do servidor:", response_r.text)
    else:
        print("Resposta do servidor: (nenhuma resposta)")

    if not participante1:
        return

    # Etapa 5: Login participante 1
    login1 = testar_login(participante1['email'], 'senha123')
    if not login1:
        return

    # Etapa 6: Inscrever participante 1
    inscricao1 = testar_inscricao(participante1['id'], evento['id'])
    if not inscricao1:
        return

    # Etapa 7: Registrar presença participante 1
    presenca1 = testar_presenca(inscricao1['id'])
    if not presenca1:
        return

    # Etapa 8: Demonstrar que presença foi registrada
    testar_consulta_inscricao(inscricao1['id'])

    print_header("🔄 INICIANDO TESTES OFFLINE")

    # Etapa 9: Cadastrar participante 2 (online)
    response_r2, participante2 = testar_cadastro_usuario(2)
    if response_r2 is not None:
        print("Resposta do servidor (part2):", response_r2.text)
    if not participante2:
        # se falhou no cadastro 2, não interrompe completamente; segue testes offline
        print_info("Falha em cadastrar participante 2; seguindo com testes offline onde aplicável.")

    # Etapa 10: Inscrever participante 2
    if participante2:
        inscricao2 = testar_inscricao(participante2['id'], evento['id'])

    testar_sistema_offline()
    testar_dados_pendentes()

    print_header("🏆 TESTANDO CERTIFICADOS")

    if participante1:
        certificado = testar_certificado(participante1['id'], evento['id'])
        if certificado:
            testar_validacao_certificado(certificado['codigo_validacao'])

    if inscricao2:
        testar_cancelamento(inscricao2['id'])

    print_header("📊 RESUMO DOS TESTES")
    print_success("Todos os testes principais foram executados!")
    print_info("Verifique os resultados acima para detalhes")
    print_info("Consulte o banco de dados para confirmar persistência")

if __name__ == '__main__':
    try:
        executar_testes_completos()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Testes interrompidos pelo usuário{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Erro fatal: {str(e)}{Colors.END}")
