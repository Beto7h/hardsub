FROM python:3.10-slim

# Instalar FFmpeg y dependencias del sistema esenciales para procesar video
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copiar e instalar requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del bot
COPY . .

# Comando para arrancar el bot directamente usando las variables de config.py
CMD ["python", "bot.py"]
