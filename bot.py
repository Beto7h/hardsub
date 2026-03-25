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

def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    p_name = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[data['preset']]
    q_name = {"18": "Alta ⭐", "24": "Buena ✅", "28": "Baja 📉"}[data['crf']]
    out_name = {0: "Ninguno 🚫", 1: "Fino ✨", 2: "Medio 🖼️"}[data['outline']]
    f_name = data['font']

    text = (
        "🎬 **AJUSTES DE PROCESAMIENTO**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 **Color:** `{c_name}`\n"
        f"🔡 **Fuente:** `{f_name}`\n"
        f"📏 **Tamaño:** `{data['size']}px`\n"
        f"🖋️ **Contorno:** `{out_name}`\n"
        f"🚀 **Velocidad:** `{p_name}`\n"
        f"🎯 **Calidad:** `{q_name}`\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Amarillo", callback_data="set_col_&H00FFFF"),
         InlineKeyboardButton("⚪ Blanco", callback_data="set_col_&HFFFFFF")],
        [InlineKeyboardButton("🔡 Arial", callback_data="set_fnt_Arial"),
         InlineKeyboardButton("🔡 Impact", callback_data="set_fnt_Impact"),
         InlineKeyboardButton("🔡 Verdana", callback_data="set_fnt_Verdana")],
        [InlineKeyboardButton("➖ Tamaño", callback_data="set_siz_down"),
         InlineKeyboardButton("➕ Tamaño", callback_data="set_siz_up")],
        [InlineKeyboardButton("🚫 Sin Contorno", callback_data="set_out_0"),
         InlineKeyboardButton("✨ Fino", callback_data="set_out_1"),
         InlineKeyboardButton("🖼️ Medio", callback_data="set_out_2")],
        [InlineKeyboardButton("⚡ Rápido", callback_data="set_pre_ultrafast"),
         InlineKeyboardButton("🐢 Lento", callback_data="set_pre_slow")],
        [InlineKeyboardButton("⭐ Alta", callback_data="set_crf_18"),
         InlineKeyboardButton("✅ Buena", callback_data="set_crf_24")],
        [InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]
    ])
    return text, markup

async def progress_bar(current, total, status_msg, start_time, action):
    user_id = status_msg.chat.id
    if user_data.get(user_id, {}).get("cancel"):
        raise Exception("STOP_PROCESS")
    now = time.time()
    diff = now - start_time
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = time.strftime('%M:%S', time.gmtime((total - current) / speed)) if speed > 0 else "00:00"
        bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
        msg = (
            f"◈ **{action}**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Progreso:** `{round(percentage, 1)}%` | `|{bar}|`\n"
            f"⚡ **Velocidad:** `{round(speed / 1024 / 1024, 2)} MB/s` \n"
            f"⏳ **Restante:** `{eta}`"
        )
        try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
        except: pass

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar.")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        user_data[user_id] = {
            "video": message, "subtitle": None, "color": "&HFFFFFF", 
            "size": 24, "italic": "0", "outline": 2, "font": "Arial",
            "preset": "veryfast", "crf": "24", "process": None, "cancel": False
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
        elif type_set == "fnt": user_data[user_id]["font"] = val
        elif type_set == "pre": user_data[user_id]["preset"] = val
        elif type_set == "crf": user_data[user_id]["crf"] = val
        elif type_set == "out": user_data[user_id]["outline"] = int(val)
        elif type_set == "siz":
            user_data[user_id]["size"] = user_data[user_id]["size"] + 2 if val == "up" else max(12, user_data[user_id]["size"] - 2)
        text, markup = get_config_menu(user_id)
        try: await query.message.edit(text, reply_markup=markup)
        except: pass
    elif query.data == "start":
        await query.message.edit("⏳ Preparando sesión...")
        await run_engine(client, query.message, user_id)
    elif query.data in ["cancel_all", "stop_ffmpeg"]:
        if user_id in user_data:
            user_data[user_id]["cancel"] = True
            if user_data[user_id]["process"]:
                try: user_data[user_id]["process"].terminate()
                except: pass
            await query.message.edit("❌ **Operación cancelada.**")

async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    chat_id = status_msg.chat.id
    
    # Manejo robusto de la sesión Premium
    dl_client = client
    if premium_client:
        try:
            if not premium_client.is_connected:
                await premium_client.start()
            # Forzamos reconocimiento del chat
            await premium_client.get_chat(chat_id)
            dl_client = premium_client
        except Exception as e:
            print(f"Sesión Premium no disponible para este chat: {e}")
            dl_client = client

    try:
        v_path = await dl_client.download_media(data["video"], progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO"))
        s_path = await client.download_media(data["subtitle"], progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO SUBTÍTULOS"))
    except Exception as e:
        await status_msg.edit(f"❌ Error descarga: {e}")
        return await clean_up(user_id)

    total_duration, w, h = get_video_info(v_path)
    output = f"{v_path}_harsub.mp4"
    style = f"FontName={data['font']},PrimaryColour={data['color']},FontSize={data['size']},Outline={data['outline']},BorderStyle=1,Shadow=0"

    cmd = [
        "ffmpeg", "-i", v_path, "-vf", f"subtitles={s_path}:force_style='{style}'",
        "-c:v", "libx264", "-preset", data["preset"], "-crf", data["crf"], "-c:a", "copy",
        "-threads", "0", "-movflags", "faststart", "-progress", "pipe:1", output, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    user_data[user_id]["process"] = process
    
    while True:
        line = await process.stdout.readline()
        if not line or data["cancel"]: break
        text = line.decode().strip()
        if "out_time=" in text:
            time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
            if time_match and total_duration > 0:
                curr_sec = time_to_seconds(time_match.group(1))
                perc = (curr_sec / total_duration) * 100
                bar = "█" * int(perc / 10) + "░" * (10 - int(perc / 10))
                try: await status_msg.edit(f"◈ **PEGANDO SUBTÍTULOS**\n━━━━━━━━━━━━\n🎬 `{round(perc, 1)}%` | `|{bar}|`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="stop_ffmpeg")]]))
                except: pass

    await process.wait()

    if os.path.exists(output) and not data["cancel"]:
        # Subida con el cliente que tenga la sesión (Premium si funcionó, sino el Bot)
        up_msg = await dl_client.send_message(chat_id, "📤 **Subiendo video final...**")
        try:
            duration, width, height = get_video_info(output)
            await dl_client.send_video(
                chat_id=chat_id, video=output, caption="✅ **¡Proceso completado!**",
                duration=duration, width=width, height=height, supports_streaming=True,
                progress=progress_bar, progress_args=(up_msg, time.time(), "SUBIENDO RESULTADO")
            )
            await up_msg.delete()
            await status_msg.delete()
        except Exception as e:
            await up_msg.edit(f"❌ Error subida: {e}")

    await clean_up(user_id, v_path, s_path, output)

async def clean_up(user_id, v=None, s=None, o=None):
    for p in [v, s, o]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass
    if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    bot.run()
