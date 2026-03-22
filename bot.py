import os
import asyncio
import time
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from config import Config

# Inicialización
bot = Client("HarsubBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

premium_client = None
if hasattr(Config, "STRING_SESSION") and Config.STRING_SESSION:
    premium_client = Client("PremiumUser", api_id=Config.API_ID, api_hash=Config.API_HASH, session_string=Config.STRING_SESSION)

user_data = {}

# --- UTILIDADES ---
def get_video_info(file_path):
    try:
        metadata = extractMetadata(createParser(file_path))
        if not metadata: return 0, 0, 0
        duration = metadata.get("duration").seconds if metadata.has("duration") else 0
        width = metadata.get("width") if metadata.has("width") else 0
        height = metadata.get("height") if metadata.has("height") else 0
        return duration, width, height
    except: return 0, 0, 0

def time_to_seconds(time_str):
    """Convierte formato HH:MM:SS.ms de FFmpeg a segundos"""
    try:
        parts = time_str.split(':')
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except: return 0

# --- MENÚ DE CONFIGURACIÓN ---
def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    p_name = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[data['preset']]
    q_name = {"18": "Alta ⭐", "22": "Buena ✅", "28": "Baja 📉"}[data['crf']]

    text = (
        "🎬 **CONFIGURACIÓN DE PROCESADO**\n\n"
        f"🎨 **Color:** `{c_name}`\n"
        f"📏 **Tamaño:** `{data['size']}px`\n"
        f"🚀 **Velocidad:** `{p_name}`\n"
        f"🎯 **Calidad:** `{q_name}`\n\n"
        "Ajusta los parámetros antes de iniciar:"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Amarillo", callback_data="set_col_&H00FFFF"),
         InlineKeyboardButton("⚪ Blanco", callback_data="set_col_&HFFFFFF")],
        [InlineKeyboardButton("➖ Menos Tamaño", callback_data="set_siz_down"),
         InlineKeyboardButton("➕ Más Tamaño", callback_data="set_siz_up")],
        [InlineKeyboardButton("⚡ Rápido", callback_data="set_pre_ultrafast"),
         InlineKeyboardButton("🐢 Lento", callback_data="set_pre_slow")],
        [InlineKeyboardButton("⭐ Alta Calidad", callback_data="set_crf_18"),
         InlineKeyboardButton("✅ Buena Calidad", callback_data="set_crf_22")],
        [InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]
    ])
    return text, markup

# --- BARRA DE PROGRESO (DESCARGA/SUBIDA) ---
async def progress_bar(current, total, status_msg, start_time, action):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = f"{round((total - current) / speed)}s" if speed > 0 else "..."
        bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
        msg = (f"🚀 **{action}**\n\n进度: `{bar}` {round(percentage, 2)}%\n⚡: `{round(speed / 1024 / 1024, 2)} MB/s` \n⏱️ ETA: `{eta}`")
        try: await status_msg.edit(msg)
        except: pass

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar.")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith("video/")):
        user_data[user_id] = {
            "video": message, "subtitle": None, "color": "&HFFFFFF", 
            "size": 24, "italic": "0", "outline": "2", 
            "preset": "veryfast", "crf": "22", "process": None
        }
        await message.reply("✅ Video recibido. Ahora envía el archivo **.srt**")
    elif message.document and message.document.file_name and message.document.file_name.endswith(".srt"):
        if user_id not in user_data: return await message.reply("❌ Envía el video primero.")
        user_data[user_id]["subtitle"] = message
        text, markup = get_config_menu(user_id)
        await message.reply(text, reply_markup=markup)

@bot.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    if query.data.startswith("set_"):
        _, type_set, val = query.data.split("_")
        if type_set == "col": user_data[user_id]["color"] = val
        elif type_set == "pre": user_data[user_id]["preset"] = val
        elif type_set == "crf": user_data[user_id]["crf"] = val
        elif type_set == "siz":
            if val == "up": user_data[user_id]["size"] += 2
            else: user_data[user_id]["size"] = max(12, user_data[user_id]["size"] - 2)
        
        text, markup = get_config_menu(user_id)
        try: await query.message.edit(text, reply_markup=markup)
        except: pass

    elif query.data == "start":
        await query.message.edit("⏳ Iniciando motores...")
        await run_engine(client, query.message, user_id)

    elif query.data == "stop_ffmpeg":
        if user_id in user_data and user_data[user_id]["process"]:
            user_data[user_id]["process"].terminate()
            await query.answer("🛑 Proceso cancelado por el usuario", show_alert=True)

# --- MOTOR DE PROCESAMIENTO CON ETA Y PROGRESO REAL ---
async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    v_path = await data["video"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando Video 📥"))
    s_path = await data["subtitle"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando SRT 📝"))

    total_duration, w, h = get_video_info(v_path)
    output = f"{v_path}_harsub.mp4"
    style = f"PrimaryColour={data['color']},FontSize={data['size']},Italic={data['italic']},BorderStyle=1,Outline={data['outline']}"

    cmd = [
        "ffmpeg", "-i", v_path,
        "-vf", f"subtitles={s_path}:force_style='{style}'",
        "-c:v", "libx264", "-preset", data["preset"], "-crf", data["crf"], "-c:a", "copy",
        "-movflags", "faststart", "-progress", "pipe:1", # Pipe para leer progreso
        output, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    user_data[user_id]["process"] = process
    
    start_time = time.time()
    last_update = 0

    # Leer la salida de FFmpeg para calcular tiempo
    while True:
        line = await process.stdout.readline()
        if not line: break
        
        text = line.decode().strip()
        if "out_time=" in text:
            time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
            if time_match and total_duration > 0:
                current_time_str = time_match.group(1)
                current_seconds = time_to_seconds(current_time_str)
                
                # Solo actualizar cada 5 segundos para no saturar Telegram
                if time.time() - last_update > 5:
                    percentage = (current_seconds / total_duration) * 100
                    elapsed_time = time.time() - start_time
                    speed = current_seconds / elapsed_time if elapsed_time > 0 else 0
                    remaining_seconds = (total_duration - current_seconds) / speed if speed > 0 else 0
                    
                    bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
                    
                    msg = (
                        "⚙️ **PEGANDO SUBTÍTULOS...**\n\n"
                        f"📊 Progreso: `{bar}` {round(percentage, 1)}%\n"
                        f"⏱️ Procesado: `{current_time_str}` / `{time.strftime('%H:%M:%S', time.gmtime(total_duration))}`\n"
                        f"⏳ Restante: `{time.strftime('%H:%M:%S', time.gmtime(remaining_seconds))}`"
                    )
                    
                    try:
                        await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="stop_ffmpeg")]]))
                        last_update = time.time()
                    except: pass

    await process.wait()

    if os.path.exists(output) and user_data[user_id]["process"].returncode == 0:
        duration, width, height = get_video_info(output)
        f_size = os.path.getsize(output)
        
        use_premium = False
        if premium_client:
            try:
                if not premium_client.is_connected: await premium_client.start()
                use_premium = True
            except: use_premium = False

        uploader = premium_client if (use_premium and f_size < 4000*1024*1024) else client
        
        up_msg = await client.send_message(status_msg.chat.id, "📤 Subiendo video final...")
        await uploader.send_video(
            chat_id=status_msg.chat.id,
            video=output,
            caption="✅ **Proceso finalizado con éxito.**",
            duration=duration, width=width, height=height,
            supports_streaming=True,
            progress=progress_bar,
            progress_args=(up_msg, time.time(), "Subiendo Video 📤")
        )
        await up_msg.delete()
        await status_msg.delete()
    else:
        await status_msg.edit("❌ El proceso fue cancelado o hubo un error.")

    # Limpieza
    for p in [v_path, s_path, output]:
        if os.path.exists(p): os.remove(p)
    if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    bot.run()
