from NOVA.database.connection import conectar

with conectar() as conexao:
    estrutura = conexao.execute(
        "PRAGMA table_info(usuarios)"
    ).fetchall()

    for coluna in estrutura:
        print(dict(coluna))