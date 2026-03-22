import os
import asyncio
import time
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

# Inicialización del cliente Bot
bot = Client(
    "HarsubBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# Cliente Premium (se activa solo si hay STRING_SESSION en config.py)
premium_client = None
if hasattr(Config, "STRING_SESSION") and Config.STRING_SESSION:
    premium_client = Client(
        "PremiumUser", 
        api_id=Config.API_ID, 
        api_hash=Config.API_HASH, 
        session_string=Config.STRING_SESSION
    )

user_data = {}

# --- FUNCIÓN DE AYUDA PARA MENÚ DE CONFIGURACIÓN ---
def get_config_menu(user_id):
    data = user_data[user_id]
    c_name = "Amarillo 🟡" if data['color'] == "&H00FFFF" else "Blanco ⚪"
    s_name = f"{data['size']}px"
    i_name = "Cursiva ✍️" if data['italic'] == "1" else "Recta 📏"
    o_name = "Con Contorno ✅" if data['outline'] == "2" else "Sin Contorno ❌"

    text = (
        "🎬 **CONFIGURACIÓN DE SUBTÍTULOS**\n\n"
        f"🎨 **Color:** `{c_name}`\n"
        f"📏 **Tamaño:** `{s_name}`\n"
        f"✍️ **Estilo:** `{i_name}`\n"
        f"🖼️ **Borde:** `{o_name}`\n\n"
        "Personaliza los detalles antes de iniciar:"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟡 Amarillo", callback_data="set_col_&H00FFFF"),
         InlineKeyboardButton("⚪ Blanco", callback_data="set_col_&HFFFFFF")],
        [InlineKeyboardButton("➖ Pequeño", callback_data="set_siz_18"),
         InlineKeyboardButton("➕ Grande", callback_data="set_siz_32")],
        [InlineKeyboardButton("✍️ Cursiva", callback_data="set_sty_italic"),
         InlineKeyboardButton("📏 Recta", callback_data="set_sty_normal")],
        [InlineKeyboardButton("🖼️ Contorno", callback_data="set_out_2"),
         InlineKeyboardButton("❌ Sin Borde", callback_data="set_out_0")],
        [InlineKeyboardButton("🚀 INICIAR PROCESO", callback_data="start")]
    ])
    return text, markup

# --- FUNCIÓN DE BARRA DE PROGRESO ---
async def progress_bar(current, total, status_msg, start_time, action):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        eta = f"{round((total - current) / speed)}s" if speed > 0 else "..."
        bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
        
        msg = (f"🚀 **{action}**\n\n"
               f"进度: `{bar}` {round(percentage, 2)}%\n"
               f"⚡ Velocidad: `{round(speed / 1024 / 1024, 2)} MB/s` \n"
               f"⏱️ ETA: `{eta}`")
        try:
            await status_msg.edit(msg)
        except:
            pass

# --- MANEJADORES DE MENSAJES ---

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("👋 ¡Hola! Envíame un **video** para comenzar.")

@bot.on_message(filters.video | filters.document)
async def handle_files(client, message):
    user_id = message.from_user.id
    
    if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith("video/")):
        user_data[user_id] = {
            "video": message, "subtitle": None, 
            "color": "&HFFFFFF", "size": "24", 
            "italic": "0", "outline": "2", "process": None
        }
        await message.reply("✅ Video recibido. Ahora envía el archivo **.srt**")
        
    elif message.document and message.document.file_name and message.document.file_name.endswith(".srt"):
        if user_id not in user_data:
            return await message.reply("❌ Envía el video primero.")
        
        user_data[user_id]["subtitle"] = message
        text, markup = get_config_menu(user_id)
        await message.reply(text, reply_markup=markup)

# --- CALLBACKS (BOTONES) ---

@bot.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    
    if query.data.startswith("set_"):
        _, type_set, val = query.data.split("_")
        if type_set == "col": user_data[user_id]["color"] = val
        elif type_set == "siz": user_data[user_id]["size"] = val
        elif type_set == "out": user_data[user_id]["outline"] = val
        elif type_set == "sty": user_data[user_id]["italic"] = "1" if val == "italic" else "0"
        
        text, markup = get_config_menu(user_id)
        try: await query.message.edit(text, reply_markup=markup)
        except: pass

    elif query.data == "start":
        if user_id not in user_data or not user_data[user_id]["subtitle"]:
            return await query.answer("❌ Faltan archivos.", show_alert=True)
        await query.message.edit("⏳ Iniciando motores...")
        await run_engine(client, query.message, user_id)
        
    elif query.data == "cancel_process":
        if user_id in user_data and user_data[user_id]["process"]:
            try:
                user_data[user_id]["process"].terminate()
                await query.answer("🛑 Deteniendo y enviando lo procesado hasta ahora...", show_alert=True)
            except: pass

# --- MOTOR DE PROCESAMIENTO ---

async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    chat_id = status_msg.chat.id
    
    v_path = await data["video"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando Video 📥"))
    s_path = await data["subtitle"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando SRT 📝"))

    output = f"{v_path}_harsub.mp4"
    style = f"PrimaryColour={data['color']},FontSize={data['size']},Italic={data['italic']},BorderStyle=1,Outline={data['outline']},OutlineColour=&H000000"

    await status_msg.edit(
        "⚙️ **PEGANDO SUBTÍTULOS...**\n\nSi cancelas, subiré lo que se haya procesado.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR Y ENVIAR", callback_data="cancel_process")]])
    )
    
    # Flags especiales (-movflags) para que el video sea reproducible aunque se cancele
    cmd = [
        "ffmpeg", "-i", v_path,
        "-vf", f"subtitles={s_path}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-c:a", "copy",
        "-movflags", "frag_keyframe+empty_moov", 
        output, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd)
    user_data[user_id]["process"] = process
    await process.wait()

    # --- LÓGICA DE SUBIDA (PREMIUM / SPLIT) ---
    if os.path.exists(output) and os.path.getsize(output) > 50000:
        f_size = os.path.getsize(output)
        use_premium = False
        
        if premium_client:
            try:
                if not premium_client.is_connected: await premium_client.start()
                use_premium = True
            except: use_premium = False

        files_to_upload = [output]
        uploader = premium_client if (use_premium and f_size < 4000*1024*1024) else client

        # Si NO es premium y pesa > 2GB, dividimos en partes de 1.9GB
        if not use_premium and f_size > 2000*1024*1024:
            await client.send_message(chat_id, "📦 El video supera los 2GB. Dividiendo en partes para la subida...")
            split_cmd = ["ffmpeg", "-i", output, "-c", "copy", "-map", "0", "-f", "segment", "-segment_size", "1900M", "-reset_timestamps", "1", f"{output}_part%03d.mp4"]
            await (await asyncio.create_subprocess_exec(*split_cmd)).wait()
            files_to_upload = sorted([os.path.join(os.path.dirname(output), f) for f in os.listdir(os.path.dirname(output)) if "_part" in f])

        try: await status_msg.delete()
        except: pass

        for i, f_path in enumerate(files_to_upload):
            caption = "✅ **Proceso finalizado.**" + (f"\nParte {i+1}" if len(files_to_upload) > 1 else "")
            up_msg = await client.send_message(chat_id, f"📤 Subiendo parte {i+1}/{len(files_to_upload)}...")
            try:
                await uploader.send_video(
                    chat_id=chat_id,
                    video=f_path,
                    caption=caption,
                    progress=progress_bar,
                    progress_args=(up_msg, time.time(), f"Subiendo Parte {i+1}")
                )
                await up_msg.delete()
            except Exception as e:
                await client.send_message(chat_id, f"❌ Error al subir: {e}")
    else:
        await status_msg.edit("❌ Error: No hay suficiente video procesado para enviar.")

    # Limpieza final
    to_clean = [v_path, s_path, output] + (files_to_upload if 'files_to_upload' in locals() and len(files_to_upload) > 1 else [])
    for p in to_clean:
        if os.path.exists(p): os.remove(p)
    if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    print("✅ Bot iniciado correctamente.")
    bot.run()
