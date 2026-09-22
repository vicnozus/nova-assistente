"""Regressões do histórico com banco real e widgets simulados, sem abrir janelas."""

from contextlib import ExitStack
from functools import partial
from pathlib import Path
from queue import Queue
import tempfile
from types import SimpleNamespace, MethodType
import unittest
from unittest.mock import MagicMock, patch

from NOVA.database import conversas, mensagens
from NOVA.database.connection import conectar
from NOVA.database.inicializar import inicializar_banco
from NOVA.interface.app import NovaApp


class HistoricoTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        pasta = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.db_path = Path(pasta) / "nova.db"
        inicializar_banco(self.db_path)
        with conectar(self.db_path) as db:
            db.execute("INSERT INTO usuarios (nome, email, senha_hash, salt) "
                       "VALUES ('Teste', 'teste@example.com', 'hash', 'salt')")
        for nome, modulo in (
            ("criar_conversa", conversas),
            ("listar_conversas_do_usuario", conversas),
            ("criar_mensagem", mensagens),
            ("listar_mensagens_da_conversa", mensagens),
        ):
            self.stack.enter_context(patch(
                f"NOVA.interface.app.{nome}",
                side_effect=partial(getattr(modulo, nome), db_path=self.db_path),
            ))
        self.widgets = {}
        for nome in ("CTkLabel", "CTkTextbox", "CTkFrame", "CTkScrollableFrame",
                     "CTkEntry", "CTkButton"):
            self.widgets[nome] = self.stack.enter_context(patch(f"NOVA.interface.app.ctk.{nome}"))
        self.app = SimpleNamespace(
            usuario_id=1, usuario_nome="Teste", conversa_id_atual=None,
            processando=False, aguardando_arquivo=False, nome_arquivo="",
            historico_comandos=[], resultados=Queue(), main=MagicMock(),
            entrada=MagicMock(), btn_enviar=MagicMock(), atualizar_menu=MagicMock(),
            limpar_main=MagicMock(), escrever_chat=MagicMock(), after=MagicMock(),
            executar_comando_em_segundo_plano=MagicMock(),
        )
        for nome in ("mostrar_chat", "abrir_conversa", "mostrar_historico",
                     "enviar_comando", "concluir_processamento", "verificar_resultados"):
            setattr(self.app, nome, MethodType(getattr(NovaApp, nome), self.app))

    def enviar(self, texto):
        self.app.entrada.get.return_value = texto
        self.app.enviar_comando()

    def test_envio_historico_abertura_e_retorno(self):
        self.enviar("pesquise Python")
        cid = self.app.conversa_id_atual
        self.app.concluir_processamento("Resposta de teste")
        self.app.mostrar_historico()
        self.widgets["CTkLabel"].assert_any_call(
            self.widgets["CTkFrame"].return_value,
            text="pesquise Python", font=("Segoe UI", 15, "bold"), anchor="w",
        )
        # Executa o callback do cartão, como um clique no histórico.
        callback = self.widgets["CTkFrame"].return_value.bind.call_args.args[1]
        callback(None)
        self.app.chat.insert.assert_any_call("end", "usuario: pesquise Python\n\n")
        self.app.chat.insert.assert_any_call("end", "nova: Resposta de teste\n\n")
        self.app.chat.insert.reset_mock()
        self.app.mostrar_chat()
        self.app.chat.insert.assert_any_call("end", "nova: Resposta de teste\n\n")
        self.enviar("pesquise SQLite")
        self.assertEqual(self.app.conversa_id_atual, cid)
        self.assertEqual(len(conversas.listar_conversas_do_usuario(1, self.db_path)), 1)
        self.assertEqual(len(mensagens.listar_mensagens_da_conversa(cid, self.db_path)), 3)

    def test_resposta_pendente_permanece_na_conversa_de_origem(self):
        self.enviar("pesquise Python")
        origem = self.app.conversa_id_atual
        with patch("NOVA.interface.app.threading.Thread") as thread, patch(
            "NOVA.interface.app.processar_comando", return_value="Resposta pendente"
        ):
            NovaApp.executar_comando_em_segundo_plano(self.app, "pesquise Python")
            outra = conversas.criar_conversa(1, "Outra conversa", self.db_path)
            self.app.abrir_conversa(outra)
            thread.call_args.kwargs["target"]()
        self.app.escrever_chat.reset_mock()
        self.app.verificar_resultados()
        self.assertEqual(mensagens.listar_mensagens_da_conversa(origem, self.db_path)[-1]["conteudo"],
                         "Resposta pendente")
        self.assertEqual(mensagens.listar_mensagens_da_conversa(outra, self.db_path), [])
        self.app.escrever_chat.assert_not_called()

    def test_respostas_de_criacao_de_arquivo_sao_salvas(self):
        self.enviar("crie arquivo notas")
        with patch("NOVA.interface.app.criar_arquivo_texto", return_value="Arquivo criado"):
            self.enviar("Meu conteudo")
        registros = mensagens.listar_mensagens_da_conversa(self.app.conversa_id_atual, self.db_path)
        self.assertEqual([m["remetente"] for m in registros], ["usuario", "nova", "usuario", "nova"])
        self.assertEqual(registros[-1]["conteudo"], "Arquivo criado")

    def test_trocar_conversa_cancela_conteudo_de_arquivo_pendente(self):
        self.enviar("crie arquivo notas")
        self.assertTrue(self.app.aguardando_arquivo)
        outra = conversas.criar_conversa(1, "Outra", self.db_path)
        self.app.abrir_conversa(outra)
        self.assertFalse(self.app.aguardando_arquivo)
        self.assertEqual(self.app.nome_arquivo, "")


if __name__ == "__main__":
    unittest.main()
