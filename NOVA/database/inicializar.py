from NOVA.database.connection import conectar
from NOVA.database.users import criar_tabela_usuarios
from NOVA.database.conversas import criar_tabela_conversas
from NOVA.database.mensagens import criar_tabela_mensagens


def inicializar_banco() -> None:
    with conectar() as conexao:
        criar_tabela_usuarios(conexao)
        criar_tabela_conversas(conexao)
        criar_tabela_mensagens(conexao)