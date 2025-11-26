"""
Sistema de Sincronização Bidirecional CORRIGIDO
✅ Trata duplicatas
✅ Mapeia IDs offline → online
✅ Não quebra se Laravel estiver offline
"""

import requests
import sqlite3
import time
import threading
from datetime import datetime

DATABASE = 'data/eventos.db'
LARAVEL_API = 'http://127.0.0.1:8000/api'

class SyncManager:
    def __init__(self):
        self.sync_interval = 300  # 5 minutos
        self.is_running = False
        self.last_sync = None
        self.usuarios_map = {}  # ID offline → ID online
        self.inscricoes_map = {}
        
    def get_db(self):
        """Conecta ao banco SQLite"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    
    def check_online(self):
        """Verifica se o Laravel está online"""
        try:
            response = requests.get(f'{LARAVEL_API}/status', timeout=3)
            return response.status_code == 200
        except:
            return False
    
    # ==========================================
    # 📤 UPLOAD: PYTHON → LARAVEL
    # ==========================================
    
    def sync_usuarios_to_laravel(self):
        """Envia usuários offline para o Laravel"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM usuarios_offline WHERE sincronizado = 0")
        usuarios = cursor.fetchall()
        
        sincronizados = 0
        erros = []
        
        for usuario in usuarios:
            try:
                # 🔥 TENTAR CADASTRAR
                resp = requests.post(f'{LARAVEL_API}/usuarios', json={
                    'nome': usuario['nome'],
                    'email': usuario['email'],
                    'senha': usuario['senha'],
                    'cpf': usuario['cpf'] if usuario['cpf'] else None,
                    'telefone': usuario['telefone'] if usuario['telefone'] else None
                }, timeout=10)
                
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    if data.get('success'):
                        # ✅ Sucesso - mapear IDs
                        id_online = data['data']['id']
                        self.usuarios_map[usuario['id']] = id_online
                        
                        cursor.execute(
                            "UPDATE usuarios_offline SET sincronizado = 1 WHERE id = ?",
                            (usuario['id'],)
                        )
                        conn.commit()
                        sincronizados += 1
                        print(f"✅ Usuário {usuario['nome']} → Laravel (ID: {id_online})")
                
                elif resp.status_code == 422:
                    # ⚠️ Email duplicado - buscar usuário existente
                    try:
                        resp_busca = requests.get(f'{LARAVEL_API}/usuarios', timeout=5)
                        if resp_busca.status_code == 200:
                            usuarios_online = resp_busca.json().get('data', [])
                            
                            # Procurar pelo email
                            usuario_existente = next(
                                (u for u in usuarios_online if u['email'] == usuario['email']), 
                                None
                            )
                            
                            if usuario_existente:
                                # Mapear para o ID existente
                                self.usuarios_map[usuario['id']] = usuario_existente['id']
                                
                                cursor.execute(
                                    "UPDATE usuarios_offline SET sincronizado = 1 WHERE id = ?",
                                    (usuario['id'],)
                                )
                                conn.commit()
                                sincronizados += 1
                                print(f"⚠️ Usuário {usuario['nome']} já existe (ID: {usuario_existente['id']})")
                    except Exception as e:
                        erros.append(f"Usuário {usuario['nome']}: {str(e)}")
                else:
                    erros.append(f"Usuário {usuario['nome']}: HTTP {resp.status_code}")
                    
            except Exception as e:
                erros.append(f"Usuário {usuario['nome']}: {str(e)}")
        
        conn.close()
        return sincronizados, erros
    
    def sync_inscricoes_to_laravel(self):
        """Envia inscrições offline para o Laravel"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM inscricoes_offline WHERE sincronizado = 0")
        inscricoes = cursor.fetchall()
        
        sincronizados = 0
        erros = []
        
        for insc in inscricoes:
            try:
                # 🔥 Usar ID mapeado do usuário (se foi sincronizado antes)
                usuario_id = self.usuarios_map.get(insc['usuario_id'], insc['usuario_id'])
                
                resp = requests.post(f'{LARAVEL_API}/inscricoes', json={
                    'usuario_id': usuario_id,
                    'evento_id': insc['evento_id']
                }, timeout=10)
                
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    if data.get('success'):
                        # ✅ Sucesso - mapear IDs
                        id_online = data['data']['id']
                        self.inscricoes_map[insc['id']] = id_online
                        
                        cursor.execute(
                            "UPDATE inscricoes_offline SET sincronizado = 1 WHERE id = ?",
                            (insc['id'],)
                        )
                        conn.commit()
                        sincronizados += 1
                        print(f"✅ Inscrição ID {insc['id']} → Laravel (ID: {id_online})")
                elif resp.status_code == 400:
                    # ⚠️ Já inscrito - buscar inscrição existente
                    try:
                        resp_busca = requests.get(
                            f'{LARAVEL_API}/inscricoes?usuario_id={usuario_id}&evento_id={insc["evento_id"]}',
                            timeout=5
                        )
                        if resp_busca.status_code == 200:
                            inscricoes_online = resp_busca.json().get('data', [])
                            if inscricoes_online:
                                # Mapear para a inscrição existente
                                self.inscricoes_map[insc['id']] = inscricoes_online[0]['id']
                                
                                cursor.execute(
                                    "UPDATE inscricoes_offline SET sincronizado = 1 WHERE id = ?",
                                    (insc['id'],)
                                )
                                conn.commit()
                                sincronizados += 1
                                print(f"⚠️ Inscrição ID {insc['id']} já existe")
                    except Exception as e:
                        erros.append(f"Inscrição {insc['id']}: {str(e)}")
                else:
                    erros.append(f"Inscrição {insc['id']}: HTTP {resp.status_code}")
                    
            except Exception as e:
                erros.append(f"Inscrição {insc['id']}: {str(e)}")
        
        conn.close()
        return sincronizados, erros
    
    def sync_presencas_to_laravel(self):
        """Envia presenças offline para o Laravel"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM presencas_offline WHERE sincronizado = 0")
        presencas = cursor.fetchall()
        
        sincronizados = 0
        erros = []
        
        for pres in presencas:
            try:
                # 🔥 Usar ID mapeado da inscrição
                inscricao_id = self.inscricoes_map.get(pres['inscricao_id'], pres['inscricao_id'])
                
                resp = requests.post(f'{LARAVEL_API}/presencas', json={
                    'inscricao_id': inscricao_id
                }, timeout=10)
                
                if resp.status_code in [200, 201]:
                    cursor.execute(
                        "UPDATE presencas_offline SET sincronizado = 1 WHERE id = ?",
                        (pres['id'],)
                    )
                    conn.commit()
                    sincronizados += 1
                    print(f"✅ Presença ID {pres['id']} → Laravel")
                elif resp.status_code == 400:
                    # ⚠️ Presença já registrada - marcar como sincronizado
                    cursor.execute(
                        "UPDATE presencas_offline SET sincronizado = 1 WHERE id = ?",
                        (pres['id'],)
                    )
                    conn.commit()
                    sincronizados += 1
                    print(f"⚠️ Presença ID {pres['id']} já existe")
                else:
                    erros.append(f"Presença {pres['id']}: HTTP {resp.status_code}")
                    
            except Exception as e:
                erros.append(f"Presença {pres['id']}: {str(e)}")
        
        conn.close()
        return sincronizados, erros
    
    # ==========================================
    # 📥 DOWNLOAD: LARAVEL → PYTHON
    # ==========================================
    
    def sync_eventos_from_laravel(self):
        """Baixa eventos do Laravel para cache"""
        try:
            resp = requests.get(f'{LARAVEL_API}/eventos', timeout=10)
            if resp.status_code != 200:
                return 0
            
            data = resp.json()
            eventos = data.get('data', [])
            
            conn = self.get_db()
            cursor = conn.cursor()
            
            # ❌ NÃO deletar cache antigo - apenas atualizar
            for evento in eventos:
                cursor.execute("""
                    INSERT OR REPLACE INTO eventos_cache (
                        id, titulo, descricao, data_inicio, data_fim,
                        local, vagas, status, carga_horaria, sincronizado_em
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    evento['id'],
                    evento['titulo'],
                    evento['descricao'],
                    evento['data_inicio'],
                    evento['data_fim'],
                    evento['local'],
                    evento['vagas'],
                    evento['status'],
                    evento.get('carga_horaria')
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ {len(eventos)} eventos sincronizados")
            return len(eventos)
            
        except Exception as e:
            print(f"❌ Erro ao baixar eventos: {str(e)}")
            return 0
    
    def sync_inscricoes_from_laravel(self):
        """Baixa inscrições do Laravel para cache"""
        try:
            resp = requests.get(f'{LARAVEL_API}/inscricoes', timeout=10)
            if resp.status_code != 200:
                return 0
            
            data = resp.json()
            inscricoes = data.get('data', [])
            
            conn = self.get_db()
            cursor = conn.cursor()
            
            # Criar tabela de cache se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inscricoes_cache (
                    id INTEGER PRIMARY KEY,
                    usuario_id INTEGER,
                    evento_id INTEGER,
                    status TEXT,
                    possui_presenca INTEGER DEFAULT 0,
                    sincronizado_em TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Atualizar cache
            for insc in inscricoes:
                cursor.execute("""
                    INSERT OR REPLACE INTO inscricoes_cache 
                    (id, usuario_id, evento_id, status, possui_presenca)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    insc['id'],
                    insc['usuario_id'],
                    insc['evento_id'],
                    insc['status'],
                    1 if insc.get('possui_presenca') else 0
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ {len(inscricoes)} inscrições sincronizadas")
            return len(inscricoes)
            
        except Exception as e:
            print(f"❌ Erro ao baixar inscrições: {str(e)}")
            return 0
    
    # ==========================================
    # 🔄 SINCRONIZAÇÃO COMPLETA
    # ==========================================
    
    def sync_full(self):
        """Executa sincronização completa"""
        print(f"\n{'='*60}")
        print(f"🔄 SINCRONIZAÇÃO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        if not self.check_online():
            print("❌ Laravel offline - usando modo offline")
            return {'success': False, 'message': 'Laravel offline'}
        
        print("✅ Laravel online\n")
        
        # FASE 1: UPLOAD
        print("📤 FASE 1: Enviando dados offline")
        usuarios_ok, usuarios_err = self.sync_usuarios_to_laravel()
        inscricoes_ok, inscricoes_err = self.sync_inscricoes_to_laravel()
        presencas_ok, presencas_err = self.sync_presencas_to_laravel()
        
        print(f"\n📊 Upload: {usuarios_ok} usuários, {inscricoes_ok} inscrições, {presencas_ok} presenças")
        
        if usuarios_err or inscricoes_err or presencas_err:
            print(f"⚠️ Erros: {len(usuarios_err + inscricoes_err + presencas_err)}")
        
        # FASE 2: DOWNLOAD
        print("\n📥 FASE 2: Atualizando cache")
        eventos_down = self.sync_eventos_from_laravel()
        inscricoes_down = self.sync_inscricoes_from_laravel()
        
        print(f"\n📊 Download: {eventos_down} eventos, {inscricoes_down} inscrições")
        
        self.last_sync = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"✅ SINCRONIZAÇÃO COMPLETA!")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'upload': {
                'usuarios': usuarios_ok,
                'inscricoes': inscricoes_ok,
                'presencas': presencas_ok
            },
            'download': {
                'eventos': eventos_down,
                'inscricoes': inscricoes_down
            },
            'erros': usuarios_err + inscricoes_err + presencas_err
        }
    
    # ==========================================
    # ⏰ AUTO-SYNC
    # ==========================================
    
    def auto_sync_loop(self):
        """Loop de sincronização automática"""
        while self.is_running:
            time.sleep(self.sync_interval)
            
            if self.check_online():
                try:
                    self.sync_full()
                except Exception as e:
                    print(f"❌ Erro na auto-sync: {str(e)}")
    
    def start_auto_sync(self):
        """Inicia sincronização automática"""
        if not self.is_running:
            self.is_running = True
            thread = threading.Thread(target=self.auto_sync_loop, daemon=True)
            thread.start()
            print(f"✅ Auto-sync ativada ({self.sync_interval}s)")
    
    def stop_auto_sync(self):
        """Para sincronização automática"""
        self.is_running = False
        print("⏸️ Auto-sync desativada")


# ==========================================
# INSTÂNCIA GLOBAL
# ==========================================

sync_manager = SyncManager()


# ==========================================
# FUNÇÕES PARA USO NO FLASK
# ==========================================

def iniciar_sync_automatico():
    sync_manager.start_auto_sync()

def sincronizar_agora():
    return sync_manager.sync_full()

def get_sync_status():
    return {
        'auto_sync_ativo': sync_manager.is_running,
        'ultima_sincronizacao': sync_manager.last_sync.isoformat() if sync_manager.last_sync else None,
        'intervalo_segundos': sync_manager.sync_interval,
        'laravel_online': sync_manager.check_online()
    }