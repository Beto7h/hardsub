import os
import asyncio
import time
import re
import shutil
import signal
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

# --- INICIALIZACIÓN ---
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

# --- PROGRESO OPTIMIZADO CON CANCELACIÓN ---
async def progress_bar(current, total, status_msg, start_time, action):
    user_id = status_msg.chat.id
    if user_data.get(user_id, {}).get("cancel"):
        raise Exception("STOP_PROCESS")
    
    now = time.time()
    last_update = user_data.get(user_id, {}).get("last_upd", 0)
    if (now - last_update) < 4 and current != total:
        return

    user_data[user_id]["last_upd"] = now
    diff = now - start_time
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
        f"⏳ **Restante:** `{eta}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    try: 
        await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
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
        [InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]
    ])
    return text, markup

# --- COMANDOS ---
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar.")

@bot.on_message(filters.command("check"))
async def check_status(client, message):
    status_text = "📊 **VERIFICACIÓN DEL SISTEMA**\n━━━━━━━━━━━━━━━━━━━━━\n"
    status_text += "🤖 **Bot:** `ACTIVO ✅` \n"
    if premium_client:
        try:
            if not premium_client.is_connected: await premium_client.start()
            me = await premium_client.get_me()
            status_text += f"🌟 **Premium:** `ACTIVO ✅` (@{me.username})\n"
        except: status_text += "🌟 **Premium:** `ERROR ❌` \n"
    else: status_text += "🌟 **Premium:** `NO CONFIGURADO ⚠️` \n"
    
    try:
        chat = await client.get_chat(Config.DUMP_CHAT_ID)
        status_text += f"📂 **Canal Dump:** `OK ✅` ({chat.title})\n"
    except: status_text += "📂 **Canal Dump:** `ERROR ❌` \n"
        
    status_text += "━━━━━━━━━━━━━━━━━━━━━"
    await message.reply(status_text)

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        user_data[user_id] = {
            "video": message, "subtitle": None, "color": "&HFFFFFF", 
            "size": 24, "outline": 2, "font": "Arial",
            "alignment": 2, "preset": "veryfast", "crf": "24", 
            "process": None, "cancel": False, "last_upd": 0
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

    elif query.data == "start":
        await query.answer("🚀 Iniciando...")
        await run_engine(client, query.message, user_id)

    elif query.data == "cancel_all":
        if user_id in user_data:
            user_data[user_id]["cancel"] = True
            process = user_data[user_id].get("process")
            if process:
                try:
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.returncode is None: process.kill()
                except: pass
            await query.answer("🛑 PROCESO CANCELADO", show_alert=True)
            await query.message.edit("❌ **Operación cancelada.**")
            await clean_up(user_id)

# --- MOTOR DE PROCESAMIENTO ---
async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    chat_id = status_msg.chat.id
    v_path, s_path, output = None, None, None

    try:
        # Descargas con protección de cancelación
        v_path = await client.download_media(data["video"], file_name=f"downloads/v_{user_id}.mp4",
                                            progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO"))
        s_path = await client.download_media(data["subtitle"], file_name=f"downloads/s_{user_id}.srt")
        
        if data.get("cancel"): raise Exception("STOP_PROCESS")

        await status_msg.edit("🎬 **PEGANDO SUBTÍTULOS...**")
        
        total_duration, _, _ = get_video_info(v_path)
        output = f"downloads/final_{user_id}.mp4"
        
        # Estilo ASS y Filtro que evita el estiramiento (setsar=1)
        style = f"FontName={data['font']},PrimaryColour={data['color']},FontSize={data['size']},Outline={data['outline']},BorderStyle=1,Shadow=0,Alignment={data['alignment']},MarginV=25"
        clean_s_path = os.path.abspath(s_path).replace("\\", "/").replace(":", "\\:")
        video_filter = f"setsar=1,scale=trunc(iw/2)*2:trunc(ih/2)*2,subtitles='{clean_s_path}':force_style='{style}',format=yuv420p"

        cmd = [
            "ffmpeg", "-i", v_path, "-vf", video_filter,
            "-c:v", "libx264", "-preset", data["preset"], "-crf", data["crf"],
            "-c:a", "copy", "-movflags", "+faststart", "-progress", "pipe:1", output, "-y"
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        user_data[user_id]["process"] = process

        while True:
            line = await process.stdout.readline()
            if not line or data.get("cancel"): break
            
            text = line.decode().strip()
            time_match = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
            if time_match:
                curr_sec = time_to_seconds(time_match.group(1))
                if (time.time() - user_data[user_id]["last_upd"]) > 4:
                    user_data[user_id]["last_upd"] = time.time()
                    perc = (curr_sec / total_duration) * 100 if total_duration > 0 else 0
                    bar = "▰" * int(perc / 10) + "▱" * (10 - int(perc / 10))
                    try: 
                        await status_msg.edit(f"🎬 **PROCESANDO...**\n━━━━━━━━━━━━━━━━━━━━━\n📊 `{round(perc,1)}%` | `|{bar}|`",
                                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
                    except: pass

        await process.wait()
        if data.get("cancel"): raise Exception("STOP_PROCESS")

        await status_msg.edit("📤 **SUBIENDO VIDEO...**")
        d, w, h = get_video_info(output)
        await client.send_video(chat_id, video=output, caption="✅ ¡Listo!", duration=d, width=w, height=h, 
                                progress=progress_bar, progress_args=(status_msg, time.time(), "SUBIENDO"))
        await status_msg.delete()

    except Exception as e:
        if str(e) != "STOP_PROCESS":
            await status_msg.edit(f"❌ **Error:** `{e}`")
    finally:
        await clean_up(user_id, v_path, s_path, output)

async def clean_up(user_id, v=None, s=None, o=None):
    paths = [v, s, o] if v else [f"downloads/v_{user_id}.mp4", f"downloads/s_{user_id}.srt", f"downloads/final_{user_id}.mp4"]
    for p in paths:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass
    if user_id in user_data:
        user_data[user_id]["process"] = None
        user_data[user_id]["cancel"] = False

if __name__ == "__main__":
    bot.run()
