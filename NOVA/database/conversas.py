from sqlite3 import Connection, Row
from pathlib import Path

from NOVA.database.connection import conectar
from NOVA.utils.paths import NOVA_DB_PATH


def criar_tabela_conversas(conexao: Connection) -> None:
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            assunto TEXT NOT NULL,
            data_inicio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_fim TEXT,
            FOREIGN KEY (usuario_id)
                REFERENCES usuarios (id)
                ON DELETE CASCADE
        )
        """
    )


def criar_conversa(
    usuario_id: int,
    assunto: str,
    db_path: Path = NOVA_DB_PATH,
) -> int:
    assunto = assunto.strip()

    if usuario_id <= 0:
        raise ValueError("usuario_id deve ser maior que zero.")

    if not assunto:
        raise ValueError("O assunto da conversa não pode estar vazio.")

    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO conversas (usuario_id, assunto)
            VALUES (?, ?)
            """,
            (usuario_id, assunto),
        )

        return cursor.lastrowid


def buscar_conversa_por_id(
    conversa_id: int,
    db_path: Path = NOVA_DB_PATH,
) -> Row | None:
    if conversa_id <= 0:
        raise ValueError("conversa_id deve ser maior que zero.")

    with conectar(db_path) as conexao:
        return conexao.execute(
            """
            SELECT
                id,
                usuario_id,
                assunto,
                data_inicio,
                data_atualizacao,
                data_fim
            FROM conversas
            WHERE id = ?
            """,
            (conversa_id,),
        ).fetchone()


def listar_conversas_do_usuario(
    usuario_id: int,
    db_path: Path = NOVA_DB_PATH,
) -> list[Row]:
    if usuario_id <= 0:
        raise ValueError("usuario_id deve ser maior que zero.")

    with conectar(db_path) as conexao:
        return conexao.execute(
            """
            SELECT
                id,
                usuario_id,
                assunto,
                data_inicio,
                data_atualizacao,
                data_fim
            FROM conversas
            WHERE usuario_id = ?
              AND data_fim IS NULL
            ORDER BY data_atualizacao DESC, id DESC
            """,
            (usuario_id,),
        ).fetchall()


def atualizar_data_conversa(
    conversa_id: int,
    db_path: Path = NOVA_DB_PATH,
) -> bool:
    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            """
            UPDATE conversas
            SET data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = ?
              AND data_fim IS NULL
            """,
            (conversa_id,),
        )

        return cursor.rowcount > 0


def encerrar_conversa(
    conversa_id: int,
    db_path: Path = NOVA_DB_PATH,
) -> bool:
    if conversa_id <= 0:
        raise ValueError("conversa_id deve ser maior que zero.")

    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            """
            UPDATE conversas
            SET
                data_fim = CURRENT_TIMESTAMP,
                data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = ?
              AND data_fim IS NULL
            """,
            (conversa_id,),
        )

        return cursor.rowcount > 0