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

# --- CONFIGURACIÓN ---
DUMP_ID = -1003878976804 

def clear_downloads():
    folder = "downloads"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except: pass
    else: os.makedirs(folder)

clear_downloads()

# --- INICIALIZACIÓN ---
bot = Client("HarsubBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN, workers=50)

premium_client = None
if hasattr(Config, "STRING_SESSION") and Config.STRING_SESSION:
    premium_client = Client("PremiumUser", api_id=Config.API_ID, api_hash=Config.API_HASH, session_string=Config.STRING_SESSION, sleep_threshold=60)

user_data = {}

# --- UTILIDADES ---
def get_video_info(file_path):
    try:
        metadata = extractMetadata(createParser(file_path))
        if not metadata: return 0, 0, 0
        return (metadata.get("duration").seconds, metadata.get("width"), metadata.get("height"))
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

# --- PROGRESO ---
async def progress_bar(current, total, status_msg, start_time, action):
    uid = status_msg.chat.id
    if user_data.get(uid, {}).get("cancel"): raise Exception("STOP_PROCESS")
    now = time.time()
    diff = now - start_time
    if (now - user_data[uid].get("last_upd", 0)) < 5 and current != total: return
    user_data[uid]["last_upd"] = now
    perc = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = time.strftime('%H:%M:%S', time.gmtime((total - current) / speed)) if speed > 0 else "00:00:00"
    bar = "▰" * int(perc / 10) + "▱" * (10 - int(perc / 10))
    msg = (f"🚀 **{action}**\n━━━━━━━━━━━━━━━━━━━━━\n"
           f"🌀 **Progreso:** `{round(perc, 1)}%` | `|{bar}|`\n"
           f"⚡ **Velocidad:** `{humanbytes(speed)}/s` | ⏳ **ETA:** `{eta}`\n━━━━━━━━━━━━━━━━━━━━━")
    try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
    except: pass

# --- MENÚ COMPLETO ---
def get_config_menu(uid):
    d = user_data[uid]
    res_txt = "Original 📺" if d['res'] == "original" else f"{d['res']}p"
    p_txt = {"ultrafast": "Rápido ⚡", "veryfast": "Medio 🏃", "slow": "Lento 🐢"}[d['preset']]
    q_txt = {"20": "Alta ⭐", "24": "Buena ✅", "28": "Baja 📉"}[d['crf']]
    
    text = (f"🎬 **AJUSTES DE PROCESAMIENTO**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔡 **Fuente:** `{d['font']}` | 📏 **Tamaño:** `{d['size']}px`\n"
            f"🎨 **Color:** `{d['color']}` | 📺 **Res:** `{res_txt}`\n"
            f"🚀 **Compresión:** `{p_txt}` | 🎯 **Calidad:** `{q_txt}`\n━━━━━━━━━━━━━━━━━━━━━")
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Amarillo", callback_data="set_col_&H00FFFF"), InlineKeyboardButton("⚪ Blanco", callback_data="set_col_&HFFFFFF")],
        [InlineKeyboardButton("🔡 Arial", callback_data="set_fnt_Arial"), InlineKeyboardButton("🔡 Impact", callback_data="set_fnt_Impact"), InlineKeyboardButton("🔡 Verdana", callback_data="set_fnt_Verdana")],
        [InlineKeyboardButton("➖ Tamaño", callback_data="set_siz_down"), InlineKeyboardButton("➕ Tamaño", callback_data="set_siz_up")],
        [InlineKeyboardButton("📏 480p", callback_data="set_res_480"), InlineKeyboardButton("📏 720p", callback_data="set_res_720"), InlineKeyboardButton("📏 1080p", callback_data="set_res_1080")],
        [InlineKeyboardButton("⚡ Rápido", callback_data="set_pre_ultrafast"), InlineKeyboardButton("🐢 Lento", callback_data="set_pre_slow")],
        [InlineKeyboardButton("⭐ Calidad Alta", callback_data="set_crf_20"), InlineKeyboardButton("📉 Calidad Baja", callback_data="set_crf_28")],
        [InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]
    ])
    return text, markup

@bot.on_message(filters.command("check_premium"))
async def check_premium(client, message):
    msg = await message.reply("🔍 **Verificando Sesión...**")
    if not premium_client: return await msg.edit("❌ Sin Sesión String.")
    try:
        if not premium_client.is_connected: await premium_client.start()
        me = await premium_client.get_me()
        chat = await premium_client.get_chat(DUMP_ID)
        await msg.edit(f"✅ **Premium OK**\n👤: `{me.first_name}`\n📡 Canal Dump: `{chat.title}`")
    except Exception as e: await msg.edit(f"❌ Error: {e}")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    uid = message.from_user.id
    if message.video or (message.document and message.document.mime_type and "video" in message.document.mime_type):
        user_data[uid] = {"video": message, "subtitle": None, "color": "&HFFFFFF", "res": "720", "size": 24, "font": "Arial", "preset": "veryfast", "crf": "24", "cancel": False, "last_upd": 0}
        await message.reply("✅ Video recibido. Envía el **.srt**")
    elif message.document and message.document.file_name.endswith(".srt"):
        if uid not in user_data: return
        user_data[uid]["subtitle"] = message
        t, m = get_config_menu(uid)
        await message.reply(t, reply_markup=m)

@bot.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    uid = query.from_user.id
    if query.data.startswith("set_"):
        _, type_set, val = query.data.split("_")
        if type_set == "siz":
            user_data[uid]["size"] = user_data[uid]["size"] + 2 if val == "up" else max(12, user_data[uid]["size"] - 2)
        else:
            user_data[uid][type_set] = val
        t, m = get_config_menu(uid)
        try: await query.message.edit(t, reply_markup=m)
        except: pass
    elif query.data == "start": await run_engine(client, query.message, uid)
    elif query.data == "cancel_all":
        user_data[uid]["cancel"] = True
        if user_data[uid].get("process"):
            try: user_data[uid]["process"].terminate()
            except: pass
        await query.message.edit("❌ **Cancelado.**")

# --- MOTOR PRINCIPAL ---
async def run_engine(client, status_msg, uid):
    data = user_data[uid]
    v_path, s_path, out = None, None, None
    try:
        await status_msg.edit("📡 **Sincronizando con Canal...**")
        dump_msg = await data["video"].forward(DUMP_ID)
        
        dl_client = client
        target = dump_msg
        if premium_client:
            if not premium_client.is_connected: await premium_client.start()
            target = await premium_client.get_messages(DUMP_ID, dump_msg.id)
            dl_client = premium_client

        v_path = await dl_client.download_media(target, file_name=f"downloads/v_{uid}.mp4", progress=progress_bar, progress_args=(status_msg, time.time(), "DESCARGANDO VIDEO"))
        s_path = await client.download_media(data["subtitle"], file_name=f"downloads/s_{uid}.srt")

        await status_msg.edit("🎬 **Iniciando Compresión...**")
        dur, _, _ = get_video_info(v_path)
        out = f"downloads/f_{uid}.mp4"
        style = f"FontName={data['font']},PrimaryColour={data['color']},FontSize={data['size']},Alignment=2,MarginV=25,Outline=2,BorderStyle=1"
        clean_s = os.path.abspath(s_path).replace("\\", "/").replace(":", "\\:")
        
        v_filter = f"setsar=1,subtitles='{clean_s}':force_style='{style}',format=yuv420p"
        if data['res'] != "original": v_filter = f"scale=-2:{data['res']}:flags=lanczos," + v_filter

        cmd = ["ffmpeg", "-y", "-i", v_path, "-vf", v_filter, "-c:v", "libx264", "-crf", data["crf"], "-preset", data["preset"], "-c:a", "copy", "-movflags", "+faststart", "-progress", "pipe:1", out]
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        user_data[uid]["process"] = process

        while True:
            line = await process.stdout.readline()
            if not line or data["cancel"]: break
            text = line.decode().strip()
            if "out_time=" in text:
                t_m = re.search(r"out_time=(\d{2}:\d{2}:\d{2})", text)
                s_m = re.search(r"speed=\s*(\d+\.?\d*)x", text)
                if t_m and s_m:
                    curr = time_to_seconds(t_m.group(1))
                    perc = (curr / dur) * 100 if dur > 0 else 0
                    bar = "█" * int(perc / 10) + "░" * (10 - int(perc / 10))
                    try: await status_msg.edit(f"🎬 **COMPRIMIENDO**\n📊 `{round(perc,1)}%` |`|{bar}|`|\n⚡ Vel: `{s_m.group(1)}x`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR", callback_data="cancel_all")]]))
                    except: pass
        await process.wait()

        if os.path.exists(out) and not data["cancel"]:
            up_client = client
            if os.path.getsize(out) > 2000*1024*1024 and premium_client: up_client = premium_client
            
            d, w, h = get_video_info(out)
            cap = f"✅ **¡Listo!**\n👤 ID: `{uid}`\n📏 Res: `{data['res']}p`"

            await up_client.send_video(uid, out, caption=cap, duration=d, width=w, height=h, supports_streaming=True, progress=progress_bar, progress_args=(status_msg, time.time(), "SUBIENDO RESULTADO"))
            await up_client.send_video(DUMP_ID, out, caption=f"📦 **Copia Comprimida**\n👤 ID: `{uid}`", duration=d, width=w, height=h, supports_streaming=True)
            await status_msg.delete()

    except Exception as e: 
        if not data["cancel"]: await status_msg.edit(f"❌ Error: {e}")
    finally:
        for f in [v_path, s_path, out]: 
            if f and os.path.exists(f): os.remove(f)
        if uid in user_data: del user_data[uid]

if __name__ == "__main__":
    bot.run()
