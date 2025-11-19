import sqlite3
from datetime import datetime, date
import hashlib

DB_NAME = "refeitorio.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Criar tabela pessoas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pessoas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT
    )
    """)

    # Garantir coluna foto_path
    cur.execute("PRAGMA table_info(pessoas)")
    cols = [row[1] for row in cur.fetchall()]
    if "foto_path" not in cols:
        cur.execute("ALTER TABLE pessoas ADD COLUMN foto_path TEXT")

    # Criar tabela refeicoes (sem tipo obrigatório para evitar conflito)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS refeicoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pessoa_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        hora TEXT NOT NULL,
        tipo TEXT,
        FOREIGN KEY (pessoa_id) REFERENCES pessoas(id)
    )
    """)

    # Garantir coluna tipo (pq no Render não existe)
    cur.execute("PRAGMA table_info(refeicoes)")
    cols = [row[1] for row in cur.fetchall()]
    if "tipo" not in cols:
        cur.execute("ALTER TABLE refeicoes ADD COLUMN tipo TEXT")

    # Criar tabela usuarios_sistema
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios_sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

# ---------------- PESSOAS ----------------

def cadastrar_pessoa(nome, matricula=None, foto_path=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pessoas (nome, matricula, foto_path) VALUES (?, ?, ?)",
        (nome, matricula, foto_path),
    )
    conn.commit()
    conn.close()


def listar_pessoas():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, nome, matricula, foto_path FROM pessoas ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------- REFEIÇÕES ----------------

def registrar_refeicao(pessoa_id, dt=None, tipo="ALMOCO"):
    if dt is None:
        dt = datetime.now()

    data_str = dt.date().isoformat()
    hora_str = dt.time().strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # verifica se já comeu no dia
    cur.execute(
        """
        SELECT COUNT(*) FROM refeicoes
        WHERE pessoa_id = ? AND data = ? AND tipo = ?
        """,
        (pessoa_id, data_str, tipo),
    )
    ja_comeu = cur.fetchone()[0] > 0

    if ja_comeu:
        conn.close()
        print("⚠ Essa pessoa já comeu hoje! Refeição NÃO registrada.")
        return False

    cur.execute(
        """
        INSERT INTO refeicoes (pessoa_id, data, hora, tipo)
        VALUES (?, ?, ?, ?)
        """,
        (pessoa_id, data_str, hora_str, tipo),
    )
    conn.commit()
    conn.close()
    print("✅ Refeição registrada com sucesso!")
    return True


def listar_refeicoes():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, p.nome, r.data, r.hora, r.tipo
        FROM refeicoes r
        JOIN pessoas p ON p.id = r.pessoa_id
        ORDER BY r.data DESC, r.hora DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------- LOGIN DO SISTEMA ----------------

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_usuario_sistema(nome, email, senha):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    senha_hash = hash_senha(senha)
    cur.execute(
        """
        INSERT INTO usuarios_sistema (nome, email, senha_hash)
        VALUES (?, ?, ?)
        """,
        (nome, email, senha_hash),
    )
    conn.commit()
    conn.close()


def autenticar_usuario(email, senha):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    senha_hash = hash_senha(senha)
    cur.execute(
        """
        SELECT id, nome FROM usuarios_sistema
        WHERE email = ? AND senha_hash = ?
        """,
        (email, senha_hash),
    )
    user = cur.fetchone()
    conn.close()
    return user
