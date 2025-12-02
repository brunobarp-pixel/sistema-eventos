import requests
import sqlite3
from datetime import datetime

# Configurações
DATABASE = 'data/eventos.db'
LARAVEL_API = 'http://127.0.0.1:8000/api'

def get_db():#legado
    """Conecta ao banco SQLite"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_cache (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            email TEXT,
            cpf TEXT,
            telefone TEXT,
            senha TEXT
        )
    ''')
    conn.commit()
    return conn

def baixar_usuarios():
    print("\nBaixando usuários do servidor...")

    try:
        response = requests.get(f'{LARAVEL_API}/usuarios', timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception as e:
                print(f"Erro ao decodificar JSON: {str(e)}\nResposta: {response.text}\n")
                return 0
            usuarios = data.get('data', [])
            if not isinstance(usuarios, list):
                print(f"Formato inesperado dos dados de usuários: {usuarios}\n")
                return 0

            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM usuarios_cache')
                for usuario in usuarios:
                    try:
                        cursor.execute('''
                            INSERT INTO usuarios_cache (
                                id, nome, email, cpf, telefone, senha
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            usuario.get('id'),
                            usuario.get('nome'),
                            usuario.get('email'),
                            usuario.get('cpf'),
                            usuario.get('telefone'),
                            usuario.get('senha')
                        ))
                    except Exception as e:
                        print(f"Erro ao inserir usuário no cache: {usuario} - {str(e)}\n")
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Erro ao salvar usuários no banco SQLite: {str(e)}\n")
                return 0

            print(f"{len(usuarios)} usuários baixados com sucesso!\n")
            return len(usuarios)
        else:
            print(f"Erro ao baixar usuários: {response.status_code} - {response.text}\n")
            return 0

    except Exception as e:
        print(f"Erro geral ao baixar usuários: {str(e)}\n")
        return 0

def sincronizar_usuarios():
    """Sincroniza usuários offline com o servidor Laravel"""
    print("\nSincronizando usuários...")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios_offline WHERE sincronizado = 0')
    usuarios = cursor.fetchall()
    
    sincronizados = 0
    erros = 0
    
    for usuario in usuarios:
        try:
            response = requests.post(f'{LARAVEL_API}/usuarios', json={
                'nome': usuario['nome'],
                'email': usuario['email'],
                'senha': usuario['senha'],
                'cpf': usuario['cpf'] if usuario['cpf'] else None,
                'telefone': usuario['telefone'] if usuario['telefone'] else None
            }, timeout=5)
            
            if response.status_code in [200, 201]:
                cursor.execute(
                    'UPDATE usuarios_offline SET sincronizado = 1 WHERE id = ?',
                    (usuario['id'],)
                )
                conn.commit()
                sincronizados += 1
                print(f"Usuário {usuario['nome']} sincronizado")
            else:
                print(f"Erro ao sincronizar {usuario['nome']}: {response.text}")
                erros += 1
                
        except Exception as e:
            print(f"Erro ao sincronizar {usuario['nome']}: {str(e)}")
            erros += 1
    
    conn.close()
    print(f"{sincronizados} usuários sincronizados, {erros} erros\n")
    return sincronizados, erros

def sincronizar_inscricoes():
    print("\nSincronizando inscrições...")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM inscricoes_offline WHERE sincronizado = 0')
    inscricoes = cursor.fetchall()
    
    sincronizados = 0
    erros = 0
    
    for inscricao in inscricoes:
        try:
            response = requests.post(f'{LARAVEL_API}/inscricoes', json={
                'usuario_id': inscricao['usuario_id'],
                'evento_id': inscricao['evento_id']
            }, timeout=5)
            
            if response.status_code in [200, 201]:
                cursor.execute(
                    'UPDATE inscricoes_offline SET sincronizado = 1 WHERE id = ?',
                    (inscricao['id'],)
                )
                conn.commit()
                sincronizados += 1
                print(f"Inscrição ID {inscricao['id']} sincronizada")
            else:
                print(f"Erro ao sincronizar inscrição {inscricao['id']}: {response.text}")
                erros += 1
                
        except Exception as e:
            print(f"Erro ao sincronizar inscrição {inscricao['id']}: {str(e)}")
            erros += 1
    
    conn.close()
    print(f"{sincronizados} inscrições sincronizadas, {erros} erros\n")
    return sincronizados, erros

def sincronizar_presencas():
    """Sincroniza presenças offline com o servidor Laravel"""
    print("\nSincronizando presenças...")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM presencas_offline WHERE sincronizado = 0')
    presencas = cursor.fetchall()
    
    sincronizados = 0
    erros = 0
    
    for presenca in presencas:
        try:
            response = requests.post(f'{LARAVEL_API}/presencas', json={
                'inscricao_id': presenca['inscricao_id']
            }, timeout=5)
            
            if response.status_code in [200, 201]:
                cursor.execute(
                    'UPDATE presencas_offline SET sincronizado = 1 WHERE id = ?',
                    (presenca['id'],)
                )
                conn.commit()
                sincronizados += 1
                print(f"Presença ID {presenca['id']} sincronizada")
            else:
                print(f"Erro ao sincronizar presença {presenca['id']}: {response.text}")
                erros += 1
                
        except Exception as e:
            print(f"Erro ao sincronizar presença {presenca['id']}: {str(e)}")
            erros += 1
    
    conn.close()
    print(f"{sincronizados} presenças sincronizadas, {erros} erros\n")
    return sincronizados, erros

def baixar_eventos():
    print("\nBaixando eventos do servidor...")
    
    try:
        response = requests.get(f'{LARAVEL_API}/eventos', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('data', [])
            
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM eventos_cache')
            
            for evento in eventos:
                cursor.execute('''
                    INSERT INTO eventos_cache (
                        id, titulo, descricao, data_inicio, data_fim, 
                        local, vagas, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    evento['id'],
                    evento['titulo'],
                    evento['descricao'],
                    evento['data_inicio'],
                    evento['data_fim'],
                    evento['local'],
                    evento['vagas'],
                    evento['status']
                ))
            
            conn.commit()
            conn.close()
            
            print(f"{len(eventos)} eventos baixados com sucesso!\n")
            return len(eventos)
        else:
            print(f"Erro ao baixar eventos: {response.text}\n")
            return 0
            
    except Exception as e:
        print(f"Erro ao baixar eventos: {str(e)}\n")
        return 0

def sincronizar_tudo():
    """Executa sincronização completa"""
    print("\n" + "="*50)
    print("INICIANDO SINCRONIZAÇÃO COMPLETA")
    print("="*50)
    
    try:
        response = requests.get(f'{LARAVEL_API}/eventos', timeout=5)
        if response.status_code != 200:
            print("Servidor Laravel não está respondendo!")
            return
    except:
        print("Não foi possível conectar ao servidor Laravel!")
        print("   Verifique se o servidor está rodando em http://127.0.0.1:8000")
        return
    
    print("Conexão com servidor OK!\n")
    
    # 1. Baixar usuários
    baixar_usuarios()
    
    # 2. Baixar eventos
    baixar_eventos()
    
    # 3. Sincronizar usuários
    sincronizar_usuarios()
    
    # 4. Sincronizar inscrições
    sincronizar_inscricoes()
    
    # 5. Sincronizar presenças
    sincronizar_presencas()
    

if __name__ == '__main__':
    sincronizar_tudo()