import os
from dotenv import load_dotenv

# Carga el archivo .env si existe (útil para pruebas locales)
load_dotenv()

class Config:
    # --- DATOS DE TELEGRAM (Obtenlos en my.telegram.org) ---
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    
    # --- DATOS DEL BOT (Obtenlo de @BotFather) ---
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # --- CONFIGURACIÓN DE ALMACENAMIENTO ---
    # Koyeb usa sistemas de archivos efímeros, así que usamos /tmp o una carpeta local
    DOWNLOAD_LOCATION = "./downloads"
    
    # --- CONFIGURACIÓN DE FFMEG / HARSUB ---
    # Estilos predeterminados si el usuario no elige en los botones
    DEFAULT_COLOR = "&H00FFFF"  # Amarillo en formato BGR
    DEFAULT_FONT_SIZE = "24"
    DEFAULT_FONT_NAME = "Arial"
