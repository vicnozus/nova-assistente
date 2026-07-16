"""Integração opcional com Gemini para comandos não reconhecidos localmente."""

import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
ACOES_PERMITIDAS = {"pesquisar", "abrir_app", "criar_arquivo", "extrair_zip"}


def inteligencia_assistente(comando_usuario):
    chave = os.getenv("GEMINI_KEY")
    if not chave:
        return None

    prompt = f'''Você é o motor de um assistente de PC.
Converta o comando do usuário em um JSON puro.
Ações permitidas: "pesquisar", "abrir_app", "criar_arquivo", "extrair_zip".
Formato: {{"acao": "uma ação permitida", "valor": "texto"}}.
Comando do usuário: {comando_usuario!r}
Responda apenas o JSON, sem markdown.'''
    try:
        client = genai.Client(api_key=chave)
        response = client.models.generate_content(model="models/gemini-2.5-flash", contents=prompt)
        texto = response.text.replace("```json", "").replace("```", "").strip()
        dados = json.loads(texto)
        if not isinstance(dados, dict) or dados.get("acao") not in ACOES_PERMITIDAS:
            return None
        return dados
    except (json.JSONDecodeError, AttributeError, ValueError):
        return None
