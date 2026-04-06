import os
import asyncio
import time
import re
import shutil
import traceback
import codecs
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

# --- INICIALIZACIÓN DE ALTO RENDIMIENTO ---
# Aumentamos workers a 200 y habilitamos múltiples transmisiones concurrentes
bot = Client(
    "HarsubBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN,
    workers=200,
    max_concurrent_transmissions=40  # Permite usar más ancho de banda en paralelo
)

premium_client = None
if hasattr(Config, "STRING_SESSION") and Config.STRING_SESSION:
    premium_client = Client(
        "PremiumUser", 
        api_id=Config.API_ID, 
        api_hash=Config.API_HASH, 
        session_string=Config.STRING_SESSION,
        sleep_threshold=120,
        workers=200,
        max_concurrent_transmissions=40
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

# --- PROGRESO (DESCARGA/SUBIDA) ---
async def progress_bar(current, total, status_msg, start_time, action):
    user_id = status_msg.chat.id
    if user_data.get(user_id, {}).get("cancel"):
        raise Exception("STOP_PROCESS")
    
    now = time.time()
    diff = now - start_time
    last_update = user_data.get(user_id, {}).get("last_upd", 0)
    
    # Actualización cada 4 segundos para evitar spam pero mantener fluidez
    if (now - last_update) < 4 and current != total:
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
        f"📦 **Tamaño:** `{humanbytes(current)}` / `{humanbytes(total)}` \n"
        f"⚡ **Velocidad:** `{humanbytes(speed)}/s` \n"
        f"⏳ **Restante:** `{eta}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
    except: pass

# --- MENÚ DE CONFIGURACIÓN ---
def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    p_name = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[data['preset']]
    q_name = {"20": "Alta ⭐", "24": "Buena ✅", "28": "Baja 📉"}.get(data['crf'], f"{data['crf']}")
    out_name = {0: "Ninguno 🚫", 1: "Fino ✨", 2: "Medio 🖼️"}.get(data['outline'], "Medio 🖼️")
    pos_name = {2: "Centro-Abajo 👇", 1: "Izquierda-Abajo 👈", 3: "Derecha-Abajo 👉"}.get(data['alignment'], "Centro-Abajo 👇")
    
    text = (
        "🎬 **AJUSTES DE PROCESAMIENTO**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 **Color:** `{c_name}`\n"
        f"🔡 **Fuente:** `{data['font']}`\n"
        f"📏 **Tamaño:** `{data['size']}px`\n"
        f"🖋️ **Contorno:** `{out_name}`\n"
        f"📍 **Posición:** `{pos_name}`\n"
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
        [InlineKeyboardButton("👈 Izquierda", callback_data="set_pos_1"),
         InlineKeyboardButton("👇 Centro", callback_data="set_pos_2"),
         InlineKeyboardButton("👉 Derecha", callback_data="set_pos_3")],
        [InlineKeyboardButton("⚡ Rápido", callback_data="set_pre_ultrafast"),
         InlineKeyboardButton("🐢 Lento", callback_data="set_pre_slow")],
        [InlineKeyboardButton("⭐ Alta", callback_data="set_crf_20"),
         InlineKeyboardButton("✅ Buena", callback_data="set_crf_24")],
        [InlineKeyboardButton("🚀 INICIAR NORMAL", callback_data="start_normal")],
        [InlineKeyboardButton("⚖️ MODO INTELIGENTE (< 2GB)", callback_data="start_smart")]
    ])
    return text, markup

# --- COMANDOS ---
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar.")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    file_name = "video_procesado.mp4"
    if message.video and message.video.file_name:
        file_name = message.video.file_name
    elif message.document and message.document.file_name:
        file_name = message.document.file_name

    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        user_data[user_id] = {
            "video": message, 
            "video_name": file_name,
            "subtitle": None, "color": "&HFFFFFF", 
            "size": 24, "outline": 2, "font": "Arial",
            "alignment": 2, "preset": "veryfast", "crf": "24", "process": None, "cancel": False,
            "last_upd": 0, "current_speed": "0.0", "mode": "normal"
        }
        await message.reply(f"✅ Video recibido: `{file_name}`. Ahora envía el archivo **.srt**")
    elif message.document and message.document.file_name and message.document.file_name.endswith(".srt"):
        if user_id not in user_data: return await message.reply("❌ Envía el video primero.")
        user_data[user_id]["subtitle"] = message
        text, markup = get_config_menu(user_id)
        await message.reply(text, reply_markup=markup)

@bot.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    if query.data.startswith("set_"):
        if user_id not in user_data: return await query.answer("❌ Error de datos.", show_alert=True)
        parts = query.data.split("_")
        type_set, val = parts[1], parts[2]
        if type_set == "col": user_data[user_id]["color"] = val
        elif type_set == "fnt": user_data[user_id]["font"] = val
        elif type_set == "pre": user_data[user_id]["preset"] = val
        elif type_set == "crf": user_data[user_id]["crf"] = val
        elif type_set == "out": user_data[user_id]["outline"] = int(val)
        elif type_set == "pos": user_data[user_id]["alignment"] = int(val)
        elif type_set == "siz":
            user_data[user_id]["size"] = min(100, user_data[user_id]["size"] + 2) if val == "up" else max(10, user_data[user_id]["size"] - 2)
        text, markup = get_config_menu(user_id)
        try: await query.message.edit(text, reply_markup=markup)
        except: pass
        await query.answer()

    elif query.data.startswith("start"):
        mode = "smart" if "smart" in query.data else "normal"
        user_data[user_id]["mode"] = mode
        await query.answer(f"🚀 Iniciando modo {mode}...")
        await query.message.edit(f"⏳ Preparando archivos (Modo: {mode.upper()})...")
        await run_engine(client, query.message, user_id)

    elif query.data in ["cancel_all", "stop_ffmpeg"]:
        if user_id in user_data:
            user_data[user_id]["cancel"] = True
            if user_data[user_id]["process"]:
                try:
                    user_data[user_id]["process"].terminate()
                except: pass
            await query.answer("🛑 Proceso detenido", show_alert=True)
            await query.message.edit("❌ **Operación cancelada.**")

# --- MOTOR DE PROCESAMIENTO ---
async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    chat_id = status_msg.chat.id
    
    # Intentar reenviar al canal DUMP para acelerar la descarga vía servidores de Telegram
    video_to_download = data["video"]
    dl_client = client
    
    try:
        dump_msg = await data["video"].forward(Config.DUMP_CHAT_ID)
        if premium_client:
            if not premium_client.is_connected: await premium_client.start()
            premium_video_msg = await premium_client.get_messages(Config.DUMP_CHAT_ID, dump_msg.id)
            if premium_video_msg:
                video_to_download = premium_video_msg
                dl_client = premium_client
    except: pass

    try:
        v_path = await dl_client.download_media(
            video_to_download, 
            file_name=f"downloads/v_{user_id}.mp4",
            progress=progress_bar, 
            progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO")
        )
        s_path = await bot.download_media(data["subtitle"], file_name=f"downloads/s_{user_id}.srt")
    except Exception as e:
        if str(e) == "STOP_PROCESS": return
        await status_msg.edit(f"❌ Error descarga: {e}")
        return await clean_up(user_id)

    total_duration, _, _ = get_video_info(v_path)
    temp_output = f"downloads/temp_{user_id}.mp4"
    style = f"FontName={data['font']},PrimaryColour={data['color']},FontSize={data['size']},Outline={data['outline']},BorderStyle=1,Shadow=0,Alignment={data['alignment']},MarginV=12"
    
    clean_v_path = os.path.abspath(v_path).replace("\\", "/").replace(":", "\\:")
    clean_s_path = os.path.abspath(s_path).replace("\\", "/").replace(":", "\\:")

    base_filter = f"scale='iw*sar':'ih',setsar=1,scale=trunc(iw/2)*2:trunc(ih/2)*2"
    
    # COMANDO FFmpeg OPTIMIZADO: '-threads 0' usa todo el CPU disponible
    if data["mode"] == "smart":
        target_size_bits = 1900 * 1024 * 1024 * 8 
        calculated_bitrate = int((target_size_bits / total_duration) * 0.9)
        v_bitrate = min(calculated_bitrate, 5000000)
        video_filter = f"{base_filter},scale=1280:-2,subtitles='{clean_s_path}':force_style='{style}',format=yuv420p"
        cmd = [
            "ffmpeg", "-threads", "0", "-i", clean_v_path, "-vf", video_filter, 
            "-c:v", "libx264", "-b:v", f"{v_bitrate}", "-maxrate", f"{v_bitrate}", "-bufsize", f"{v_bitrate*2}",
            "-preset", "ultrafast", "-c:a", "copy", "-movflags", "+faststart", 
            "-progress", "pipe:1", temp_output, "-y"
        ]
    else:
        video_filter = f"{base_filter},subtitles='{clean_s_path}':force_style='{style}',format=yuv420p"
        cmd = [
            "ffmpeg", "-threads", "0", "-i", clean_v_path, "-vf", video_filter, 
            "-c:v", "libx264", "-preset", data["preset"], "-crf", data["crf"], 
            "-c:a", "copy", "-movflags", "+faststart", 
            "-progress", "pipe:1", temp_output, "-y"
        ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    user_data[user_id]["process"] = process

    while True:
        line = await process.stdout.readline()
        if not line or data["cancel"]: break
        text = line.decode().strip()
        
        time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
        speed_match = re.search(r"speed=\s*(\d+\.?\d*)x", text)
        
        if speed_match: data["current_speed"] = speed_match.group(1)
        if time_match:
            curr_sec = time_to_seconds(time_match.group(1))
            now = time.time()
            if (now - data["last_upd"]) >= 5:
                data["last_upd"] = now
                perc = (curr_sec / total_duration) * 100 if total_duration > 0 else 0
                raw_speed = data["current_speed"]
                try:
                    f_speed = float(raw_speed) if raw_speed != "0.0" else 0.01
                    eta_sec = (total_duration - curr_sec) / f_speed
                    eta = time.strftime('%H:%M:%S', time.gmtime(max(0, eta_sec)))
                except: eta = "00:00:00"
                
                bar = "▰" * int(perc / 10) + "▱" * (10 - int(perc / 10))
                status_text = (
                    f"🎬 **PEGANDO SUBTÍTULOS ({data['mode'].upper()})**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 **Progreso:** `{round(perc, 1)}%` | `|{bar}|` \n"
                    f"⚡ **Velocidad:** `{raw_speed}x` \n"
                    f"⏳ **Restante:** `{eta}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
                try: await status_msg.edit(status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
                except: pass

    await process.wait()
    
    if data["cancel"]: return await clean_up(user_id, v_path, s_path, temp_output)

    if os.path.exists(temp_output):
        final_output = f"downloads/{data['video_name']}"
        if os.path.exists(final_output): os.remove(final_output)
        os.rename(temp_output, final_output)
        file_size = os.path.getsize(final_output)
        
        up_client = premium_client if (file_size > 2000*1024*1024 and premium_client) else bot
        
        try:
            d, width, height = get_video_info(final_output)
            await up_client.send_video(
                chat_id=chat_id, video=final_output, 
                caption=f"✅ **¡Completado!**\n⚖️ **Peso:** `{humanbytes(file_size)}`",
                duration=d, width=width, height=height, supports_streaming=True,
                progress=progress_bar, progress_args=(status_msg, time.time(), "SUBIENDO RESULTADO")
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(f"❌ Error subida: {e}")
            
        await clean_up(user_id, v_path, s_path, final_output)

async def clean_up(user_id, v=None, s=None, o=None):
    for p in [v, s, o]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass
    if user_id in user_data: 
        user_data[user_id]["process"] = None
        user_data[user_id]["cancel"] = False

if __name__ == "__main__":
    bot.run()
