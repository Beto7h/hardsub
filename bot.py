import os
import asyncio
import time
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from config import Config

# Inicialización con optimización de velocidad
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
        sleep_threshold=60 # Mejora para evitar desconexiones en archivos grandes
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

# --- MENÚ DE CONFIGURACIÓN ---
def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    p_name = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[data['preset']]
    q_name = {"18": "Alta ⭐", "24": "Buena ✅", "28": "Baja 📉"}[data['crf']] # CRF 24 es mejor que 22 para peso
    out_name = {0: "Ninguno 🚫", 1: "Fino ✨", 2: "Medio 🖼️"}[data['outline']]

    text = (
        "🎬 **AJUSTES DE PROCESAMIENTO**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 **Color:** `{c_name}`\n"
        f"📏 **Tamaño:** `{data['size']}px`\n"
        f"🖋️ **Contorno:** `{out_name}`\n"
        f"🚀 **Velocidad:** `{p_name}`\n"
        f"🎯 **Calidad:** `{q_name}`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Ajusta los parámetros antes de iniciar:"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Amarillo", callback_data="set_col_&H00FFFF"),
         InlineKeyboardButton("⚪ Blanco", callback_data="set_col_&HFFFFFF")],
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

# --- BARRA DE PROGRESO PROFESIONAL ---
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
        cur_mb = current / 1024 / 1024
        tot_mb = total / 1024 / 1024
        spd_mb = speed / 1024 / 1024

        msg = (
            f"◈ **{action}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Progreso:** `{round(percentage, 1)}%`\n"
            f"✨ **Estado:** `|{bar}|`\n"
            f"📁 **Datos:** `{round(cur_mb, 1)}` / `{round(tot_mb, 1)} MB`\n"
            f"⚡ **Velocidad:** `{round(spd_mb, 2)} MB/s` \n"
            f"⏳ **Restante:** `{eta}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            await status_msg.edit(
                msg, 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]])
            )
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
            "size": 24, "italic": "0", "outline": 2, 
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
        _, type_set, val = query.data.split("_")
        if type_set == "col": user_data[user_id]["color"] = val
        elif type_set == "pre": user_data[user_id]["preset"] = val
        elif type_set == "crf": user_data[user_id]["crf"] = val
        elif type_set == "out": user_data[user_id]["outline"] = int(val)
        elif type_set == "siz":
            if val == "up": user_data[user_id]["size"] += 2
            else: user_data[user_id]["size"] = max(12, user_data[user_id]["size"] - 2)
        
        text, markup = get_config_menu(user_id)
        try: await query.message.edit(text, reply_markup=markup)
        except: pass

    elif query.data == "start":
        await query.message.edit("⏳ Iniciando motores...")
        await run_engine(client, query.message, user_id)

    elif query.data in ["cancel_all", "stop_ffmpeg"]:
        if user_id in user_data:
            user_data[user_id]["cancel"] = True
            if user_data[user_id]["process"]:
                try: user_data[user_id]["process"].terminate()
                except: pass
            await query.answer("🛑 Deteniendo proceso...", show_alert=True)
            await query.message.edit("❌ **Operación cancelada por el usuario.**")

async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    
    # Iniciar cliente premium si existe
    uploader = client
    if premium_client:
        if not premium_client.is_connected:
            try: await premium_client.start()
            except: pass
        uploader = premium_client

    dl_client = uploader if premium_client else client

    try:
        v_path = await dl_client.download_media(data["video"], progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO"))
        if data["cancel"]: raise Exception("Cancel")
        
        s_path = await client.download_media(data["subtitle"], progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO SUBTÍTULOS"))
        if data["cancel"]: raise Exception("Cancel")
    except Exception as e:
        if str(e) != "STOP_PROCESS":
            await status_msg.edit(f"❌ Error: {e}")
        return await clean_up(user_id)

    total_duration, w, h = get_video_info(v_path)
    output = f"{v_path}_harsub.mp4"
    style = f"PrimaryColour={data['color']},FontSize={data['size']},Italic={data['italic']},BorderStyle=1,Outline={data['outline']},Shadow=0"

    # FFmpeg optimizado: CRF 24 para balance peso/calidad y threads 0 para velocidad
    cmd = [
        "ffmpeg", "-i", v_path,
        "-vf", f"subtitles={s_path}:force_style='{style}'",
        "-c:v", "libx264", "-preset", data["preset"], "-crf", data["crf"], "-c:a", "copy",
        "-threads", "0", "-movflags", "faststart", "-progress", "pipe:1", output, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    user_data[user_id]["process"] = process
    
    start_time = time.time()
    last_update = 0

    while True:
        line = await process.stdout.readline()
        if not line or data["cancel"]: break
        text = line.decode().strip()
        if "out_time=" in text:
            time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
            if time_match and total_duration > 0:
                curr_time = time_match.group(1)
                curr_sec = time_to_seconds(curr_time)
                if time.time() - last_update > 5:
                    perc = (curr_sec / total_duration) * 100
                    bar = "█" * int(perc / 10) + "░" * (10 - int(perc / 10))
                    msg = (
                        "◈ **PEGANDO SUBTÍTULOS**\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎬 **Progreso:** `{round(perc, 1)}%`\n"
                        f"✨ **Estado:** `|{bar}|`\n"
                        f"⏱️ **Tiempo:** `{curr_time}` / `{time.strftime('%H:%M:%S', time.gmtime(total_duration))}`\n"
                        "━━━━━━━━━━━━━━━━━━━━━"
                    )
                    try:
                        await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="stop_ffmpeg")]]))
                        last_update = time.time()
                    except: pass

    await process.wait()

    if os.path.exists(output) and not data["cancel"] and process.returncode == 0:
        duration, width, height = get_video_info(output)
        
        # MEJORA FINAL: El uploader envía su propio mensaje para que la barra de >2GB funcione
        up_msg = await uploader.send_message(status_msg.chat.id, "📤 **Subiendo video final (Soporte Premium)...**")
        
        try:
            await uploader.send_video(
                chat_id=status_msg.chat.id, 
                video=output, 
                caption="✅ **¡Proceso completado!**",
                duration=duration, width=width, height=height, supports_streaming=True,
                progress=progress_bar, 
                progress_args=(up_msg, time.time(), "SUBIENDO RESULTADO")
            )
            await up_msg.delete()
            await status_msg.delete()
        except Exception as e:
            await up_msg.edit(f"❌ Error en subida: {e}")
    else:
        if not data["cancel"]:
            await status_msg.edit("❌ Error en el procesamiento de FFmpeg.")

    await clean_up(user_id, v_path, s_path, output)

async def clean_up(user_id, v=None, s=None, o=None):
    for p in [v, s, o]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass
    if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    bot.run()
