import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

bot = Client(
    "HarsubBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

user_settings = {}

# Función para la barra de progreso
async def progress_bar(current, total, status_msg, start_time, action):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff)
        eta = round((total - current) / speed) if speed > 0 else 0
        
        # Barra visual
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        msg = (f"**{action}**\n"
               f"[{bar}] {round(percentage, 2)}%\n"
               f"🚀 Velocidad: {round(speed / 1024 / 1024, 2)} MB/s\n"
               f"⏱️ ETA: {eta}s")
        try:
            await status_msg.edit(msg)
        except:
            pass

@bot.on_message(filters.video | filters.document | filters.command("start"))
async def handle_message(client, message):
    if message.text == "/start":
        await message.reply("👋 ¡Hola! Envíame cualquier video y le pegaré los subtítulos.")
        return

    # Validar que sea video
    is_video = message.video or (message.document and message.document.mime_type.startswith("video/"))
    if not is_video:
        return

    user_id = message.from_user.id
    # Guardamos el mensaje del video para procesarlo después
    user_settings[user_id] = {
        "video_msg": message,
        "color": "&H00FFFF", 
        "size": "24"
    }

    await message.reply(
        "🎬 **Video detectado.**\nConfigura el estilo:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Amarillo 🟡", callback_data="set_col_&H00FFFF"),
             InlineKeyboardButton("Blanco ⚪", callback_data="set_col_&HFFFFFF")],
            [InlineKeyboardButton("Pequeño", callback_data="set_siz_18"),
             InlineKeyboardButton("Grande", callback_data="set_siz_32")],
            [InlineKeyboardButton("🚀 EMPEZAR", callback_data="start_harsub")]
        ])
    )

@bot.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_settings:
        await query.answer("Envía el video de nuevo.", show_alert=True)
        return

    if query.data.startswith("set_col_"):
        user_settings[user_id]["color"] = query.data.split("_")[2]
        await query.answer("Color fijado.")
    
    elif query.data.startswith("set_siz_"):
        user_settings[user_id]["size"] = query.data.split("_")[2]
        await query.answer("Tamaño fijado.")

    elif query.data == "start_harsub":
        await query.message.edit("⏳ Preparando archivos...")
        await run_harsub(client, query.message, user_id)

async def run_harsub(client, status_msg, user_id):
    data = user_settings[user_id]
    video_msg = data["video_msg"]
    
    # 1. DESCARGA
    start_time = time.time()
    input_path = await video_msg.download(
        progress=progress_bar,
        progress_args=(status_msg, start_time, "📥 Descargando...")
    )

    # 2. PROCESAMIENTO (FFMPEG)
    output_path = f"{input_path}_harsub.mp4"
    await status_msg.edit("⚙️ **Pegando subtítulos...**\nEsto puede tardar varios minutos.")
    
    # Comando FFmpeg (Asumimos que el video ya trae subs o hay un .srt con el mismo nombre)
    # Si quieres pegar un archivo .srt externo, el comando cambia.
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", f"subtitles={input_path}:force_style='PrimaryColour={data['color']},FontSize={data['size']}'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-c:a", "copy",
        output_path, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()

    # 3. SUBIDA
    await status_msg.edit("📤 **Subiendo video final...**")
    start_time = time.time()
    await client.send_video(
        chat_id=video_msg.chat.id,
        video=output_path,
        caption="✅ ¡Aquí tienes tu video con Harsub!",
        progress=progress_bar,
        progress_args=(status_msg, start_time, "📤 Subiendo...")
    )

    # Limpieza
    if os.path.exists(input_path): os.remove(input_path)
    if os.path.exists(output_path): os.remove(output_path)
    await status_msg.delete()

bot.run()
