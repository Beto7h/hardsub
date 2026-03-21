import os
import asyncio
import time
import math
import signal
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

bot = Client("HarsubBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# Diccionario expandido para control de procesos
user_data = {}

async def progress_bar(current, total, status_msg, start_time, action, can_cancel=False):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = f"{round((total - current) / speed)}s" if speed > 0 else "..."
        bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
        
        msg = (f"🚀 **{action}**\n\n进度: `{bar}` {round(percentage, 2)}%\n"
               f"⚡ Velocidad: `{round(speed / 1024 / 1024, 2)} MB/s` \n⏱️ ETA: `{eta}`")
        
        reply_markup = None
        if can_cancel:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR Y ENVIAR", callback_data="cancel_process")]])
        
        try:
            await status_msg.edit(msg, reply_markup=reply_markup)
        except: pass

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    if message.video or (message.document and message.document.mime_type.startswith("video/")):
        user_data[user_id] = {"video": message, "subtitle": None, "color": "&H00FFFF", "size": "24", "process": None}
        await message.reply("✅ Video recibido. Envía el **.srt**")
    elif message.document and message.document.file_name.endswith(".srt"):
        if user_id in user_data:
            user_data[user_id]["subtitle"] = message
            await message.reply("🎬 Archivos listos.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 INICIAR", callback_data="start")]]))

@bot.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    
    if query.data == "start":
        await query.message.edit("⏳ Iniciando...")
        await run_engine(client, query.message, user_id)
        
    elif query.data == "cancel_process":
        if user_id in user_data and user_data[user_id]["process"]:
            # Enviamos señal de terminar al proceso de FFmpeg
            user_data[user_id]["process"].terminate()
            await query.answer("🛑 Cancelando... Enviando parte procesada.", show_alert=True)

async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    v_path = await data["video"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando Video 📥"))
    s_path = await data["subtitle"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando SRT 📝"))

    output = f"{v_path}_final.mp4"
    await status_msg.edit("⚙️ **PEGANDO SUBTÍTULOS...**\nPresiona abajo para detener y recibir lo que vaya procesado.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR Y ENVIAR", callback_data="cancel_process")]]))
    
    # Comando FFmpeg
    cmd = ["ffmpeg", "-i", v_path, "-vf", f"subtitles={s_path}:force_style='PrimaryColour={data['color']}'", 
           "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "copy", output, "-y"]
    
    # Iniciamos el proceso y lo guardamos en el diccionario para poder cancelarlo
    process = await asyncio.create_subprocess_exec(*cmd)
    user_data[user_id]["process"] = process
    
    await process.wait() # Aquí esperamos a que termine o sea cancelado

    # 3. ENVÍO (Ya sea completo o parcial)
    if os.path.exists(output) and os.path.getsize(output) > 1000: # Verificamos que el archivo tenga datos
        await status_msg.edit("📤 **Enviando resultado...**")
        await client.send_video(
            chat_id=status_msg.chat.id,
            video=output,
            caption="✅ Aquí tienes el resultado (Proceso finalizado o detenido por usuario).",
            progress=progress_bar, progress_args=(status_msg, time.time(), "Subiendo a Telegram 📤")
        )
    else:
        await status_msg.edit("❌ El proceso fue cancelado demasiado pronto y no se generó video.")

    # Limpieza
    for p in [v_path, s_path, output]:
        if os.path.exists(p): os.remove(p)
    if user_id in user_data: del user_data[user_id]
