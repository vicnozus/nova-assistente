# Nova

Assistente desktop em Python para pesquisar na Wikipédia, abrir aplicativos, criar arquivos de texto e extrair ZIPs.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite o `.env` e informe `GEMINI_KEY` somente se quiser usar Gemini como alternativa para comandos que a Nova não reconhece localmente.

## Executar

```powershell
python -m NOVA.main
```

## Exemplos

- `pesquise Hollow Knight`
- `abra o bloco de notas`
- `crie arquivo ideias.txt`
- `extraia backup.zip`

## Testes

```powershell
python -m unittest discover -s NOVA/tests
```
