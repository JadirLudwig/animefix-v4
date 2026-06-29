import sqlite3
import os

# Determinar o caminho do banco de dados (mesma lógica do database.py)
DB_PATH = os.getenv("DB_PATH", "anime.db")
if not DB_PATH.startswith("/"):
    # Assume que o script roda na raiz do projeto
    DB_PATH = os.path.join(os.getcwd(), DB_PATH)

print(f"Migrando banco de dados em: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("Banco de dados não encontrado. Nada para migrar.")
    exit(0)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    print("Tentando adicionar coluna 'mal_url' à tabela 'animes'...")
    cursor.execute("ALTER TABLE animes ADD COLUMN mal_url TEXT")
    conn.commit()
    print("✅ Coluna 'mal_url' adicionada com sucesso!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
        print("ℹ️ A coluna 'mal_url' já existe.")
    else:
        print(f"❌ Erro ao migrar: {e}")
finally:
    conn.close()
