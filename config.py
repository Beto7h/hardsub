import os
from dotenv import load_dotenv

# Carga el archivo .env si existe (útil para pruebas locales o en VPS como Contabo)
load_dotenv()

class Config:
    # --- DATOS DE TELEGRAM (Obtenlos en my.telegram.org) ---
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    
    # --- DATOS DEL BOT (Obtenlo de @BotFather) ---
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # --- SESIÓN PREMIUM (OPCIONAL) ---
    # Pega aquí tu String Session si quieres subir archivos de hasta 4GB.
    # Si lo dejas vacío "", el bot dividirá automáticamente los videos de más de 2GB.
    STRING_SESSION = os.environ.get("STRING_SESSION", "")
    
    # --- CONFIGURACIÓN DE ALMACENAMIENTO ---
    # En Koyeb se recomienda "/tmp", en Contabo "./downloads" está bien.
    DOWNLOAD_LOCATION = os.environ.get("DOWNLOAD_LOCATION", "./downloads")
    
    # --- CONFIGURACIÓN DE FFmpeg / HARSUB (Valores Iniciales) ---
    DEFAULT_COLOR = "&HFFFFFF"      # Blanco (BGR format)
    DEFAULT_FONT_SIZE = "24"
    DEFAULT_FONT_NAME = "Arial"
    DEFAULT_ITALIC = "0"           # 0 = Recta, 1 = Cursiva
    DEFAULT_OUTLINE = "2"          # 2 = Con contorno negro, 0 = Sin contorno
