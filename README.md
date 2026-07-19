---

## 📱 ¿Cómo usar el Bot en Telegram?

Una vez que el bot esté encendido en tu VPS, interactuar con él es sumamente sencillo. Sigue este flujo lógico de comandos para procesar tus videos:

### 1. Iniciar el Bot

Busca tu bot por su nombre de usuario en Telegram y presiona el botón **Iniciar** o envía el comando:

```text
/start

```

El bot te responderá con un mensaje de bienvenida confirmando que está en línea y listo para recibir tareas.

### 2. Enviar los Archivos (El Orden Importa)

Para que el bot pueda fusionar correctamente el video con sus subtítulos, debes enviárselos en el siguiente orden:

1. **Envía el Video:** Sube el archivo de video (`.mp4`, `.mkv`, `.avi`, etc.) al chat del bot. Puedes enviarlo como archivo (sin compresión) o como video normal.
2. **Envía el Subtítulo:** Inmediatamente después, envía el archivo de subtítulos correspondiente (formatos soportados: `.srt` o `.ass`).

### 3. Configuración de Estilos (Opcional)

Si deseas cambiar el diseño por defecto antes de iniciar el procesamiento, puedes usar los comandos de personalización:

* `/setfont <Nombre>` - Cambia la tipografía de los subtítulos. *Ejemplo: `/setfont Trebuchet MS*`
* `/setsize <Número>` - Cambia el tamaño de la letra. *Ejemplo: `/setsize 28*`
* `/setcolor <Código>` - Cambia el color del texto usando el formato ASS. *Ejemplo: `/setcolor &H0000FF` (Rojo)*

### 4. Iniciar el "Hardsubbing"

Una vez que el bot tenga vinculados ambos archivos, te mostrará un menú interactivo o procesará automáticamente el video usando **FFmpeg**.

* El bot descargará los archivos internamente en la carpeta aislada `hardownload/downloads`.
* FFmpeg empezará a "quemar" los subtítulos píxel por píxel.
* Al finalizar, el bot subirá el archivo resultante (`hardownload/output`) al canal temporal que configuraste en tu `DUMP_CHAT_ID` y te lo reenviará de vuelta terminado.

---

*¡Listo! Con esto tu repositorio de GitHub tendrá una documentación impecable y profesional de inicio a fin.*
