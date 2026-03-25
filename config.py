import os
from dotenv import load_dotenv

# Carga el archivo .env si existe
load_dotenv()

class Config:
    # --- DATOS DE TELEGRAM ---
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    
    # --- DATOS DEL BOT ---
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # --- SESIÓN PREMIUM ---
    # Necesaria para subir archivos de hasta 4GB y que la barra de progreso sea visible.
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
