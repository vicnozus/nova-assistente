"""Interpretação local e leve dos comandos da Nova."""

INTENCOES = {
    "pesquisar": {
        "acao": "pesquisar",
        "gatilhos": [
            "pesquisar", "pesquisa", "buscar", "busca", "procurar", "procura",
            "encontrar", "encontra", "procure", "pesquise", "busque",
        ],
    },
    "abrir_app": {
        "acao": "abrir_app",
        "gatilhos": ["abrir", "abra", "abre", "iniciar", "inicie", "executar", "execute"],
    },
    "criar_arquivo": {
        "acao": "criar_arquivo",
        "gatilhos": ["criar", "crie", "fazer", "faça", "faz", "gerar", "gere"],
        "obrigatorias": ["arquivo"],
    },
    "extrair_zip": {
        "acao": "extrair_zip",
        "gatilhos": ["extrair", "extraia", "descompactar", "descompacte"],
    },
}

PALAVRAS_IGNORAR = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "é", "são", "ser",
    "para", "pra", "pro", "por", "da", "de", "do", "dos", "das", "no", "na",
    "nos", "nas", "mim", "favor", "pfv", "please", "que", "qual", "quais", "me",
    "minha", "meu", "minhas", "meus", "nova", "sobre", "aplicativo", "programa",
}


def _palavras(comando):
    return [palavra.strip(".,!?;:()[]{}\"").casefold() for palavra in comando.split()]


def limpar_valor(valor):
    """Remove palavras de ligação sem alterar a capitalização do valor informado."""
    palavras_filtradas = []
    for palavra in valor.split():
        palavra = palavra.strip(".,!?;:()[]{}\"")
        if palavra and palavra.casefold() not in PALAVRAS_IGNORAR:
            palavras_filtradas.append(palavra)
    return " ".join(palavras_filtradas).strip()


def interpretar_local(comando):
    palavras = _palavras(comando)

    for nome_intencao, dados in INTENCOES.items():
        gatilho_usado = next((gatilho for gatilho in dados["gatilhos"] if gatilho in palavras), None)
        if not gatilho_usado:
            continue

        obrigatorias = dados.get("obrigatorias", [])
        if not all(obrigatoria in palavras for obrigatoria in obrigatorias):
            continue

        if nome_intencao == "extrair_zip" and not any(
            palavra == "zip" or palavra.endswith(".zip") for palavra in palavras
        ):
            continue

        palavras_valor = [
            palavra_original
            for palavra_original, palavra in zip(comando.split(), palavras)
            if palavra != gatilho_usado and palavra not in obrigatorias
        ]
        return {
            "acao": dados["acao"],
            "valor": limpar_valor(" ".join(palavras_valor)),
            "gatilho": gatilho_usado,
            "intencao": nome_intencao,
        }

    return None
