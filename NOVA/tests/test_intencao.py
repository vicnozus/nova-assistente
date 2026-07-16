import unittest

from NOVA.models.intent import interpretar_local, limpar_valor


class InterpretarIntencaoTest(unittest.TestCase):
    def test_pesquisa_remove_palavras_de_ligacao(self):
        resultado = interpretar_local("Pesquise, por Hollow Knight!")
        self.assertEqual(resultado["acao"], "pesquisar")
        self.assertEqual(resultado["valor"], "Hollow Knight")

    def test_criar_arquivo_reconhece_variacao_do_comando(self):
        resultado = interpretar_local("crie arquivo notas")
        self.assertEqual(resultado["acao"], "criar_arquivo")
        self.assertEqual(resultado["valor"], "notas")

    def test_zip_com_nome_de_arquivo_e_reconhecido(self):
        resultado = interpretar_local("extraia backup.zip")
        self.assertEqual(resultado["acao"], "extrair_zip")
        self.assertEqual(resultado["valor"], "backup.zip")

    def test_limpar_valor_preserva_maiusculas(self):
        self.assertEqual(limpar_valor("sobre Visual Studio Code"), "Visual Studio Code")


if __name__ == "__main__":
    unittest.main()
