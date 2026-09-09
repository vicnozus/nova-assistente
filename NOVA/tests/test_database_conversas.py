import sqlite3
import tempfile
import unittest
from pathlib import Path

from NOVA.database.connection import conectar
from NOVA.database.conversas import (
    buscar_conversa_por_id,
    criar_conversa,
    encerrar_conversa,
    listar_conversas_do_usuario,
)
from NOVA.database.users import criar_usuario, inicializar_banco


class ConversasDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.db_path = Path(self.pasta.name) / "nova.db"
        inicializar_banco(self.db_path)

    def tearDown(self):
        self.pasta.cleanup()

    def criar_usuario_teste(self, email="ana@example.com"):
        sucesso, mensagem = criar_usuario("Ana", email, "senha123", self.db_path)
        self.assertTrue(sucesso, mensagem)
        with conectar(self.db_path) as conexao:
            return conexao.execute(
                "SELECT id FROM usuarios WHERE email = ?",
                (email,),
            ).fetchone()[0]

    def test_criar_conversa(self):
        usuario_id = self.criar_usuario_teste()

        conversa_id = criar_conversa(usuario_id, "Primeira conversa", self.db_path)
        conversa = buscar_conversa_por_id(conversa_id, self.db_path)

        self.assertEqual(conversa[1], usuario_id)
        self.assertEqual(conversa[2], "Primeira conversa")
        self.assertIsNone(conversa["data_fim"])

    def test_listar_conversas_do_usuario(self):
        usuario_id = self.criar_usuario_teste()
        outro_usuario_id = self.criar_usuario_teste("bia@example.com")
        criar_conversa(usuario_id, "Assunto A", self.db_path)
        criar_conversa(usuario_id, "Assunto B", self.db_path)
        criar_conversa(outro_usuario_id, "Outro usuario", self.db_path)

        conversas = listar_conversas_do_usuario(usuario_id, self.db_path)

        self.assertEqual(len(conversas), 2)
        self.assertEqual({conversa[2] for conversa in conversas}, {"Assunto A", "Assunto B"})

    def test_nao_cria_conversa_para_usuario_inexistente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            criar_conversa(999, "Sem dono", self.db_path)

    def test_encerrar_conversa(self):
        usuario_id = self.criar_usuario_teste()
        conversa_id = criar_conversa(usuario_id, "Para encerrar", self.db_path)

        self.assertTrue(encerrar_conversa(conversa_id, self.db_path))
        conversa = buscar_conversa_por_id(conversa_id, self.db_path)

        self.assertIsNotNone(conversa["data_fim"])

    def test_excluir_usuario_remove_conversas_em_cascata(self):
        usuario_id = self.criar_usuario_teste()
        conversa_id = criar_conversa(usuario_id, "Vai sumir", self.db_path)

        with conectar(self.db_path) as conexao:
            conexao.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))

        self.assertIsNone(buscar_conversa_por_id(conversa_id, self.db_path))


if __name__ == "__main__":
    unittest.main()
