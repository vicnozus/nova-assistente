from contextlib import contextmanager
from pathlib import Path
import sqlite3
from sqlite3 import Connection
from typing import Iterator

from NOVA.utils.paths import NOVA_DB_PATH


@contextmanager
def conectar(
    db_path: Path = NOVA_DB_PATH,
) -> Iterator[Connection]:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(db_path)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()