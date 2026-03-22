import os
import asyncio
import time
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

# Inicialización del cliente
bot = Client(
    "HarsubBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
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
        # Valores iniciales por defecto
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
                await query.answer("🛑 Cancelando y enviando lo obtenido...", show_alert=True)
            except: pass

# --- MOTOR DE PROCESAMIENTO ---

async def run_engine(client, status_msg, user_id):
    data = user_data[user_id]
    
    v_path = await data["video"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando Video 📥"))
    s_path = await data["subtitle"].download(progress=progress_bar, progress_args=(status_msg, time.time(), "Descargando SRT 📝"))

    output = f"{v_path}_harsub.mp4"
    
    # Construcción del estilo ASS para FFmpeg
    style = (
        f"PrimaryColour={data['color']},"
        f"FontSize={data['size']},"
        f"Italic={data['italic']},"
        f"BorderStyle=1,"
        f"Outline={data['outline']},"
        f"OutlineColour=&H000000" # Contorno siempre negro para legibilidad
    )

    await status_msg.edit(
        "⚙️ **PEGANDO SUBTÍTULOS...**\n\n"
        f"🎨 Color: `{data['color']}` | 📏 Size: `{data['size']}`\n"
        "Revisa los logs para ver el avance real.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 CANCELAR Y ENVIAR", callback_data="cancel_process")]])
    )
    
    cmd = [
        "ffmpeg", "-i", v_path,
        "-vf", f"subtitles={s_path}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-c:a", "copy",
        output, "-y"
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd)
    user_data[user_id]["process"] = process
    await process.wait()

    # Envío del video (Limpiamos el mensaje antes para refrescar la barra de subida)
    try: await status_msg.delete()
    except: pass
    
    final_msg = await client.send_message(status_msg.chat.id, "📤 **Iniciando subida del resultado...**")

    if os.path.exists(output) and os.path.getsize(output) > 5000:
        try:
            await client.send_video(
                chat_id=status_msg.chat.id,
                video=output,
                caption="✅ **Hardsub completado.**",
                progress=progress_bar,
                progress_args=(final_msg, time.time(), "Subiendo a Telegram 📤")
            )
        except Exception as e:
            await final_msg.edit(f"❌ Error al subir: {e}")
    else:
        await final_msg.edit("❌ Error: No se generó el video (posible cancelación o falta de espacio).")

    # Limpieza final
    for p in [v_path, s_path, output]:
        if os.path.exists(p): os.remove(p)
    if user_id in user_data: del user_data[user_id]
    try: await final_msg.delete()
    except: pass

if __name__ == "__main__":
    print("✅ Bot iniciado correctamente.")
    bot.run()
