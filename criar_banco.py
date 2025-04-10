import sqlite3

conn = sqlite3.connect('usuario.db')
cursor = conn.cursor()

# Tabela 'usuario'
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT,
    funcionario_id INTEGER UNIQUE,
    security_question TEXT,
    security_answer TEXT
)
''')


conn.commit()
conn.close()

print("Tabelas 'usuario' e 'chamados' criadas (se não existiam) com sucesso!")
