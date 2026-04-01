import os
from dotenv import load_dotenv

# Carga las variables desde un archivo .env si existe
load_dotenv()

class Config:
    # --- CREDENCIALES DE TELEGRAM ---
    # En GitHub dejamos valores genéricos (0 o "") 
    # El bot leerá los reales desde las Variables de Entorno del servidor
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # --- CANAL DUMP ---
    DUMP_CHAT_ID = int(os.environ.get("DUMP_CHAT_ID", 0))

    # --- SESIÓN PREMIUM ---
    STRING_SESSION = os.environ.get("STRING_SESSION", "")

    # --- CONFIGURACIONES POR DEFECTO ---
    DOWNLOAD_LOCATION = os.environ.get("DOWNLOAD_LOCATION", "./downloads")
    DEFAULT_COLOR = os.environ.get("DEFAULT_COLOR", "&HFFFFFF")
    DEFAULT_FONT_NAME = os.environ.get("DEFAULT_FONT_NAME", "Arial")
    DEFAULT_FONT_SIZE = int(os.environ.get("DEFAULT_FONT_SIZE", 24))
    DEFAULT_OUTLINE = int(os.environ.get("DEFAULT_OUTLINE", 2))
    DEFAULT_PRESET = os.environ.get("DEFAULT_PRESET", "veryfast")
    DEFAULT_CRF = os.environ.get("DEFAULT_CRF", "24")
