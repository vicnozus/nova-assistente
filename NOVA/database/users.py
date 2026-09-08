import hashlib
from pathlib import Path
import secrets
import sqlite3

from NOVA.database.connection import conectar
from NOVA.database.conversas import criar_tabela_conversas
from NOVA.utils.paths import DATABASE_DIR, NOVA_DB_PATH


def inicializar_banco(db_path=NOVA_DB_PATH):
    with conectar(db_path) as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        criar_tabela_conversas(conexao)
    migrar_usuarios_legados(db_path)


def migrar_usuarios_legados(db_path=NOVA_DB_PATH):
    banco_legado = DATABASE_DIR / "usuarios.db"
    if Path(db_path) != NOVA_DB_PATH or not banco_legado.exists():
        return

    with conectar(db_path) as conexao:
        total_usuarios = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if total_usuarios:
            return

        try:
            with conectar(banco_legado) as origem:
                usuarios = origem.execute(
                    "SELECT id, nome, email, senha_hash, salt, criado_em FROM usuarios"
                ).fetchall()
        except sqlite3.Error:
            usuarios = []

        conexao.executemany(
            """
            INSERT OR IGNORE INTO usuarios (id, nome, email, senha_hash, salt, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            usuarios,
        )


def gerar_hash_senha(senha, salt=None):
    salt = salt or secrets.token_hex(16)
    senha_hash = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return senha_hash, salt


def criar_usuario(nome, email, senha, db_path=NOVA_DB_PATH):
    nome = nome.strip()
    email = email.strip().casefold()

    if not nome:
        return False, "Informe seu nome."
    if "@" not in email or "." not in email:
        return False, "Informe um e-mail valido."
    if len(senha) < 6:
        return False, "A senha precisa ter pelo menos 6 caracteres."

    senha_hash, salt = gerar_hash_senha(senha)

    try:
        with conectar(db_path) as conexao:
            conexao.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, salt) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, salt),
            )
        return True, "Cadastro criado. Voce ja pode entrar."
    except sqlite3.IntegrityError:
        return False, "Esse e-mail ja esta cadastrado."


def autenticar_usuario(email, senha, db_path=NOVA_DB_PATH):
    email = email.strip().casefold()

    with conectar(db_path) as conexao:
        usuario = conexao.execute(
            """
            SELECT id, nome, senha_hash, salt
            FROM usuarios
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    if not usuario:
        return False, "E-mail ou senha incorretos.", None, None

    usuario_id, nome, senha_hash_salva, salt = usuario

    senha_hash, _ = gerar_hash_senha(senha, salt)

    if not secrets.compare_digest(senha_hash, senha_hash_salva):
        return False, "E-mail ou senha incorretos.", None, None

    return True, "Login realizado com sucesso.", usuario_id, nome
