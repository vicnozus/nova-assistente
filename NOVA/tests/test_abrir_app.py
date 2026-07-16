import tempfile
import unittest
from pathlib import Path

from NOVA.commands.app_launcher import carregar_apps_salvos, normalizar_nome, resolver_app, salvar_app


class AbrirAppTest(unittest.TestCase):
    def test_normalizar_nome_remove_palavras_de_ligacao(self):
        self.assertEqual(normalizar_nome("bloco de notas"), "bloco notas")

    def test_resolver_app_usa_alias_padrao(self):
        self.assertEqual(resolver_app("bloco de notas"), ("bloco notas", "notepad.exe"))
        self.assertEqual(resolver_app("calculadora"), ("calculadora", "calc.exe"))

    def test_salvar_e_carregar_app(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "apps_salvos.json"
            salvar_app("Visual Studio Code", "C:/Apps/Code.lnk", arquivo)

            self.assertEqual(
                carregar_apps_salvos(arquivo),
                {"visual studio code": Path("C:/Apps/Code.lnk")},
            )


if __name__ == "__main__":
    unittest.main()
