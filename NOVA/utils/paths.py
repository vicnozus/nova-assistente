from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = PACKAGE_DIR.parent
ASSETS_DIR = PACKAGE_DIR / "assets"
DATABASE_DIR = PACKAGE_DIR / "database"

ICON_PATH = ASSETS_DIR / "Nova_imagem.ico"
USERS_DB_PATH = DATABASE_DIR / "usuarios.db"
SAVED_APPS_PATH = DATABASE_DIR / "apps_salvos.json"
