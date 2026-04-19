# 🎬 Hardsub Bot - Guía de Instalación y Despliegue

Este bot de Telegram pega subtítulos (.srt) a videos (.mp4) de forma automática, optimizado para conservar la calidad original y el aspecto panorámico sin deformaciones.

## 🚀 Requisitos Previos

Antes de empezar, asegúrate de tener instalado en tu VPS:
* **Python 3.10** o superior.
* **FFmpeg** (Instalar con: `sudo apt update && sudo apt install ffmpeg -y`).

---

## 🛠️ Instalación Paso a Paso

### 1. Clonar el repositorio
Si aún no lo tienes en el servidor:
```bash
git clone https://github.com/Beto7h/hardsub
cd hardsub
```

### 2. Configuración de Variables
Edita el archivo `config.py` con tus credenciales:
```python
class Config:
    API_ID = 123456
    API_HASH = "tu_api_hash"
    BOT_TOKEN = "tu_bot_token"
    DUMP_CHAT_ID = -100123456789  # Canal para proceso de archivos
    STRING_SESSION = "" # Opcional: Para usar cuenta Premium
```

### 3. Instalación de Librerías (Solución a errores de entorno)
Debido a las nuevas protecciones de Python (PEP 668), usa este comando para forzar la instalación de dependencias:

```bash
pip install -r requirements.txt --break-system-packages
pip install pyrogram tgcrypto hachoir --break-system-packages
```

---

## 🛰️ Despliegue con Screen (24/7 Activo)

Para que el bot no se apague al cerrar la terminal, usamos sesiones de "espejo" o terminales virtuales:

1. **Crear e iniciar la sesión:**
   ```bash
   screen -S harsub
   ```

2. **Ejecutar el bot dentro de la sesión:**
   ```bash
   python3 bot.py
   ```

3. **Salir de la sesión (sin apagar el bot):**
   Presiona la combinación: `Ctrl + A` y luego la tecla `D`.

4. **Volver a entrar a la sesión para ver logs:**
   ```bash
   screen -r harsub
   ```

---

## 💎 Mejoras Implementadas

Este bot incluye soluciones a los errores más comunes:

* **Error 0 Bytes:** Se implementó un filtro de escalado que redondea las dimensiones a números pares (`trunc(iw/2)*2`), requisito obligatorio para el codificador H.264.
* **Subtítulos Estirados:** Se añadió `scale='iw*sar':'ih',setsar=1` para que los videos panorámicos (iPhone/Cámaras) mantengan su aspecto real.
* **ETA Real:** El progreso ahora muestra el tiempo restante estimado basado en la velocidad de procesamiento de FFmpeg.
* **Logs de FFmpeg:** Si un video falla, el bot enviará los últimos errores técnicos al chat para facilitar el diagnóstico.

---

## 📋 Comandos Útiles de Mantenimiento

* **Ver sesiones activas:** `screen -ls`
* **Cerrar una sesión colgada:** `screen -X -S harsub quit`
* **Limpiar carpeta de descargas:** El bot lo hace automáticamente al iniciar, pero puedes hacerlo manual con `rm -rf downloads/*`.

---

## ⚠️ Notas de Seguridad
Si recibes el error `ModuleNotFoundError`, repite el paso de instalación con `--break-system-packages`. Es común tras actualizaciones del sistema operativo en el VPS.

---

### ¿Cómo usar este archivo?
1. Crea un archivo nuevo en tu terminal: `nano README.md`
2. Pega el contenido de arriba.
3. Presiona `Ctrl + O` para guardar y `Ctrl + X` para salir.

