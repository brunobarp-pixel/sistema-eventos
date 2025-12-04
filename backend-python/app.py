import os
import sys
import threading
import time
import mysql.connector
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from email_service import enviar_email, enviar_email_inscricao, enviar_email_certificado, enviar_email_checkin, enviar_email_cancelamento        
from gerador_pdf import gerar_certificado_pdf
import laravel_auth_service

app = Flask(__name__)

CORS(app, #isso e nem um pouco seguro, rever depois
     origins=["*"],  # Permite todas as origens
     allow_headers=["*"],  # Permite todos os headers
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Métodos permitidos
     supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
MYSQL_CONFIG = {
    "host": "database",
    "user": "eventos_user",
    "password": "eventos_pass_123",
    "database": "sistema_eventos",
}

SISTEMA_OFFLINE_TOKEN = "sistema_offline_token_2025_abcdef123456"

sync_ativo = False
sync_thread = None
laravel_auth = laravel_auth_service.LaravelAuth() 


def popular_dados_exemplo():
    try:
        conn = get_mysql_connection() 
        if not conn:
            print("Não foi possível conectar ao MySQL")
            return
            
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM eventos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Populando dados de exemplo no MySQL...")
            
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
            
            cursor.execute("""
                INSERT IGNORE INTO usuarios 
                (nome, email, cpf, telefone, senha)
                VALUES 
                ('Sistema Offline', 'sistema.offline@eventos.com', '00000000000', '(00)00000-0000', 'sistema_offline_2025'),
                ('Usuário Teste', 'teste@exemplo.com', '12345678901', '(51)99999-9999', 'senha123')
            """)
            
            conn.commit()
            print("Dados de exemplo populados no MySQL!")
            
        conn.close()
        
    except Exception as e:
        print(f"Erro ao popular dados de exemplo: {str(e)}")


def validar_token_sistema(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
        
    try:
        token = auth_header.replace('Bearer ', '')
        return token == SISTEMA_OFFLINE_TOKEN
    except:
        return False


def get_mysql_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar MySQL: {str(e)}")
        return None


def iniciar_sync_automatico():
    global sync_ativo, sync_thread
    
    if sync_ativo:
        print("Sync já está ativo")
        return
        
    sync_ativo = True
    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
    print("Sincronização automática iniciada")


def sync_loop():
    global sync_ativo
    
    while sync_ativo:
        try:
            if laravel_auth.is_authenticated():
                print("Executando sincronização automática...")
                
        except Exception as e:
            print(f"Erro na sincronização: {str(e)}")
            
        time.sleep(300)  


@app.route("/login-laravel", methods=["POST"])
def login_laravel():
    data = request.get_json()
    
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({
            "success": False,
            "message": "Email e senha são obrigatórios"
        }), 400
    
    return jsonify({
        "success": True,
        "message": "Login realizado com sucesso",
        "token": SISTEMA_OFFLINE_TOKEN
    })


@app.route("/auth-status", methods=["GET"])
def auth_status():
    """Verificar status da autenticação"""
    return jsonify({
        "authenticated": True,  # Sistema usa token fixo
        "token": SISTEMA_OFFLINE_TOKEN
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
    # Tentar obter token do header 
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        data = request.get_json()
        token = data.get('token') if data else None
    
    if not token:
        return jsonify({
            "success": False,
            "valid": False,
            "message": "Token não fornecido"
        }), 400
    
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
    mysql_ok = get_mysql_connection() is not None
    
    return jsonify({
        "status": "online",
        "mysql": mysql_ok,
        "sistema_token": "ativo",
        "sync_ativo": sync_ativo
    })


@app.route("/dados-pendentes", methods=["GET", "OPTIONS"]) #Tentar rever isso aqui
def dados_pendentes():
    try:
        return jsonify({
            "success": True,
            "dados": {
                "usuarios_pendentes": 0,
                "inscricoes_pendentes": 0,
                "presencas_pendentes": 0,
                "total_pendentes": 0
            },
            "message": "Dados pendentes obtidos com sucesso"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao obter dados pendentes: {str(e)}"
        }), 500


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
                SELECT i.*, u.nome as usuario_nome, e.nome as evento_titulo
                FROM inscricoes i
                JOIN usuarios u ON i.usuario_id = u.id  
                JOIN eventos e ON i.evento_id = e.id
                ORDER BY i.created_at DESC
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
                SELECT p.*, u.nome as usuario_nome, e.nome as evento_titulo
                FROM presencas p
                JOIN inscricoes i ON p.inscricao_id = i.id
                JOIN usuarios u ON i.usuario_id = u.id
                JOIN eventos e ON i.evento_id = e.id
                ORDER BY p.created_at DESC
            """)
            presencas = cursor.fetchall()
            return jsonify({
                "success": True,
                "data": presencas
            })
            
        elif request.method == "POST":
            print(f"Recebendo POST para /presencas")
            print(f"Content-Type: {request.content_type}")
            print(f"Headers: {dict(request.headers)}")
            print(f"Raw data: {request.get_data()}")
            
            try:
                if request.is_json:
                    data = request.get_json()
                    print(f"JSON via is_json: {data}")
                else:
                    data = request.get_json(force=True)
                    print(f"JSON via force=True: {data}")
                
                if not data:
                    print("Nenhum JSON válido encontrado")
                    return jsonify({
                        "success": False,
                        "message": "Dados JSON inválidos ou ausentes"
                    }), 400
                    
            except Exception as e:
                print(f"Erro ao fazer parse do JSON: {e}")
                return jsonify({
                    "success": False,
                    "message": f"Erro ao fazer parse do JSON: {str(e)}"
                }), 400
                
            inscricao_id = data.get("inscricao_id")
            evento_id = data.get("evento_id")
            usuario_id = data.get("usuario_id")
            
            if not inscricao_id:
                return jsonify({
                    "success": False,
                    "message": "inscricao_id é obrigatório"
                }), 400
                
            if not evento_id:
                return jsonify({
                    "success": False,
                    "message": "evento_id é obrigatório"
                }), 400
                
            if not usuario_id:
                return jsonify({
                    "success": False,
                    "message": "usuario_id é obrigatório"
                }), 400
                
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM inscricoes WHERE id = %s AND status = 'confirmada'", (inscricao_id,))
            inscricao = cursor.fetchone()
            
            if not inscricao:
                return jsonify({
                    "success": False,
                    "message": "Inscrição não encontrada ou inativa"
                }), 404
                
            cursor.execute("SELECT id FROM presencas WHERE inscricao_id = %s", (inscricao_id,))
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Presença já registrada"
                }), 400
                
            cursor.execute("""
                INSERT INTO presencas (inscricao_id, evento_id, usuario_id, data_checkin)
                VALUES (%s, %s, %s, NOW())
            """, (inscricao_id, evento_id, usuario_id))
            
            conn.commit()
            presenca_id = cursor.lastrowid
            
            cursor.execute("""
                SELECT u.nome, u.email, e.nome as titulo, e.data_inicio, e.data_fim
                FROM inscricoes i
                JOIN usuarios u ON i.usuario_id = u.id
                JOIN eventos e ON i.evento_id = e.id
                WHERE i.id = %s
            """, (inscricao_id,))
            
            dados = cursor.fetchone()
            if dados:
                nome, email, evento_titulo, data_inicio, data_fim = dados
                
                try:
                    certificado_path = gerar_certificado_pdf({
                        'nome_participante': nome,
                        'evento_titulo': evento_titulo,
                        'data_inicio': data_inicio,
                        'data_fim': data_fim,
                        'codigo_validacao': f'CERT_{inscricao_id}_{int(time.time())}',
                        'data_emissao': datetime.now().strftime('%Y-%m-%d')
                    }, "certificados_pdf")
                    
                    cursor.execute("""
                        INSERT INTO certificados (inscricao_id, caminho_arquivo)
                        VALUES (%s, %s)
                    """, (inscricao_id, certificado_path))
                    conn.commit()
                    
                    print(f"Certificado gerado: {certificado_path}")
                    
                except Exception as e:
                    print(f"Erro ao gerar certificado: {str(e)}")
                
                try:
                    enviar_email_checkin(
                        {"nome": nome, "email": email},
                        {"nome": evento_titulo}
                    )
                    print(f"Email de check-in enviado para {email}")
                    
                except Exception as e:
                    print(f"Erro ao enviar email de check-in: {str(e)}")
            
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
def endpoint_enviar_email_inscricao():
    try:
        # Logs
        print(f"Headers: {dict(request.headers)}")
        print(f"Content-Type: {request.content_type}")
        print(f"Raw data: {request.get_data()}")
        
        data = request.get_json()
        print(f"Parsed JSON: {data}")
        
        # Garantir compatibilidade, torcer para nao dar pau
        evento = data["evento"].copy()
        if "titulo" in evento and "nome" not in evento:
            evento["nome"] = evento["titulo"]
        
        enviar_email_inscricao(
            {
                "nome": data["usuario"]["nome"],
                "email": data["usuario"]["email"]
            },
            evento
        )
        
        return jsonify({
            "success": True,
            "message": "Email de inscrição enviado com sucesso"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao enviar email de inscrição: {str(e)}"
        }), 500


@app.route("/enviar-email-checkin", methods=["POST"])
def endpoint_enviar_email_checkin():
    """Enviar email de confirmação de check-in/presença"""
    data = request.get_json()
    
    try:
        # Garantir compatibilidade, torcer para nao dar pau
        evento = data["evento"].copy()
        if "titulo" in evento and "nome" not in evento:
            evento["nome"] = evento["titulo"]
        
        enviar_email_checkin(
            {
                "nome": data["usuario"]["nome"],
                "email": data["usuario"]["email"]
            },
            evento
        )
        
        return jsonify({
            "success": True,
            "message": "Email de check-in enviado com sucesso"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao enviar email de check-in: {str(e)}"
        }), 500


@app.route("/enviar-email-cancelamento", methods=["POST"])
def endpoint_enviar_email_cancelamento():
    try:
        print(f"Headers: {dict(request.headers)}")
        print(f"Content-Type: {request.content_type}")
        print(f"Raw data: {request.get_data()}")
        
        data = request.get_json()
        print(f"Parsed JSON: {data}")
        
        evento = data["evento"].copy()
        if "titulo" in evento and "nome" not in evento:
            evento["nome"] = evento["titulo"]
        
        usuario = {
            "nome": data["usuario"]["nome"],
            "email": data["usuario"]["email"]
        }
        
        enviar_email_cancelamento(usuario, evento)
        
        return jsonify({
            "success": True,
            "message": "Email de cancelamento enviado com sucesso"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao enviar email de cancelamento: {str(e)}"
        }), 500


@app.route("/enviar-email-certificado", methods=["POST"]) #rever isso aqui tbm
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


@app.route("/gerar-certificado-pdf", methods=["POST"])#rever isso aqui tbm
def gerar_certificado_endpoint():
    """Gerar certificado PDF"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados não fornecidos"
            }), 400
        
        print(f"Dados recebidos para gerar PDF: {data}")
        
        # Validar campos obrigatórios
        required_fields = ['nome_participante', 'evento_titulo', 'codigo_validacao', 'data_inicio', 'data_fim', 'local', 'data_emissao']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
            }), 400
        
        certificado_path = gerar_certificado_pdf(data, "certificados_pdf")
        
        nome_arquivo = os.path.basename(certificado_path)
        
        print(f"Certificado gerado: {certificado_path}")
        print(f"Nome do arquivo: {nome_arquivo}")
        
        return jsonify({
            "success": True,
            "message": "Certificado gerado com sucesso",
            "pdf_path": nome_arquivo,
            "full_path": certificado_path
        })
        
    except Exception as e:
        print(f"Erro ao gerar certificado: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Erro ao gerar certificado: {str(e)}"
        }), 500


@app.route("/download-pdf/<path:filename>", methods=["GET"])
def download_pdf(filename):
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
        print("Pasta 'certificados_pdf' criada!") 

    print("\nVerificando dados de exemplo...")
    popular_dados_exemplo()

    print("\nIniciando sincronização automática...")
    iniciar_sync_automatico()

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)