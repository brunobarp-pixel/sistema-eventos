import sqlite3
import os

DATABASE = 'data/eventos.db'

# Deletar banco antigo
if os.path.exists(DATABASE):
    os.remove(DATABASE)
    print("✅ Banco de dados antigo deletado!")

# Criar pasta se não existir
if not os.path.exists('data'):
    os.makedirs('data')

# Conectar e criar novo banco
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Criar tabelas
cursor.execute('''
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
''')

cursor.execute('''
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
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS inscricoes_offline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        evento_id INTEGER,
        status TEXT DEFAULT 'ativa',
        sincronizado INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS presencas_offline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inscricao_id INTEGER,
        usuario_id INTEGER,
        evento_id INTEGER,
        sincronizado INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

print("✅ Banco de dados recriado com sucesso!")
print("✅ Todas as tabelas criadas com a coluna carga_horaria!")