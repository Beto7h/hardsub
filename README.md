🎬 Hardsub Telegram Bot (Beto7h/hardsub)
Un potente bot de Telegram auto-alojable escrito en Python para automatizar el proceso de Hardsubbing (pegar/incrustar subtítulos de forma permanente en un video) utilizando la potencia de procesamiento de FFmpeg.

Este bot incluye soporte para String Sessions de Telegram Premium, permitiéndote saltar el límite tradicional de 2 GB de Telegram y descargar o subir archivos de hasta 4 GB sin restricciones.

✨ Características Principales
Automatización Completa: Envíale un video y un archivo de subtítulos (.srt o .ass), y el bot se encargará del resto.

Aislamiento Total: El almacenamiento está diseñado para guardarse en la carpeta local hardownload/, evitando que tus archivos colisionen si tienes otros bots alojados en el mismo servidor.

Soporte Premium (Hasta 4 GB): Capacidad para procesar archivos grandes usando una sesión de usuario Premium en segundo plano.

Despliegue con Un Solo Comando: Configurado nativamente para compilarse y correr en contenedores de Docker.

🛠️ Requisitos Previos
Antes de realizar el despliegue, asegúrate de obtener las siguientes credenciales de Telegram:

API_ID y API_HASH: Se obtienen registrando una aplicación en my.telegram.org.

BOT_TOKEN: Crea tu bot en Telegram conversando con @BotFather.

DUMP_CHAT_ID: Crea un canal privado en Telegram, añade a tu bot como Administrador y obtén su ID única (debe empezar con -100). El bot usará este canal como almacenamiento temporal.

STRING_SESSION (Opcional): Si deseas procesar archivos de más de 2 GB (hasta 4 GB), es necesario generar un String Session usando una cuenta con Telegram Premium activo.

🚀 Despliegue en un VPS usando Docker (Vía PuTTY)
Este es el método de instalación recomendado. Docker empaqueta automáticamente todas las dependencias críticas (como Python y FFmpeg) sin alterar el sistema operativo de tu servidor.

Paso 1: Conéctate a tu servidor
Abre PuTTY, ingresa la IP de tu VPS y accede como usuario root (o un usuario con privilegios sudo).

Paso 2: Clonar el Repositorio
Descarga el código del proyecto y accede al directorio raíz:

Bash
git clone https://github.com/Beto7h/hardsub.git
cd hardsub
Paso 3: Configurar el Archivo de Entorno (.env)
Por motivos de seguridad, las credenciales reales nunca deben subirse a GitHub. Debes crear un archivo local .env en tu VPS:

Bash
nano .env
Pega el siguiente bloque de configuración y reemplaza los valores con tus credenciales reales:

Fragmento de código
API_ID=1234567
API_HASH=tu_api_hash_aqui
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
DUMP_CHAT_ID=-1001234567890

# Deja esta línea vacía si no usas una cuenta Premium
STRING_SESSION=

# Parámetros avanzados (Opcional modificarlos)
DOWNLOAD_LOCATION=./downloads
DEFAULT_COLOR=&HFFFFFF
DEFAULT_FONT_NAME=Arial
DEFAULT_FONT_SIZE=24
DEFAULT_PRESET=veryfast
DEFAULT_CRF=24
Para guardar los cambios en el editor Nano, presiona Ctrl + O, luego Enter. Para salir, presiona Ctrl + X.

Paso 4: Inicializar Almacenamiento Aislado
Crea las carpetas físicas en donde el bot guardará las descargas y dale los permisos necesarios a Docker:

Bash
mkdir -p hardownload/downloads hardownload/output
chmod -R 777 hardownload
Paso 5: Construir y Encender el Bot
Ejecuta el comando de Docker Compose para compilar la imagen de FFmpeg y poner a correr el bot de manera persistente en segundo plano (modo detached):

Bash
docker compose up -d --build
¡Listo! El bot ya estará activo en Telegram y puedes cerrar tu ventana de PuTTY con total seguridad.

📊 Comandos de Mantenimiento Útiles
Puedes administrar el contenedor ejecutando estos comandos desde la carpeta hardsub en tu VPS:

Monitorear la actividad (Logs en tiempo real): Ideal para verificar el progreso del procesamiento de video de FFmpeg o cazar errores.

Bash
docker compose logs -f --tail 50
Reiniciar el bot:

Bash
docker compose restart
Detener el bot por completo:

Bash
docker compose down
Actualizar el bot: Si se suben nuevas mejoras a este repositorio de GitHub, actualiza tu servidor en segundos corriendo:

Bash
git pull
docker compose up -d --build
🎨 Ajustes de Subtítulos (FFmpeg)
Si deseas cambiar el diseño por defecto de los subtítulos incrustados, edita los valores correspondientes en tu archivo .env:

DEFAULT_COLOR: Código de color en formato Hexadecimal inverso para subtítulos ASS (&H[BGR]). El valor &HFFFFFF representa blanco puro.

DEFAULT_PRESET: Regula la velocidad de codificación de FFmpeg (ultrafast, superfast, veryfast, faster, fast, medium). El valor veryfast ofrece el balance óptimo en un VPS para no congelar la CPU.

DEFAULT_CRF: Controla la calidad visual final. Escala de 0 a 51. Valores comunes recomendados entre 18 (máxima calidad / archivo pesado) y 28 (menor calidad / archivo liviano). El valor predeterminado es 24.
