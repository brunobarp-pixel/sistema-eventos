from email_service import (
    enviar_email_inscricao,
    enviar_email_cancelamento,
    enviar_email_checkin,
)
import sqlite3
from datetime import datetime
import json
import os
import requests
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from datetime import datetime
import os
from sync_manager import sync_manager, iniciar_sync_automatico, sincronizar_agora, get_sync_status

from laravel_auth_service import laravel_auth, laravel_get, laravel_post, laravel_put, laravel_delete

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)



# Configurações
DATABASE = "data/eventos.db"
LARAVEL_API = "http://backend-laravel/api"

# ==========================================
# FUNÇÕES DO BANCO DE DADOS
# ==========================================


def get_db():
    """Conecta ao banco SQLite"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa o banco de dados local"""
    conn = get_db()
    cursor = conn.cursor()

    # Tabela de usuários (offline)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios_offline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            cpf TEXT,
            telefone TEXT,
            senha TEXT NOT NULL,
            dados_completos INTEGER DEFAULT 0,
            sincronizado INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Tabela de eventos (cache)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS eventos_cache (
            id INTEGER PRIMARY KEY,
            titulo TEXT NOT NULL,
            descricao TEXT,
            data_inicio TEXT,
            data_fim TEXT,
            local TEXT,
            vagas INTEGER,
            status TEXT,
            sincronizado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Tabela de inscrições (offline)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inscricoes_offline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            evento_id INTEGER,
            status TEXT DEFAULT 'ativa',
            sincronizado INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    
    # Tabela de presenças (offline)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS presencas_offline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inscricao_id INTEGER,
            usuario_id INTEGER,
            evento_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()
    print("✅ Banco de dados local inicializado!")
    
    
@app.route("/login-laravel", methods=["POST"])
def login_laravel():
    """Login no Laravel para obter token"""
    try:
        data = request.json
        email = data.get('email')
        senha = data.get('senha')
        
        if not email or not senha:
            return jsonify({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        # Fazer login
        if laravel_auth.login(email, senha):
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'data': {
                    'user': laravel_auth.user_data,
                    'token': laravel_auth.token
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Credenciais inválidas'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route("/auth-status", methods=["GET"])
def auth_status():
    """Verifica status da autenticação"""
    return jsonify({
        'success': True,
        'authenticated': laravel_auth.is_authenticated(),
        'user': laravel_auth.user_data if laravel_auth.is_authenticated() else None
    })


# ==========================================
# ENDPOINTS DA API OFFLINE
# ==========================================


@app.route("/status", methods=["GET"])
def status():
    return jsonify(
        {
            "success": True,
            "message": "Sistema offline funcionando!",
            "timestamp": datetime.now().isoformat(),
            "laravel_authenticated": laravel_auth.is_authenticated()
        }
    )

@app.route("/usuarios", methods=["GET", "POST", "OPTIONS"])
def usuarios():
    """
    GET: Lista usuários
    POST: Cadastro rápido de usuário (offline)
    """
    
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return response
    
    if request.method == "GET":
        try:
            todosUsuarios = []
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios_offline")
            usuarios_offline = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # ✅ USAR AUTENTICAÇÃO
            try:
                if laravel_auth.is_authenticated():
                    resp = laravel_get('/usuarios')
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('success'):
                            usuarios_online = data.get('data', [])
                            for u_online in usuarios_online:
                                if not any(u['email'] == u_online['email'] for u in usuarios_offline):
                                    todosUsuarios.append(u_online)
            except:
                pass  
            
            todosUsuarios.extend(usuarios_offline)
            
            return jsonify({
                "success": True,
                "data": todosUsuarios
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Erro ao buscar usuários: {str(e)}"
            }), 500
    
    if request.method == "POST":
        try:
            data = request.json

            if not data.get("nome") or not data.get("email"):
                return jsonify({
                    "success": False,
                    "message": "Nome e email são obrigatórios"
                }), 400

            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM usuarios_offline WHERE email = ?", (data["email"],)
            )
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    "success": False,
                    "message": "Email já cadastrado"
                }), 400

            senha_padrao = 'senha123'

            cursor.execute(
                """
                INSERT INTO usuarios_offline (nome, email, cpf, telefone, senha, dados_completos)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    data["nome"],
                    data["email"],
                    data.get("cpf", ""),
                    data.get("telefone", ""),
                    senha_padrao,
                    1 if data.get("cpf") and data.get("telefone") else 0,
                ),
            )

            usuario_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"✅ Usuário cadastrado offline: {data['nome']} (senha padrão: senha123)")

            return jsonify({
                "success": True,
                "message": "Usuário cadastrado (offline). Senha padrão: senha123",
                "data": {
                    "id": usuario_id,
                    "nome": data["nome"],
                    "email": data["email"],
                    "sincronizado": False,
                    "senha_padrao": "senha123",
                },
            }), 201

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Erro ao cadastrar: {str(e)}"
            }), 500
        

@app.route("/inscricoes", methods=["GET", "POST", "OPTIONS"])
def inscricoes():
    """
    GET: Lista inscrições
    POST: Criar inscrição offline
    """
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    if request.method == "GET":
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Buscar inscrições offline
            cursor.execute("SELECT * FROM inscricoes_offline ORDER BY id DESC")
            inscricoes_offline = [dict(row) for row in cursor.fetchall()]
            
            # Tentar buscar do Laravel também
            todasInscricoes = inscricoes_offline.copy()
            
            try:
                token = request.headers.get("Authorization")
                
                headers = {}
                if token:
                    headers["Authorization"] = token
                
                resp = requests.get(
                    f"{LARAVEL_API}/inscricoes",
                    headers=headers,
                    timeout=3
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    inscricoes_online = data.get('data', [])
                    
                    # Adicionar apenas inscrições que não estão no offline
                    for insc_online in inscricoes_online:
                        if not any(
                            insc['usuario_id'] == insc_online['usuario_id'] and 
                            insc['evento_id'] == insc_online['evento_id'] 
                            for insc in inscricoes_offline
                        ):
                            todasInscricoes.append(insc_online)
            except:
                pass  # Laravel offline
            
            conn.close()

            return jsonify({"success": True, "data": todasInscricoes}), 200
            
        except Exception as e:
            return jsonify(
                {"success": False, "message": f"Erro ao buscar inscrições: {str(e)}"}
            ), 500

    elif request.method == "POST":
        try:
            data = request.json

            if not data.get("usuario_id") or not data.get("evento_id"):
                return jsonify(
                    {"success": False, "message": "usuario_id e evento_id são obrigatórios"}
                ), 400

            conn = get_db()
            cursor = conn.cursor()

            # Verificar se já existe inscrição
            cursor.execute(
                """
                SELECT id FROM inscricoes_offline 
                WHERE usuario_id = ? AND evento_id = ? AND status = 'ativa'
                """,
                (data["usuario_id"], data["evento_id"]),
            )

            if cursor.fetchone():
                conn.close()
                return jsonify(
                    {"success": False, "message": "Usuário já inscrito neste evento"}
                ), 400

            # Criar inscrição
            cursor.execute(
                """
                INSERT INTO inscricoes_offline (usuario_id, evento_id, status)
                VALUES (?, ?, 'ativa')
                """,
                (data["usuario_id"], data["evento_id"]),
            )

            inscricao_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"✅ Inscrição criada offline: ID {inscricao_id}")

            return jsonify(
                {
                    "success": True,
                    "message": "Inscrição criada localmente (offline)",
                    "data": {
                        "id": inscricao_id,
                        "usuario_id": data["usuario_id"],
                        "evento_id": data["evento_id"],
                        "sincronizado": False,
                    },
                }
            ), 201

        except Exception as e:
            return jsonify(
                {"success": False, "message": f"Erro ao criar inscrição: {str(e)}"}
            ), 500


@app.route("/eventos", methods=["GET", "OPTIONS"])
def eventos():
    """
    GET: Lista eventos do cache
    """
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Criar tabela se não existir
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos_cache (
                id INTEGER PRIMARY KEY,
                titulo TEXT NOT NULL,
                descricao TEXT,
                data_inicio TEXT,
                data_fim TEXT,
                local TEXT,
                vagas INTEGER,
                status TEXT,
                carga_horaria INTEGER,
                sincronizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 🆕 SEMPRE tentar atualizar do Laravel (se online)
        try:
            resp = requests.get(f"{LARAVEL_API}/eventos", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                eventos_laravel = data.get('data', [])

                for evento in eventos_laravel:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO eventos_cache (
                            id, titulo, descricao, data_inicio, data_fim, 
                            local, vagas, status, carga_horaria
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            evento["id"],
                            evento["titulo"],
                            evento["descricao"],
                            evento["data_inicio"],
                            evento["data_fim"],
                            evento["local"],
                            evento["vagas"],
                            evento["status"],
                            evento.get("carga_horaria"),
                        ),
                    )
                conn.commit()
                print(f"✅ Cache de eventos atualizado: {len(eventos_laravel)} eventos")
        except Exception as e:
            print(f"⚠️ Laravel offline, usando cache local: {str(e)}")

        # Retornar eventos do cache
        cursor.execute(
            'SELECT * FROM eventos_cache WHERE status = "ativo" ORDER BY data_inicio'
        )
        eventos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({"success": True, "data": eventos}), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao buscar eventos: {str(e)}"
        }), 500



@app.route("/presencas", methods=["GET", "POST", "OPTIONS"])
def presencas():
    """
    GET: Lista presenças
    POST: Registrar presença offline
    """
    # Suporte CORS para OPTIONS
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return response

    if request.method == "GET":
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM presencas_offline ORDER BY id DESC")
            presencas = [dict(row) for row in cursor.fetchall()]
            conn.close()
            response = jsonify({"success": True, "data": presencas})
            return response
        except Exception as e:
            return jsonify(
                {"success": False, "message": f"Erro ao buscar presenças: {str(e)}"}
            ), 500

    elif request.method == "POST":
        try:
            data = request.json
            print(f"📋 Dados recebidos para presença: {data}")

            if not data or not data.get("inscricao_id"):
                return jsonify(
                    {"success": False, "message": "inscricao_id é obrigatório"}
                ), 400

            inscricao_id = data["inscricao_id"]
            conn = get_db()
            cursor = conn.cursor()

            # 1️⃣ BUSCA LOCAL
            cursor.execute(
                """
                SELECT usuario_id, evento_id, status
                FROM inscricoes_offline
                WHERE id = ?
                """,
                (inscricao_id,),
            )
            
            row = cursor.fetchone()
            if row:
                inscricao = {
                    "usuario_id": row[0],
                    "evento_id": row[1],
                    "status": row[2],
                }
            else:
                inscricao = None

            # 2️⃣ SE NÃO EXISTIR LOCALMENTE, TENTA ONLINE
            if not inscricao:
                print(f"⚠️ Inscrição {inscricao_id} não existe localmente, tentando Laravel...")
                try:
                    token = laravel_auth.token if laravel_auth.is_authenticated() else None
                    headers = {}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    
                    resp = requests.get(
                        f"{LARAVEL_API}/inscricoes/{inscricao_id}",
                        headers=headers,
                        timeout=4
                    )
                    
                    if resp.status_code == 200:
                        data_laravel = resp.json()
                        if data_laravel.get("success"):
                            ins = data_laravel["data"]
                            inscricao = {
                                "usuario_id": ins["usuario"]["id"],
                                "evento_id": ins["evento"]["id"],
                                "status": ins["status"],
                            }
                            print(f"✅ Achou no Laravel: {ins}")
                    else:
                        print(f"❌ Laravel retornou {resp.status_code} – ignorando e registrando offline")
                except Exception as e:
                    print(f"❌ Falha ao acessar Laravel: {e} – registrando assim mesmo")

            # 3️⃣ SE AINDA ASSIM NÃO TIVER DADOS, CRIA UMA INSCRIÇÃO "SEM METADADOS"
            if not inscricao:
                print("⚠️ Registrando mesmo sem dados completos")
                inscricao = {
                    "usuario_id": None,
                    "evento_id": None,
                    "status": "ativa",
                }

            # 4️⃣ VERIFICA SE JÁ EXISTE PRESENÇA LOCAL
            cursor.execute(
                """
                SELECT id FROM presencas_offline
                WHERE inscricao_id = ?
                """,
                (inscricao_id,),
            )

            if cursor.fetchone():
                conn.close()
                return jsonify(
                    {"success": False, "message": "Presença já registrada (offline)"}
                ), 400

            # 5️⃣ REGISTRAR PRESENÇA LOCAL
            cursor.execute(
                """
                INSERT INTO presencas_offline (inscricao_id, usuario_id, evento_id, sincronizado)
                VALUES (?, ?, ?, 0)
                """,
                (inscricao_id, inscricao["usuario_id"], inscricao["evento_id"]),
            )

            presenca_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"✅ Presença registrada offline: ID {presenca_id}")

            return jsonify(
                {
                    "success": True,
                    "message": "Presença registrada offline com sucesso",
                    "data": {
                        "id": presenca_id,
                        "inscricao_id": inscricao_id,
                        "sincronizado": False,
                    },
                }
            ), 201

        except Exception as e:
            print(f"❌ Erro ao registrar presença: {e}")
            import traceback
            traceback.print_exc()
            return jsonify(
                {
                    "success": False,
                    "message": f"Erro ao registrar presença: {str(e)}",
                }
            ), 500

@app.route("/dados-pendentes", methods=["GET"])
def listar_dados_pendentes():
    """Lista todos os dados que precisam ser sincronizados"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Usuários não sincronizados
        cursor.execute("SELECT * FROM usuarios_offline WHERE sincronizado = 0")
        usuarios = [dict(row) for row in cursor.fetchall()]

        # Inscrições não sincronizadas
        cursor.execute("SELECT * FROM inscricoes_offline WHERE sincronizado = 0")
        inscricoes = [dict(row) for row in cursor.fetchall()]

        # Presenças não sincronizadas
        cursor.execute("SELECT * FROM presencas_offline WHERE sincronizado = 0")
        presencas = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify(
            {
                "success": True,
                "data": {
                    "usuarios": usuarios,
                    "inscricoes": inscricoes,
                    "presencas": presencas,
                    "total_pendente": len(usuarios) + len(inscricoes) + len(presencas),
                },
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Erro ao listar dados pendentes: {str(e)}",
                }
            ),
            500,
        )

        
# ==========================================
# ENDPOINTS DE E-MAIL
# ==========================================


@app.route("/enviar-email-inscricao", methods=["POST"])
def endpoint_email_inscricao():
    """Endpoint para enviar e-mail de inscrição"""
    try:
        data = request.json
        usuario = data.get("usuario")
        evento = data.get("evento")

        if not usuario or not evento:
            return jsonify({"success": False, "message": "Dados incompletos"}), 400

        sucesso = enviar_email_inscricao(usuario, evento)
        return jsonify(
            {"success": sucesso, "message": "E-mail enviado" if sucesso else "Erro"}
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/enviar-email-certificado", methods=["POST"])
def endpoint_email_certificado():
    """Endpoint para enviar e-mail com certificado"""
    try:
        data = request.json
        usuario = data.get("usuario")
        evento = data.get("evento")
        certificado = data.get("certificado")

        if not usuario or not evento or not certificado:
            return jsonify({"success": False, "message": "Dados incompletos"}), 400

        sucesso = enviar_email_certificado(usuario, evento, certificado)
        return jsonify({"success": sucesso})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/enviar-email-cancelamento", methods=["POST"])
def endpoint_email_cancelamento():
    """Endpoint para enviar e-mail de cancelamento"""
    try:
        data = request.json
        usuario = data.get("usuario")
        evento = data.get("evento")

        if not usuario or not evento:
            return jsonify({"success": False, "message": "Dados incompletos"}), 400

        sucesso = enviar_email_cancelamento(usuario, evento)
        return jsonify(
            {"success": sucesso, "message": "E-mail enviado" if sucesso else "Erro"}
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/enviar-email-checkin", methods=["POST"])
def endpoint_email_checkin():
    """Endpoint para enviar e-mail de check-in"""
    try:
        data = request.json
        usuario = data.get("usuario")
        evento = data.get("evento")

        if not usuario or not evento:
            return jsonify({"success": False, "message": "Dados incompletos"}), 400

        sucesso = enviar_email_checkin(usuario, evento)
        return jsonify(
            {"success": sucesso, "message": "E-mail enviado" if sucesso else "Erro"}
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/gerar-certificado-pdf", methods=["POST"])
def endpoint_gerar_certificado_pdf():
    """Endpoint para gerar certificado em PDF"""
    try:
        data = request.json

        print(f"📋 Dados recebidos: {data}")

        # Validação básica
        campos_obrigatorios = [
            "nome_participante",
            "evento_titulo",
            "data_inicio",
            "data_fim",
            "local",
            "codigo_validacao",
            "data_emissao",
        ]

        for campo in campos_obrigatorios:
            if campo not in data:
                print(f"❌ Campo ausente: {campo}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Campo obrigatório ausente: {campo}",
                        }
                    ),
                    400,
                )

        # Gerar o PDF
        pdf_path = gerar_certificado_pdf(data)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Certificado gerado com sucesso",
                    "pdf_path": pdf_path,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ ERRO no endpoint: {str(e)}")
        import traceback

        traceback.print_exc()
        return (
            jsonify(
                {"success": False, "message": f"Erro ao gerar certificado: {str(e)}"}
            ),
            500,
        )


def gerar_certificado_pdf(dados_certificado, output_path="certificados_pdf"):
    """
    Gera um certificado em PDF
    """
    try:
        # Criar pasta se não existir
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        codigo_curto = dados_certificado["codigo_validacao"][:8]
        nome_arquivo = f"certificado_{codigo_curto}_{timestamp}.pdf"
        caminho_completo = os.path.join(output_path, nome_arquivo)

        # Criar o PDF em paisagem
        pdf = canvas.Canvas(caminho_completo, pagesize=landscape(A4))
        width, height = landscape(A4)

        # Borda decorativa externa
        pdf.setStrokeColor(HexColor("#667eea"))
        pdf.setLineWidth(3)
        pdf.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm, stroke=1, fill=0)

        # Borda decorativa interna
        pdf.setStrokeColor(HexColor("#764ba2"))
        pdf.setLineWidth(1)
        pdf.rect(
            1.3 * cm, 1.3 * cm, width - 2.6 * cm, height - 2.6 * cm, stroke=1, fill=0
        )

        # Título principal
        pdf.setFont("Helvetica-Bold", 40)
        pdf.setFillColor(HexColor("#667eea"))
        pdf.drawCentredString(width / 2, height - 4 * cm, "CERTIFICADO")

        # Subtítulo
        pdf.setFont("Helvetica", 16)
        pdf.setFillColor(HexColor("#333333"))
        pdf.drawCentredString(width / 2, height - 5 * cm, "Certificamos que")

        # Nome do participante
        pdf.setFont("Helvetica-Bold", 28)
        pdf.setFillColor(HexColor("#000000"))
        nome_participante = dados_certificado["nome_participante"].upper()
        pdf.drawCentredString(width / 2, height - 7 * cm, nome_participante)

        # Linha decorativa sob o nome
        pdf.setStrokeColor(HexColor("#667eea"))
        pdf.setLineWidth(2)
        nome_width = pdf.stringWidth(nome_participante, "Helvetica-Bold", 28)
        pdf.line(
            width / 2 - nome_width / 2 - 1 * cm,
            height - 7.3 * cm,
            width / 2 + nome_width / 2 + 1 * cm,
            height - 7.3 * cm,
        )

        # Texto principal
        pdf.setFont("Helvetica", 14)
        pdf.setFillColor(HexColor("#333333"))
        pdf.drawCentredString(width / 2, height - 9 * cm, "participou do evento")

        # Título do evento
        pdf.setFont("Helvetica-Bold", 18)
        pdf.setFillColor(HexColor("#667eea"))
        pdf.drawCentredString(
            width / 2, height - 10.5 * cm, dados_certificado["evento_titulo"]
        )

        # Descrição do evento
        if dados_certificado.get("evento_descricao"):
            pdf.setFont("Helvetica", 12)
            pdf.setFillColor(HexColor("#666666"))
            descricao = dados_certificado["evento_descricao"]
            if len(descricao) > 100:
                descricao = descricao[:97] + "..."
            pdf.drawCentredString(width / 2, height - 11.8 * cm, descricao)

        # Informações do evento
        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(HexColor("#333333"))
        y_position = height - 13.5 * cm

        # Período - COM TRATAMENTO DE ERRO
        try:
            data_inicio_fmt = datetime.strptime(
                dados_certificado["data_inicio"], "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
            data_fim_fmt = datetime.strptime(
                dados_certificado["data_fim"], "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
        except Exception as e:
            print(f"⚠️ Erro ao formatar datas: {e}")
            data_inicio_fmt = dados_certificado["data_inicio"]
            data_fim_fmt = dados_certificado["data_fim"]

        texto_periodo = f"Realizado no periodo de {data_inicio_fmt} a {data_fim_fmt}"
        pdf.drawCentredString(width / 2, y_position, texto_periodo)

        # Local
        texto_local = f"Local: {dados_certificado['local']}"
        pdf.drawCentredString(width / 2, y_position - 0.7 * cm, texto_local)

        # Carga horária
        if dados_certificado.get("carga_horaria"):
            texto_carga = f"Carga horaria: {dados_certificado['carga_horaria']} horas"
            pdf.drawCentredString(width / 2, y_position - 1.4 * cm, texto_carga)

        # Data de emissão - COM TRATAMENTO DE ERRO
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(HexColor("#666666"))
        try:
            data_emissao_fmt = datetime.strptime(
                dados_certificado["data_emissao"], "%Y-%m-%d %H:%M:%S"
            ).strftime("%d/%m/%Y")
        except:
            data_emissao_fmt = datetime.now().strftime("%d/%m/%Y")

        pdf.drawCentredString(width / 2, 3 * cm, f"Emitido em: {data_emissao_fmt}")

        # Código de validação
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(HexColor("#999999"))
        pdf.drawCentredString(
            width / 2,
            2.3 * cm,
            f"Codigo de Validacao: {dados_certificado['codigo_validacao']}",
        )

        # URL de validação
        url_validacao = f"http://127.0.0.1:8000/api/certificados/{dados_certificado['codigo_validacao']}"
        pdf.drawCentredString(
            width / 2, 1.8 * cm, f"Valide este certificado em: {url_validacao}"
        )

        # Assinatura
        pdf.setStrokeColor(HexColor("#333333"))
        pdf.setLineWidth(1)
        pdf.line(width / 2 - 5 * cm, 5 * cm, width / 2 + 5 * cm, 5 * cm)

        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(HexColor("#333333"))
        pdf.drawCentredString(width / 2, 4.5 * cm, "Sistema de Eventos - Univates")

        # Finalizar PDF
        pdf.save()

        print(f"✅ Certificado gerado: {caminho_completo}")
        return caminho_completo

    except Exception as e:
        print(f"❌ ERRO ao gerar PDF: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


# ==========================================
# ENDPOINT DE TESTE PARA CERTIFICADO
# ==========================================


@app.route("/teste-certificado", methods=["GET"])
def teste_certificado():
    """Endpoint de teste para gerar um certificado de exemplo"""
    try:
        dados_teste = {
            "nome_participante": "Bruno Barp",
            "evento_titulo": "Workshop de Desenvolvimento Web",
            "evento_descricao": "Workshop intensivo sobre desenvolvimento web moderno.",
            "data_inicio": "2025-11-01",
            "data_fim": "2025-11-03",
            "local": "Auditório Principal - Univates",
            "carga_horaria": 20,
            "codigo_validacao": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "data_emissao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        pdf_path = gerar_certificado_pdf(dados_teste)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Certificado de teste gerado!",
                    "pdf_path": pdf_path,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500


from flask import send_file


@app.route("/download-pdf/<path:filename>", methods=["GET"])
def download_pdf(filename):
    """Endpoint para download do PDF gerado"""
    try:
        return send_file(
            filename,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=os.path.basename(filename),
        )
    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Erro ao baixar PDF: {str(e)}"}),
            404,
        )
        
@app.route("/sync-status", methods=["GET"])
def status_sincronizacao():
    """Retorna status da sincronização"""
    try:
        status = get_sync_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route("/sincronizar", methods=["POST"])
def sincronizar():
    """Sincroniza dados locais com o servidor Laravel"""
    try:
        resultado = sincronizar_agora()
        
        if resultado['success']:
            return jsonify({
                "success": True,
                "message": "Sincronização completa!",
                "data": resultado,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": resultado['message']
            }), 503
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro na sincronização: {str(e)}"
        }), 500


@app.route("/sync-auto/<acao>", methods=["POST"])
def controlar_sync_automatico(acao):
    """Ativa ou desativa sincronização automática"""
    try:
        if acao == "ativar":
            sync_manager.start_auto_sync()
            return jsonify({
                "success": True,
                "message": f"Sincronização automática ativada ({sync_manager.sync_interval}s)"
            })
        elif acao == "desativar":
            sync_manager.stop_auto_sync()
            return jsonify({
                "success": True,
                "message": "Sincronização automática desativada"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Ação inválida"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==========================================
# INICIALIZAÇÃO
# ==========================================


if __name__ == "__main__":
    # Criar pastas
    if not os.path.exists("data"):
        os.makedirs("data")
    
    if not os.path.exists("certificados_pdf"):
        os.makedirs("certificados_pdf")
        print("📁 Pasta 'certificados_pdf' criada!")

    # Inicializar banco
    init_db()

    # ✅ FAZER LOGIN AUTOMÁTICO NO LARAVEL
    print("\n🔐 Tentando login automático no Laravel...")
    if laravel_auth.login('sistema@eventos.com', 'senha_sistema_2025'):
        print("✅ Autenticado com Laravel!")
    else:
        print("⚠️ Laravel offline - usando modo offline")

    # Iniciar sincronização automática
    print("\n🔄 Iniciando sincronização automática...")
    iniciar_sync_automatico()

    # Rodar aplicação
    print("\n🚀 Sistema Offline iniciado!")
    print("🔐 Laravel autenticado:", laravel_auth.is_authenticated())
    print("🔄 Sincronização automática: ATIVA\n")

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
