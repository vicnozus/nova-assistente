"""Procura aplicativos conhecidos, salvos e instalados no Windows."""

import json
import os
from functools import lru_cache
from pathlib import Path

from NOVA.models.intent import limpar_valor
from NOVA.utils.paths import SAVED_APPS_PATH


ARQUIVO_APPS_SALVOS = SAVED_APPS_PATH

APPS_PADRAO = {
    "bloco de notas": "notepad.exe",
    "bloco notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorador": "explorer.exe",
    "arquivos": "explorer.exe",
    "cmd": "cmd.exe",
    "terminal": "cmd.exe",
    "gerenciador de tarefas": "taskmgr.exe",
}


def normalizar_nome(nome):
    return limpar_valor(str(nome)).casefold()


def carregar_apps_salvos(caminho=ARQUIVO_APPS_SALVOS):
    try:
        with Path(caminho).open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(dados, dict):
        return {}
    return {normalizar_nome(nome): Path(caminho_app) for nome, caminho_app in dados.items()}


def salvar_app(nome, caminho_app, caminho=ARQUIVO_APPS_SALVOS):
    apps = carregar_apps_salvos(caminho)
    apps[normalizar_nome(nome)] = Path(caminho_app)
    dados = {nome_app: str(caminho_app) for nome_app, caminho_app in sorted(apps.items())}
    Path(caminho).write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


@lru_cache(maxsize=1)
def buscar_apps_instalados():
    pastas_atalhos = [
        Path(os.environ.get("ProgramData", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("AppData", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]
    apps = {}
    for pasta in pastas_atalhos:
        if pasta.exists():
            for atalho in pasta.rglob("*.lnk"):
                apps.setdefault(normalizar_nome(atalho.stem), atalho)
    return apps


def encontrar_por_nome(nome_app, apps):
    nome_normalizado = normalizar_nome(nome_app)
    if not nome_normalizado:
        return None

    if nome_normalizado in apps:
        return nome_normalizado, apps[nome_normalizado]

    encontrados = [
        (nome, caminho)
        for nome, caminho in apps.items()
        if nome_normalizado in nome or nome in nome_normalizado
    ]
    if not encontrados:
        return None
    return min(encontrados, key=lambda item: (len(item[0]), item[0]))


def resolver_app(nome_app):
    for apps in (APPS_PADRAO, carregar_apps_salvos()):
        encontrado = encontrar_por_nome(nome_app, apps)
        if encontrado:
            return encontrado

    encontrado = encontrar_por_nome(nome_app, buscar_apps_instalados())
    if encontrado:
        nome_real, caminho = encontrado
        salvar_app(nome_real, caminho)
        return nome_real, caminho
    return None
