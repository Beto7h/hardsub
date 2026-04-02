# 🎬 Harsub Bot - Auto Subtitle Burner

Este bot de Telegram permite "quemar" (pegar) subtítulos externos en formato `.srt` a archivos de video `.mp4`. Está optimizado para trabajar con archivos grandes (más de 2GB) mediante la integración de una cuenta **Telegram Premium**.

---

## 🚀 Métodos de Despliegue

### 1. Despliegue en VPS (Ubuntu/Debian vía Putty)
Este es el método recomendado para procesar videos pesados, ya que FFmpeg consume bastantes recursos.

**Paso 1: Actualizar el servidor e instalar dependencias**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip ffmpeg screen -y
```

**Paso 2: Clonar el repositorio**
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO
```

**Paso 3: Instalar librerías de Python**
```bash
pip3 install -r requirements.txt
```

**Paso 4: Configurar credenciales**
Edita el archivo `config.py` con tus datos (API_ID, HASH, TOKEN, etc.):
```bash
nano config.py
```

**Paso 5: Ejecutar con Screen (Para que no se apague)**
```bash
screen -S harsub
python3 bot.py
```
*(Para salir de la consola sin cerrar el bot: `Ctrl + A` y luego `D`. Para volver: `screen -r harsub`)*.

---

### 2. Despliegue en Koyeb (PaaS)
Ideal para despliegues rápidos y gratuitos/baratos.

1.  **Conecta tu GitHub:** Crea un nuevo "Service" y selecciona este repositorio.
2.  **Variables de Entorno:** No edites el `config.py`. En el panel de Koyeb, agrega las siguientes variables:
    * `API_ID`
    * `API_HASH`
    * `BOT_TOKEN`
    * `DUMP_CHAT_ID`
    * `STRING_SESSION` (Opcional, para >2GB)
3.  **Comandos:**
    * Build Command: `pip install -r requirements.txt`
    * Run Command: `python3 bot.py`
4.  **Instance:** Selecciona una instancia con al menos 1GB de RAM.

---

## 🛠️ Configuración (`config.py`)

| Variable | Descripción |
| :--- | :--- |
| `API_ID` | ID de API obtenido en my.telegram.org |
| `API_HASH` | Hash de API obtenido en my.telegram.org |
| `BOT_TOKEN` | Token de tu bot obtenido en @BotFather |
| `DUMP_CHAT_ID` | ID del canal (debe empezar con -100) |
| `STRING_SESSION` | Sesión Pyrogram de cuenta Premium (opcional) |

---

## 📖 Modo de Uso

1.  Usa el comando `/start` para activar el bot.
2.  Envía el **Video** que deseas procesar.
3.  Envía el archivo **.srt** de subtítulos.
4.  Personaliza el estilo (Color, Tamaño, Posición) en el menú interactivo.
5.  Presiona **🚀 INICIAR PROCESO**.
6.  El bot enviará el video terminado al chat. 
    * Si el video pesa **< 2GB**, lo envía el Bot.
    * Si el video pesa **> 2GB**, lo envía tu cuenta Premium automáticamente.

---

## 📂 Requisitos del Sistema
El archivo `requirements.txt` debe incluir:
* `pyrogram`
* `tgcrypto`
* `hachoir`

---

## ⚠️ Notas de Seguridad
* **IMPORTANTE:** No subas tu archivo `.session` o tu `config.py` real a GitHub si el repositorio es público.
* Asegúrate de que tanto el Bot como la cuenta Premium sean **Administradores** en el canal de Dump.

---

**Desarrollado con ❤️ por Beto.**
