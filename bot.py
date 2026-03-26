import os
import asyncio
import time
import re
import shutil
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

# --- BARRA DE PROGRESO (DESCARGA/SUBIDA) ---
async def progress_bar(current, total, status_msg, start_time, action):
    user_id = status_msg.chat.id
    if user_data.get(user_id, {}).get("cancel"):
        raise Exception("STOP_PROCESS")
    
    now = time.time()
    diff = now - start_time
    
    last_update = user_data.get(user_id, {}).get("last_upd", 0)
    if (now - last_update) < 5 and current != total:
        return

    user_data[user_id]["last_upd"] = now
    
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = time.strftime('%H:%M:%S', time.gmtime((total - current) / speed)) if speed > 0 else "00:00:00"
    bar = "▰" * int(percentage / 10) + "▱" * (10 - int(percentage / 10))
    
    msg = (
        f"🚀 **{action}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌀 **Estado:** `{round(percentage, 1)}%` | `|{bar}|`\n"
        f"📦 **Tamaño:** `{humanbytes(current)}` de `{humanbytes(total)}` \n"
        f"⚡ **Velocidad:** `{humanbytes(speed)}/s` \n"
        f"⏳ **Tiempo restante:** `{eta}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
    except: pass

# --- COMANDO STATUS ---
@bot.on_message(filters.command("status"))
async def status_check(client, message):
    status_text = "📊 **ESTADO DEL SISTEMA**\n━━━━━━━━━━━━━━━━━━━━━\n"
    status_text += "🤖 **Bot:** `CONECTADO ✅` \n"
    if premium_client:
        status_text += "🌟 **Premium:** `ACTIVO ✅` \n"
    _, _, free = shutil.disk_usage("/")
    status_text += f"━━━━━━━━━━━━━━━━━━━━━\n💾 **Disco Libre:** `{free // (2**30)} GB`"
    await message.reply(status_text)

def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    p_name = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[data['preset']]
    q_name = {"18": "Alta ⭐", "24": "Buena ✅", "28": "Baja 📉"}[data['crf']]
    out_name = {0: "Ninguno 🚫", 1: "Fino ✨", 2: "Medio 🖼️"}[data['outline']]
    
    text = (
        "🎬 **AJUSTES DE PROCESAMIENTO**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 **Color:** `{c_name}`\n"
        f"🔡 **Fuente:** `{data['font']}`\n"
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
            "preset": "veryfast", "crf": "24", "process": None, "cancel": False,
            "last_upd": 0, "current_speed": "0.0"
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
    dl_client = client
    video_to_download = data["video"]

    try:
        await status_msg.edit("📡 **Sincronizando con Canal Dump...**")
        dump_msg = await data["video"].forward(Config.DUMP_CHAT_ID)
        video_to_download = dump_msg
    except: pass

    if premium_client:
        try:
            if not premium_client.is_connected: await premium_client.start()
            premium_video_msg = await premium_client.get_messages(Config.DUMP_CHAT_ID, dump_msg.id)
            if premium_video_msg:
                video_to_download = premium_video_msg
                dl_client = premium_client
        except: dl_client = client

    try:
        v_path = await dl_client.download_media(
            video_to_download, 
            progress=progress_bar, 
            progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO")
        )
        s_path = await client.download_media(data["subtitle"])
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

    # --- BUCLE DE PROGRESO FFmpeg ---
    while True:
        line = await process.stdout.readline()
        if not line or data["cancel"]: break
        text = line.decode().strip()
        
        time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
        speed_match = re.search(r"speed=\s*(\d+\.?\d*)x", text)

        if speed_match:
            user_data[user_id]["current_speed"] = speed_match.group(1)

        if time_match:
            current_time_str = time_match.group(1)
            curr_sec = time_to_seconds(current_time_str)
            
            # SALIDA FORZADA: Si el tiempo procesado llega al final, rompemos el bucle
            if total_duration > 0 and curr_sec >= (total_duration - 1):
                break

            now = time.time()
            if (now - user_data[user_id]["last_upd"]) >= 5:
                user_data[user_id]["last_upd"] = now
                perc = (curr_sec / total_duration) * 100 if total_duration > 0 else 0
                raw_speed = user_data[user_id].get("current_speed", "0.0")
                f_speed = float(raw_speed)
                
                if f_speed > 0:
                    eta_sec = (total_duration - curr_sec) / f_speed
                    eta_ffmpeg = time.strftime('%H:%M:%S', time.gmtime(max(0, eta_sec)))
                else:
                    eta_ffmpeg = "Calculando..."

                bar = "█" * int(perc / 10) + "░" * (10 - int(perc / 10))
                
                msg = (
                    f"🎬 **PEGANDO SUBTÍTULOS**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 **Progreso:** `{round(perc, 1)}%` | `|{bar}|`\n"
                    f"🕒 **Tiempo video:** `{current_time_str}` / `{time.strftime('%H:%M:%S', time.gmtime(total_duration))}`\n"
                    f"⚡ **Velocidad Real:** `{raw_speed}x` \n"
                    f"⏳ **Restante:** `{eta_ffmpeg}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
                try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="stop_ffmpeg")]]))
                except: pass

    await process.wait()

    # --- SUBIDA FINAL ---
    if os.path.exists(output) and not data["cancel"]:
        # Reciclamos el status_msg para la subida
        await status_msg.edit("📤 **Pegado listo. Iniciando subida...**")
        try:
            duration, width, height = get_video_info(output)
            await dl_client.send_video(
                chat_id=chat_id, video=output, caption="✅ **¡Proceso completado!**",
                duration=duration, width=width, height=height, supports_streaming=True,
                progress=progress_bar, progress_args=(status_msg, time.time(), "SUBIENDO RESULTADO")
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(f"❌ Error subida: {e}")

    try: await dump_msg.delete()
    except: pass
    await clean_up(user_id, v_path, s_path, output)

async def clean_up(user_id, v=None, s=None, o=None):
    for p in [v, s, o]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass
    if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    bot.run()
