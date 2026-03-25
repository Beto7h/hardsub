import os
from dotenv import load_dotenv

# Carga las variables desde un archivo .env si existe
load_dotenv()

class Config:
    # --- CREDENCIALES DE TELEGRAM ---
    # Se obtienen de https://my.telegram.org
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    
    # El token que te da @BotFather
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # --- CANAL DUMP (LOGS / RESPALDO) ---
    # IMPORTANTE: En tu código usas 'DUMP_CHAT_ID'. 
    # Asegúrate de que sea el ID numérico (ej: -100123456789)
    DUMP_CHAT_ID = int(os.environ.get("DUMP_CHAT_ID", 0))

    # --- SESIÓN PREMIUM (OPCIONAL) ---
    # Si dejas esto vacío, el bot usará la cuenta normal del Bot.
    # Si pones el String Session, usará los beneficios Premium para descargar/subir.
    STRING_SESSION = os.environ.get("STRING_SESSION", "")
    
    # --- CONFIGURACIÓN DE ALMACENAMIENTO ---
    DOWNLOAD_LOCATION = os.environ.get("DOWNLOAD_LOCATION", "./downloads")
    
    # --- CONFIGURACIÓN DE FFmpeg / HARSUB (Valores Iniciales) ---
    DEFAULT_COLOR = "&HFFFFFF"      # Blanco (BGR format)
    DEFAULT_FONT_NAME = "Arial"     # Fuente por defecto
    DEFAULT_FONT_SIZE = 24          # Tamaño en px
    DEFAULT_OUTLINE = 2             # 2 = Medio, 1 = Fino, 0 = Sin contorno
    
    # --- AJUSTES DE CODIFICACIÓN ---
    DEFAULT_PRESET = "veryfast"     # Velocidad de proceso
    DEFAULT_CRF = "24"              # Calidad (18 alta, 24 buena, 28 baja)
