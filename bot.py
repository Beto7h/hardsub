import os
import asyncio
import time
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

# Inicialización del cliente
bot = Client(
    "HarsubBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

user_data = {}

# --- FUNCIÓN DE BARRA DE PROGRESO ---
async def progress_bar(current, total, status_msg, start_time, action):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = f"{round((total - current) / speed)}s" if speed > 0 else "..."
        bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
        
        msg = (f"🚀 **{action}**\n\n"
               f"进度: `{bar}` {round(percentage, 2)}%\n"
               f"⚡ Velocidad: `{round(speed / 1024 / 1024, 2)} MB/s` \n"
               f"⏱️ ETA: `{eta}`")
        try:
            await status_msg.edit(msg)
        except:
            pass

# --- MANEJADORES DE MENSAJES ---

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar el proceso de Hardsub.")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    
    # Validar si es video
    if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith("video/")):
        user_data[user_id] = {"video": message, "subtitle": None, "color": "&H00FFFF", "size": "24", "process": None}
        await message.reply("✅ Video recibido. Ahora envía el archivo de subtítulos **.srt**")
        
    # Validar si es subtítulo
    elif message.document and message.document.file_name and message.document.file_name.endswith(".srt"):
        if user_id not in user_data:
            await message.reply("❌ Primero debes enviar un video.")
            return
        
        user_data[user_id]["subtitle"] = message
        await message.reply(
            "🎬 **Archivos listos.**\nPresiona el botón para iniciar el pegado de subtítulos.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]])
        )

# --- CALLBACKS (BOTONES) ---

@bot.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    
    if query.data == "start":
        if user_id not in user_data or not user_data[user_id]["subtitle"]:
            await query.answer("❌ Faltan archivos.", show_alert=True)
            return
        await query.message.edit("⏳ Iniciando motores...")
        await run_engine(client, query.message, user_id)
        
    elif query.data == "cancel_process":
        if user_id in user_data and user_data[user_id]["process"]:
            try:
                user_data[user_id]["process"].terminate()
                await query.answer("🛑 Deteniendo y enviando lo procesado...", show_alert=True)
            except:
                await query.answer("No se pudo cancelar.")

# --- MOTOR DE PROCESAMIENTO ---

async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    
    # 1. Descargas
    v_path = await data["video"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando Video 📥"))
    s_path = await data["subtitle"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando SRT 📝"))

    output = f"{v_path}_harsub.mp4"
    await status_msg.edit(
        "⚙️ **PEGANDO SUBTÍTULOS...**\nEsto puede tardar varios minutos.\nSi cancelas, enviaré lo que se haya procesado hasta ahora.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR Y ENVIAR", callback_data="cancel_process")]])
    )
    
    # 2. FFmpeg (Uso de subprocess)
    cmd = [
        "ffmpeg", "-i", v_path,
        "-vf", f"subtitles={s_path}:force_style='PrimaryColour={data['color']},FontSize={data['size']}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-c:a", "copy",
        output, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd)
    user_data[user_id]["process"] = process
    await process.wait()

    # 3. Envío del video
    if os.path.exists(output) and os.path.getsize(output) > 5000:
        await status_msg.edit("📤 **Subiendo resultado...**")
        try:
            await client.send_video(
                chat_id=status_msg.chat.id,
                video=output,
                caption="✅ Proceso finalizado.",
                progress=progress_bar,
                progress_args=(status_msg, time.time(), "Subiendo a Telegram 📤")
            )
        except Exception as e:
            await status_msg.edit(f"❌ Error al subir: {e}")
    else:
        await status_msg.edit("❌ El video no se generó correctamente o fue cancelado muy pronto.")

    # 4. Limpieza final
    for p in [v_path, s_path, output]:
        if os.path.exists(p):
            os.remove(p)
    if user_id in user_data:
        del user_data[user_id]
    
    try:
        await status_msg.delete()
    except:
        pass

# --- INICIO DEL BOT (Esto es lo que faltaba) ---
if __name__ == "__main__":
    print("✅ Bot iniciado correctamente.")
    bot.run()
