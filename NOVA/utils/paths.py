from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = PACKAGE_DIR.parent
ASSETS_DIR = PACKAGE_DIR / "assets"
DATABASE_DIR = PACKAGE_DIR / "database"

ICON_PATH = ASSETS_DIR / "Nova_imagem.ico"
DARK_PURPLE_THEME_PATH = ASSETS_DIR / "dark-purple.json"
NOVA_DB_PATH = DATABASE_DIR / "nova.db"
SAVED_APPS_PATH = DATABASE_DIR / "apps_salvos.json"
