import os
import asyncio
import time
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

bot = Client(
    "HarsubBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Diccionario para guardar video, subtítulo y ajustes por usuario
user_settings = {}

# --- FUNCIÓN DE BARRA DE PROGRESO MEJORADA ---
async def progress_bar(current, total, status_msg, start_time, action):
    now = time.time()
    diff = now - start_time
    # Actualiza cada 4 segundos para evitar spam/bloqueo de Telegram
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        
        # Cálculo de ETA (Tiempo estimado)
        if speed > 0:
            eta_seconds = round((total - current) / speed)
            eta = f"{eta_seconds}s" if eta_seconds < 60 else f"{round(eta_seconds/60, 1)}m"
        else:
            eta = "Calculando..."

        # Barra visual [████░░░░░░]
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        msg = (f"🚀 **{action}**\n\n"
               f"进度: `{bar}` {round(percentage, 2)}%\n"
               f"⚡ Velocidad: `{round(speed / 1024 / 1024, 2)} MB/s` \n"
               f"⏱️ Tiempo restante: `{eta}`")
        try:
            await status_msg.edit(msg)
        except:
            pass

# --- MANEJADOR DE MENSAJES (VIDEO Y SUBTÍTULOS) ---
@bot.on_message(filters.video | filters.document | filters.command("start"))
async def handle_message(client, message):
    user_id = message.from_user.id

    if message.text == "/start":
        await message.reply("👋 ¡Hola! **Paso 1:** Envíame el video (cualquier formato).")
        return

    # Si recibimos un VIDEO
    is_video = message.video or (message.document and message.document.mime_type.startswith("video/"))
    if is_video:
        user_settings[user_id] = {"video": message, "subtitle": None, "color": "&H00FFFF", "size": "24"}
        await message.reply("✅ **Video guardado.**\n**Paso 2:** Ahora envíame el archivo de subtítulos **.srt**")
        return

    # Si recibimos un SUBTÍTULO
    if message.document and message.document.file_name.endswith(".srt"):
        if user_id not in user_settings:
            await message.reply("❌ Primero debes enviar un video.")
            return
        
        user_settings[user_id]["subtitle"] = message
        await message.reply(
            "🎬 **¡Todo listo!**\nConfigura el estilo de los subtítulos:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Amarillo 🟡", callback_data="set_col_&H00FFFF"),
                 InlineKeyboardButton("Blanco ⚪", callback_data="set_col_&HFFFFFF")],
                [InlineKeyboardButton("Pequeño", callback_data="set_siz_18"),
                 InlineKeyboardButton("Grande", callback_data="set_siz_32")],
                [InlineKeyboardButton("🚀 INICIAR HARDSUB", callback_data="start_harsub")]
            ])
        )

# --- MANEJADOR DE BOTONES ---
@bot.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_settings:
        await query.answer("Error: Envía los archivos de nuevo.", show_alert=True)
        return

    if query.data.startswith("set_col_"):
        user_settings[user_id]["color"] = query.data.split("_")[2]
        await query.answer("Color actualizado ✅")
    
    elif query.data.startswith("set_siz_"):
        user_settings[user_id]["size"] = query.data.split("_")[2]
        await query.answer("Tamaño actualizado ✅")

    elif query.data == "start_harsub":
        await query.message.edit("⏳ Iniciando descargas...")
        await run_harsub(client, query.message, user_id)

# --- PROCESO PRINCIPAL (DESCARGA, FFMPEG, SUBIDA) ---
async def run_harsub(client, status_msg, user_id):
    data = user_settings[user_id]
    
    # 1. DESCARGAS
    start_v = time.time()
    v_path = await data["video"].download(
        progress=progress_bar, progress_args=(status_msg, start_v, "Descargando Video 📥")
    )
    
    start_s = time.time()
    s_path = await data["subtitle"].download(
        progress=progress_bar, progress_args=(status_msg, start_s, "Descargando Subtítulo 📝")
    )

    # 2. PROCESAMIENTO FFmpeg
    output_path = f"{v_path}_harsub.mp4"
    await status_msg.edit("⚙️ **PROCESANDO VIDEO...**\nEsto puede tardar según el tamaño.\n\n`Estado: FFmpeg está pegando los subtítulos...`")
    
    # Comando FFmpeg para pegar SRT externo con estilos
    cmd = [
        "ffmpeg", "-i", v_path,
        "-vf", f"subtitles={s_path}:force_style='PrimaryColour={data['color']},FontSize={data['size']}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26", "-c:a", "copy",
        output_path, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()

    # 3. SUBIDA FINAL
    await status_msg.edit("✅ **Procesado con éxito.**\nIniciando subida a Telegram...")
    start_u = time.time()
    
    await client.send_video(
        chat_id=status_msg.chat.id,
        video=output_path,
        caption="✅ **¡Harsub Finalizado!**\n\nAquí tienes tu video con subtítulos permanentes.",
        progress=progress_bar,
        progress_args=(status_msg, start_u, "Subiendo Video Final 📤")
    )

    # LIMPIEZA DE ARCHIVOS (Koyeb tiene espacio limitado)
    for path in [v_path, s_path, output_path]:
        if os.path.exists(path):
            os.remove(path)
    
    await status_msg.delete()
    del user_settings[user_id]

bot.run()
