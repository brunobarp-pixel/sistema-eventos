import os
import threading
import time
import mysql.connector
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from email_service import enviar_email, enviar_email_inscricao, enviar_email_certificado
from gerador_pdf import GeradorPDF
from laravel_auth_service import LaravelAuthService

app = Flask(__name__)
CORS(app)

# Configurações
MYSQL_CONFIG = {
    "host": "db",
    "user": "eventos_user", 
    "password": "eventos_pass_123",
    "database": "sistema_eventos",
}

# Token fixo para o sistema offline
SISTEMA_OFFLINE_TOKEN = "sistema_offline_token_2025_abcdef123456"

# Instâncias globais
gerador_pdf = GeradorPDF()
laravel_auth = LaravelAuthService()
sync_ativo = False
sync_thread = None


def popular_dados_exemplo():
    """Popular dados de exemplo no MySQL se estiver vazio"""
    try:
        conn = get_mysql_connection()
        if not conn:
            print("❌ Não foi possível conectar ao MySQL para popular dados")
            return
            
        cursor = conn.cursor()
        
        # Verificar se já tem eventos
        cursor.execute("SELECT COUNT(*) FROM eventos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📋 Populando dados de exemplo no MySQL...")
            
            # Adicionar eventos de exemplo
            eventos_exemplo = [
                ("Workshop Laravel", "Introdução ao desenvolvimento com Laravel", 
                 "2025-12-15 09:00:00", "2025-12-15 17:00:00", "Laboratório 1", 30, "aberto"),
                ("Palestra Docker", "Containerização com Docker", 
                 "2025-12-20 14:00:00", "2025-12-20 16:00:00", "Auditório", 50, "aberto"),
                ("Curso JavaScript", "JavaScript moderno e frameworks", 
                 "2026-01-10 08:00:00", "2026-01-12 18:00:00", "Sala 201", 25, "aberto"),
                ("Workshop React", "Desenvolvimento Frontend com React", 
                 "2025-12-01 14:00:00", "2025-12-01 18:00:00", "Laboratório 2", 20, "aberto"),
                ("Palestra sobre IA", "Inteligência Artificial e Machine Learning", 
                 "2025-12-15 09:00:00", "2025-12-15 12:00:00", "Auditório", 60, "aberto")
            ]
            
            for evento in eventos_exemplo:
                cursor.execute("""
                    INSERT INTO eventos 
                    (titulo, descricao, data_inicio, data_fim, local, vagas, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, evento)
            
            # Adicionar usuário do sistema permanente
            cursor.execute("""
                INSERT IGNORE INTO usuarios 
                (nome, email, cpf, telefone, senha)
                VALUES 
                ('Sistema Offline', 'sistema.offline@eventos.com', '00000000000', '(00)00000-0000', 'sistema_offline_2025'),
                ('Usuário Teste', 'teste@exemplo.com', '12345678901', '(51)99999-9999', 'senha123')
            """)
            
            conn.commit()
            print("✅ Dados de exemplo populados no MySQL!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao popular dados de exemplo: {str(e)}")


def validar_token_sistema(request):
    """Validar se o request tem o token do sistema válido"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
        
    try:
        token = auth_header.replace('Bearer ', '')
        return token == SISTEMA_OFFLINE_TOKEN
    except:
        return False


def get_mysql_connection():
    """Conectar ao MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar MySQL: {str(e)}")
        return None


def iniciar_sync_automatico():
    """Iniciar thread de sincronização automática"""
    global sync_ativo, sync_thread
    
    if sync_ativo:
        print("⚠️ Sync já está ativo")
        return
        
    sync_ativo = True
    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
    print("🔄 Sincronização automática iniciada")


def sync_loop():
    """Loop principal de sincronização"""
    global sync_ativo
    
    while sync_ativo:
        try:
            if laravel_auth.is_authenticated():
                print("🔄 Executando sincronização automática...")
                # Aqui pode adicionar sincronização se necessário
                
        except Exception as e:
            print(f"❌ Erro na sincronização: {str(e)}")
            
        time.sleep(300)  # 5 minutos


@app.route("/login-laravel", methods=["POST"])
def login_laravel():
    """Fazer login no Laravel"""
    data = request.get_json()
    
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({
            "success": False,
            "message": "Email e senha são obrigatórios"
        }), 400
    
    success = laravel_auth.login(data["email"], data["password"])
    
    if success:
        return jsonify({
            "success": True,
            "message": "Login realizado com sucesso",
            "token": laravel_auth.token
        })
    else:
        return jsonify({
            "success": False,
            "message": "Credenciais inválidas"
        }), 401


@app.route("/auth-status", methods=["GET"])
def auth_status():
    """Verificar status da autenticação"""
    return jsonify({
        "authenticated": laravel_auth.is_authenticated(),
        "token": laravel_auth.token if laravel_auth.is_authenticated() else None
    })


@app.route("/sistema-token", methods=["GET"])
def sistema_token():
    """Obter token fixo do sistema para autenticação offline"""
    return jsonify({
        "success": True,
        "token": SISTEMA_OFFLINE_TOKEN,
        "usuario": {
            "id": 1,
            "nome": "Sistema Offline",
            "email": "sistema.offline@eventos.com",
            "tipo": "sistema"
        },
        "message": "Token do sistema obtido com sucesso"
    })


@app.route("/validar-token", methods=["POST"])
def validar_token():
    """Validar se o token é válido"""
    data = request.get_json()
    token = data.get('token') if data else None
    
    if token == SISTEMA_OFFLINE_TOKEN:
        return jsonify({
            "success": True,
            "valid": True,
            "usuario": {
                "id": 1,
                "nome": "Sistema Offline",
                "email": "sistema.offline@eventos.com"
            }
        })
    else:
        return jsonify({
            "success": False,
            "valid": False,
            "message": "Token inválido"
        }), 401


@app.route("/status", methods=["GET"])
def status():
    """Status geral do sistema"""
    mysql_ok = get_mysql_connection() is not None
    
    return jsonify({
        "status": "online",
        "mysql": mysql_ok,
        "laravel_auth": laravel_auth.is_authenticated(),
        "sync_ativo": sync_ativo
    })


@app.route("/usuarios", methods=["GET", "POST", "OPTIONS"])
def usuarios():
    """Gerenciar usuários"""
    if request.method == "OPTIONS":
        return "", 204
        
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable"}), 500
        
    try:
        if request.method == "GET":
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios ORDER BY nome")
            usuarios = cursor.fetchall()
            return jsonify({
                "success": True,
                "data": usuarios
            })
            
        elif request.method == "POST":
            data = request.get_json()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO usuarios (nome, email, cpf, telefone, senha, data_nascimento)
                VALUES (%(nome)s, %(email)s, %(cpf)s, %(telefone)s, %(senha)s, %(data_nascimento)s)
            """, data)
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Usuário cadastrado com sucesso",
                "id": cursor.lastrowid
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500
    finally:
        conn.close()


@app.route("/inscricoes", methods=["GET", "POST", "OPTIONS"])
def inscricoes():
    """Gerenciar inscrições"""
    if request.method == "OPTIONS":
        return "", 204
        
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable"}), 500
        
    try:
        if request.method == "GET":
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT i.*, u.nome as usuario_nome, e.titulo as evento_titulo
                FROM inscricoes i
                JOIN usuarios u ON i.usuario_id = u.id  
                JOIN eventos e ON i.evento_id = e.id
                ORDER BY i.criado_em DESC
            """)
            inscricoes = cursor.fetchall()
            return jsonify({
                "success": True,
                "data": inscricoes
            })
            
        elif request.method == "POST":
            data = request.get_json()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO inscricoes (usuario_id, evento_id, status)
                VALUES (%(usuario_id)s, %(evento_id)s, 'ativa')
            """, data)
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Inscrição realizada com sucesso",
                "id": cursor.lastrowid
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500
    finally:
        conn.close()


@app.route("/eventos", methods=["GET", "OPTIONS"])
def eventos():
    """Listar eventos"""
    if request.method == "OPTIONS":
        return "", 204
        
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable"}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, 
                   COUNT(i.id) as total_inscritos
            FROM eventos e
            LEFT JOIN inscricoes i ON e.id = i.evento_id AND i.status = 'ativa'
            GROUP BY e.id
            ORDER BY e.data_inicio
        """)
        eventos = cursor.fetchall()
        
        return jsonify({
            "success": True,
            "data": eventos
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500
    finally:
        conn.close()


@app.route("/presencas", methods=["GET", "POST", "OPTIONS"])
def presencas():
    """Gerenciar presenças"""
    if request.method == "OPTIONS":
        return "", 204
        
    conn = get_mysql_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable"}), 500
        
    try:
        if request.method == "GET":
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.*, u.nome as usuario_nome, e.titulo as evento_titulo
                FROM presencas p
                JOIN inscricoes i ON p.inscricao_id = i.id
                JOIN usuarios u ON i.usuario_id = u.id
                JOIN eventos e ON i.evento_id = e.id
                ORDER BY p.criado_em DESC
            """)
            presencas = cursor.fetchall()
            return jsonify({
                "success": True,
                "data": presencas
            })
            
        elif request.method == "POST":
            data = request.get_json()
            inscricao_id = data.get("inscricao_id")
            
            if not inscricao_id:
                return jsonify({
                    "success": False,
                    "message": "inscricao_id é obrigatório"
                }), 400
                
            cursor = conn.cursor()
            
            # Verificar se inscrição existe
            cursor.execute("SELECT * FROM inscricoes WHERE id = %s AND status = 'ativa'", (inscricao_id,))
            inscricao = cursor.fetchone()
            
            if not inscricao:
                return jsonify({
                    "success": False,
                    "message": "Inscrição não encontrada ou inativa"
                }), 404
                
            # Verificar se já tem presença
            cursor.execute("SELECT id FROM presencas WHERE inscricao_id = %s", (inscricao_id,))
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Presença já registrada"
                }), 400
                
            # Registrar presença
            cursor.execute("""
                INSERT INTO presencas (inscricao_id)
                VALUES (%s)
            """, (inscricao_id,))
            
            conn.commit()
            presenca_id = cursor.lastrowid
            
            # Gerar certificado automaticamente
            try:
                # Buscar dados para o certificado
                cursor.execute("""
                    SELECT u.nome, e.titulo, e.data_inicio, e.data_fim
                    FROM inscricoes i
                    JOIN usuarios u ON i.usuario_id = u.id
                    JOIN eventos e ON i.evento_id = e.id
                    WHERE i.id = %s
                """, (inscricao_id,))
                
                cert_data = cursor.fetchone()
                if cert_data:
                    nome, evento, data_inicio, data_fim = cert_data
                    
                    certificado_path = gerador_pdf.gerar_certificado({
                        'nome_participante': nome,
                        'nome_evento': evento,
                        'data_inicio': data_inicio,
                        'data_fim': data_fim
                    })
                    
                    # Salvar certificado no banco
                    cursor.execute("""
                        INSERT INTO certificados (inscricao_id, caminho_arquivo)
                        VALUES (%s, %s)
                    """, (inscricao_id, certificado_path))
                    conn.commit()
                    
                    print(f"✅ Certificado gerado: {certificado_path}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao gerar certificado: {str(e)}")
            
            return jsonify({
                "success": True,
                "message": "Presença registrada com sucesso",
                "id": presenca_id
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500
    finally:
        conn.close()


@app.route("/enviar-email-inscricao", methods=["POST"])
def enviar_email_inscricao():
    """Enviar email de confirmação de inscrição"""
    data = request.get_json()
    
    try:
        enviar_email_inscricao(
            {
                "nome": data["nome"],
                "email": data["email"]
            },
            data["evento"]
        )
        
        return jsonify({
            "success": True,
            "message": "Email enviado com sucesso"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao enviar email: {str(e)}"
        }), 500


@app.route("/enviar-email-certificado", methods=["POST"])
def enviar_email_certificado():
    """Enviar email com certificado"""
    data = request.get_json()
    
    try:
        enviar_email_certificado(
            {
                "nome": data["nome"],
                "email": data["email"]
            },
            data["evento"],
            data.get("certificado_path")
        )
        
        return jsonify({
            "success": True,
            "message": "Email com certificado enviado"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao enviar email: {str(e)}"
        }), 500


@app.route("/gerar-certificado-pdf", methods=["POST"])
def gerar_certificado_pdf():
    """Gerar certificado PDF"""
    data = request.get_json()
    
    try:
        certificado_path = gerador_pdf.gerar_certificado(data)
        
        return jsonify({
            "success": True,
            "message": "Certificado gerado com sucesso",
            "path": certificado_path
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao gerar certificado: {str(e)}"
        }), 500


@app.route("/download-pdf/<path:filename>", methods=["GET"])
def download_pdf(filename):
    """Download de arquivo PDF"""
    try:
        file_path = os.path.join("certificados_pdf", filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "Arquivo não encontrado"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Criar pastas
    if not os.path.exists("certificados_pdf"):
        os.makedirs("certificados_pdf")
        print("📁 Pasta 'certificados_pdf' criada!")

    # Popular dados de exemplo se necessário
    print("\n📋 Verificando dados de exemplo...")
    popular_dados_exemplo()

    # Login automático no Laravel
    print("\n🔐 Tentando login automático no Laravel...")
    if laravel_auth.login('sistema@eventos.com', 'senha_sistema_2025'):
        print("✅ Autenticado com Laravel!")
    else:
        print("⚠️ Laravel offline - usando modo MySQL direto")

    # Iniciar sincronização automática
    print("\n🔄 Iniciando sincronização automática...")
    iniciar_sync_automatico()

    # Rodar aplicação
    print("\n🚀 Sistema Python iniciado!")
    print("🔐 Laravel autenticado:", laravel_auth.is_authenticated())
    print("🔄 Sincronização automática: ATIVA")
    print("💾 Usando MySQL diretamente (sem SQLite)\n")

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)