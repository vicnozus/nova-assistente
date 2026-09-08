from pathlib import Path
from sqlite3 import Connection, Row

from NOVA.database.connection import conectar
from NOVA.utils.paths import NOVA_DB_PATH


REMETENTES_VALIDOS = {"usuario", "nova", "sistema"}


def criar_tabela_mensagens(conexao: Connection) -> None:
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversa_id INTEGER NOT NULL,
            remetente TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            data_envio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            

            FOREIGN KEY (conversa_id)
                REFERENCES conversas (id)
                ON DELETE CASCADE,

            CHECK (remetente IN ('usuario', 'nova', 'sistema'))
        )
        """
    )


def criar_mensagem(
    conversa_id: int,
    remetente: str,
    conteudo: str,
    db_path: Path = NOVA_DB_PATH,
) -> int:
    remetente = remetente.strip().lower()
    conteudo = conteudo.strip()

    if conversa_id <= 0:
        raise ValueError("conversa_id deve ser maior que zero.")

    if remetente not in REMETENTES_VALIDOS:
        raise ValueError(
            f"Remetente inválido: {remetente}. "
            f"Use: {', '.join(sorted(REMETENTES_VALIDOS))}."
        )

    if not conteudo:
        raise ValueError("O conteúdo da mensagem não pode estar vazio.")

    with conectar(db_path) as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO mensagens (
                conversa_id,
                remetente,
                conteudo
            )
            VALUES (?, ?, ?)
            """,
            (conversa_id, remetente, conteudo),
        )

        conexao.execute(
            """
            UPDATE conversas
            SET data_atualizacao = CURRENT_TIMESTAMP
            WHERE id = ?
              AND data_fim IS NULL
            """,
            (conversa_id,),
        )

        return cursor.lastrowid


def buscar_mensagem_por_id(
    mensagem_id: int,
    db_path: Path = NOVA_DB_PATH,
) -> Row | None:
    if mensagem_id <= 0:
        raise ValueError("mensagem_id deve ser maior que zero.")

    with conectar(db_path) as conexao:
        return conexao.execute(
            """
            SELECT
                id,
                conversa_id,
                remetente,
                conteudo,
                data_envio
            FROM mensagens
            WHERE id = ?
            """,
            (mensagem_id,),
        ).fetchone()


def listar_mensagens_da_conversa(
    conversa_id: int,
    db_path: Path = NOVA_DB_PATH,
) -> list[Row]:
    if conversa_id <= 0:
        raise ValueError("conversa_id deve ser maior que zero.")

    with conectar(db_path) as conexao:
        return conexao.execute(
            """
            SELECT
                id,
                conversa_id,
                remetente,
                conteudo,
                data_envio
            FROM mensagens
            WHERE conversa_id = ?
            ORDER BY data_envio ASC, id ASC
            """,
            (conversa_id,),
        ).fetchall()