import hashlib
import secrets
import sqlite3

from NOVA.utils.paths import USERS_DB_PATH


def inicializar_banco(db_path=USERS_DB_PATH):
    with sqlite3.connect(db_path) as conexao:
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


def gerar_hash_senha(senha, salt=None):
    salt = salt or secrets.token_hex(16)
    senha_hash = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return senha_hash, salt


def criar_usuario(nome, email, senha, db_path=USERS_DB_PATH):
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
        with sqlite3.connect(db_path) as conexao:
            conexao.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, salt) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, salt),
            )
        return True, "Cadastro criado. Voce ja pode entrar."
    except sqlite3.IntegrityError:
        return False, "Esse e-mail ja esta cadastrado."


def autenticar_usuario(email, senha, db_path=USERS_DB_PATH):
    email = email.strip().casefold()

    with sqlite3.connect(db_path) as conexao:
        usuario = conexao.execute(
            "SELECT nome, senha_hash, salt FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()

    if not usuario:
        return False, "E-mail ou senha incorretos.", None

    nome, senha_hash_salva, salt = usuario
    senha_hash, _ = gerar_hash_senha(senha, salt)
    if not secrets.compare_digest(senha_hash, senha_hash_salva):
        return False, "E-mail ou senha incorretos.", None

    return True, "Login realizado com sucesso.", nome
