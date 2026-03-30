import os
import asyncio
import time
import re
import shutil
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from config import Config

# --- LIMPIEZA AUTOMÁTICA AL INICIAR ---
def clear_downloads():
    folder = "downloads"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except: pass
    else:
        os.makedirs(folder)

clear_downloads()

# Inicialización
bot = Client(
    "HarsubBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN,
    workers=50
)

premium_client = None
if hasattr(Config, "STRING_SESSION") and Config.STRING_SESSION:
    premium_client = Client(
        "PremiumUser", 
        api_id=Config.API_ID, 
        api_hash=Config.API_HASH, 
        session_string=Config.STRING_SESSION,
        sleep_threshold=60 
    )

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
    try:
        parts = time_str.split(':')
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except: return 0

def humanbytes(size):
    if not size: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024

# --- BARRA DE PROGRESO ---
async def progress_bar(current, total, status_msg, start_time, action):
    user_id = status_msg.chat.id
    if user_data.get(user_id, {}).get("cancel"):
        raise Exception("STOP_PROCESS")
    
    now = time.time()
    diff = now - start_time
    last_update = user_data.get(user_id, {}).get("last_upd", 0)
    if (now - last_update) < 5 and current != total: return

    user_data[user_id]["last_upd"] = now
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = time.strftime('%H:%M:%S', time.gmtime((total - current) / speed)) if speed > 0 else "00:00:00"
    bar = "▰" * int(percentage / 10) + "▱" * (10 - int(percentage / 10))
    
    msg = (f"🚀 **{action}**\n━━━━━━━━━━━━━━━━━━━━━\n"
           f"🌀 **Estado:** `{round(percentage, 1)}%` | `|{bar}|`\n"
           f"📦 **Tamaño:** `{humanbytes(current)}` de `{humanbytes(total)}` \n"
           f"⚡ **Velocidad:** `{humanbytes(speed)}/s` | ⏳ **ETA:** `{eta}`\n━━━━━━━━━━━━━━━━━━━━━")
    try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
    except: pass

# --- MENÚ DE CONFIGURACIÓN ---
def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    p_name = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[data['preset']]
    res_display = "Original 📺" if data['res'] == "original" else f"{data['res']}p"
    
    text = (
        "🎬 **AJUSTES DE PROCESAMIENTO**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 **Color:** `{c_name}` | 📏 **Resolución:** `{res_display}`\n"
        f"🔡 **Fuente:** `{data['font']}` ({data['size']}px)\n"
        f"🚀 **Velocidad:** `{p_name}` | 🎯 **CRF:** `{data['crf']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Amarillo", callback_data="set_col_&H00FFFF"),
         InlineKeyboardButton("⚪ Blanco", callback_data="set_col_&HFFFFFF")],
        [InlineKeyboardButton("📏 480p", callback_data="set_res_480"),
         InlineKeyboardButton("📏 720p", callback_data="set_res_720"),
         InlineKeyboardButton("📏 1080p", callback_data="set_res_1080")],
        [InlineKeyboardButton("📺 Original", callback_data="set_res_original")],
        [InlineKeyboardButton("➕ Tamaño", callback_data="set_siz_up"),
         InlineKeyboardButton("➖ Tamaño", callback_data="set_siz_down")],
        [InlineKeyboardButton("⚡ Rápido", callback_data="set_pre_ultrafast"),
         InlineKeyboardButton("🐢 Lento", callback_data="set_pre_slow")],
        [InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]
    ])
    return text, markup

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar.")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        user_data[user_id] = {
            "video": message, "subtitle": None, "color": "&HFFFFFF", "res": "720",
            "size": 24, "outline": 2, "font": "Arial", "preset": "veryfast", "crf": "24",
            "process": None, "cancel": False, "last_upd": 0, "current_speed": "0.0"
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
        parts = query.data.split("_")
        type_set, val = parts[1], parts[2]
        if type_set == "col": user_data[user_id]["color"] = val
        elif type_set == "res": user_data[user_id]["res"] = val
        elif type_set == "pre": user_data[user_id]["preset"] = val
        elif type_set == "siz":
            user_data[user_id]["size"] = user_data[user_id]["size"] + 2 if val == "up" else max(12, user_data[user_id]["size"] - 2)
        text, markup = get_config_menu(user_id)
        try: await query.message.edit(text, reply_markup=markup)
        except: pass
    elif query.data == "start":
        await run_engine(client, query.message, user_id)
    elif query.data == "cancel_all":
        if user_id in user_data:
            user_data[user_id]["cancel"] = True
            if user_data[user_id]["process"]:
                try: user_data[user_id]["process"].terminate()
                except: pass
            await query.message.edit("❌ **Operación cancelada.**")

# --- MOTOR DE PROCESAMIENTO ---
async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    chat_id = status_msg.chat.id
    dl_client = client

    try:
        await status_msg.edit("📥 **Descargando archivos...**")
        v_path = await dl_client.download_media(data["video"], file_name=f"downloads/v_{user_id}.mp4", progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO"))
        s_path = await client.download_media(data["subtitle"], file_name=f"downloads/s_{user_id}.srt")
    except Exception as e:
        return await status_msg.edit(f"❌ Error descarga: {e}")

    await status_msg.edit("🎬 **Iniciando Hardsub (Aspecto Inteligente)...**")
    total_duration, _, _ = get_video_info(v_path)
    output = f"downloads/final_{user_id}.mp4"
    
    style = f"FontName={data['font']},PrimaryColour={data['color']},FontSize={data['size']},Outline={data['outline']},BorderStyle=1,Shadow=0,Alignment=2,MarginV=25"
    clean_s = os.path.abspath(s_path).replace("\\", "/").replace(":", "\\:")

    # MEJORA DEFINITIVA: 
    # scale=-2:res mantiene proporción original. setsar=1 elimina deformación.
    if data['res'] == "original":
        v_filter = f"setsar=1,subtitles='{clean_s}':force_style='{style}',format=yuv420p"
    else:
        v_filter = f"scale=-2:{data['res']}:flags=lanczos,setsar=1,subtitles='{clean_s}':force_style='{style}',format=yuv420p"

    cmd = [
        "ffmpeg", "-y", "-i", v_path, "-vf", v_filter,
        "-c:v", "libx264", "-preset", data["preset"], "-crf", data["crf"],
        "-c:a", "copy", "-movflags", "+faststart", "-progress", "pipe:1", output
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    user_data[user_id]["process"] = process

    while True:
        line = await process.stdout.readline()
        if not line or data["cancel"]: break
        text = line.decode().strip()
        if "out_time=" in text:
            time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
            if time_match:
                curr_sec = time_to_seconds(time_match.group(1))
                perc = (curr_sec / total_duration) * 100 if total_duration > 0 else 0
                bar = "█" * int(perc / 10) + "░" * (10 - int(perc / 10))
                try: await status_msg.edit(f"🎬 **PEGANDO SUBTÍTULOS**\n━━━━━━━━━━━━━━━━━━━━━\n📊 `{round(perc, 1)}%` |`|{bar}|`|\n⏳ **Restante:** `{time.strftime('%M:%S', time.gmtime(total_duration - curr_sec))}`\n━━━━━━━━━━━━━━━━━━━━━")
                except: pass

    await process.wait()

    if os.path.exists(output) and not data["cancel"]:
        await status_msg.edit("📤 **Subiendo video final...**")
        dur, w, h = get_video_info(output)
        await client.send_video(
            chat_id=chat_id, video=output, caption="✅ **¡Harsub Completado!**\nAspecto original respetado.",
            duration=dur, width=w, height=h, supports_streaming=True,
            progress=progress_bar, progress_args=(status_msg, time.time(), "SUBIENDO")
        )
        await status_msg.delete()

    # Limpieza final
    for p in [v_path, s_path, output]:
        if p and os.path.exists(p): os.remove(p)
    if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    bot.run()
