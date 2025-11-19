import sqlite3
from datetime import datetime, date

DB_NAME = "refeitorio.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Tabela de pessoas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pessoas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT UNIQUE
    )
    """)

    # Tabela de refeições
    cur.execute("""
    CREATE TABLE IF NOT EXISTS refeicoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pessoa_id INTEGER NOT NULL,
        data DATE NOT NULL,
        hora TIME NOT NULL,
        tipo_refeicao TEXT NOT NULL,
        FOREIGN KEY(pessoa_id) REFERENCES pessoas(id)
    )
    """)

    # Tabela de usuários do sistema
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

def cadastrar_pessoa(nome, matricula=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pessoas (nome, matricula) VALUES (?, ?)",
        (nome, matricula),
    )
    conn.commit()
    pessoa_id = cur.lastrowid
    conn.close()
    return pessoa_id

def ja_comeu_hoje(pessoa_id, tipo_refeicao="ALMOCO", data_ref=None):
    if data_ref is None:
        data_ref = date.today().isoformat()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM refeicoes
        WHERE pessoa_id = ? AND data = ? AND tipo_refeicao = ?
        """,
        (pessoa_id, data_ref, tipo_refeicao),
    )
    count = cur.fetchone()[0]
    conn.close()
    return count > 0

def registrar_refeicao(pessoa_id, tipo_refeicao="ALMOCO", dt=None):
    if dt is None:
        dt = datetime.now()

    data_str = dt.date().isoformat()
    hora_str = dt.time().strftime("%H:%M:%S")

    if ja_comeu_hoje(pessoa_id, tipo_refeicao, data_str):
        return False

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO refeicoes (pessoa_id, data, hora, tipo_refeicao)
        VALUES (?, ?, ?, ?)
        """,
        (pessoa_id, data_str, hora_str, tipo_refeicao),
    )
    conn.commit()
    conn.close()
    return True

def listar_refeicoes():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.id, p.nome, r.data, r.hora, r.tipo_refeicao
    FROM refeicoes r
    JOIN pessoas p ON p.id = r.pessoa_id
    ORDER BY r.data, r.hora
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def listar_pessoas():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, nome, matricula FROM pessoas ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows
import hashlib

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario_sistema(nome, email, senha):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    senha_hash = hash_senha(senha)
    cur.execute("""
        INSERT INTO usuarios_sistema (nome, email, senha_hash)
        VALUES (?, ?, ?)
    """, (nome, email, senha_hash))
    conn.commit()
    conn.close()

def autenticar_usuario(email, senha):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    senha_hash = hash_senha(senha)
    cur.execute("""
        SELECT id, nome FROM usuarios_sistema
        WHERE email = ? AND senha_hash = ?
    """, (email, senha_hash))
    user = cur.fetchone()
    conn.close()
    return user

