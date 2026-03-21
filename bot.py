import os
import time
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config

# Inicializamos el cliente del Bot
bot = Client(
    "HarsubBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Diccionario temporal para guardar preferencias de usuario
user_settings = {}

@bot.on_message(filters.video | filters.document)
async def handle_video(client, message):
    # Filtramos para que solo acepte videos o documentos de video
    if message.document and not message.document.mime_type.startswith("video/"):
        return

    user_id = message.from_user.id
    user_settings[user_id] = {"color": "&H00FFFF", "size": "24"} # Valores por defecto

    await message.reply(
        "🎬 **¡Video recibido!**\n\nSelecciona el estilo de los subtítulos antes de procesar:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Amarillo 🟡", callback_data="set_color_&H00FFFF"),
                InlineKeyboardButton("Blanco ⚪", callback_data="set_color_&HFFFFFF")
            ],
            [
                InlineKeyboardButton("Pequeño 🔡", callback_data="set_size_18"),
                InlineKeyboardButton("Grande 🔠", callback_data="set_size_32")
            ],
            [InlineKeyboardButton("🚀 INICIAR PROCESAMIENTO", callback_data="start_harsub")]
        ])
    )

@bot.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data.startswith("set_color_"):
        user_settings[user_id]["color"] = data.split("_")[2]
        await query.answer("Color actualizado ✅")
    
    elif data.startswith("set_size_"):
        user_settings[user_id]["size"] = data.split("_")[2]
        await query.answer("Tamaño actualizado ✅")

    elif data == "start_harsub":
        await query.message.edit("⏳ **Iniciando descarga...**")
        await start_process(client, query.message, user_id)

async def start_process(client, status_msg, user_id):
    # Aquí iría la lógica de descarga (download_media)
    # y la llamada a FFmpeg usando subprocess.
    # Por brevedad, simulamos el flujo:
    
    # 1. Descarga con barra de progreso
    # 2. FFmpeg: ffmpeg -i video.mkv -vf "subtitles=subs.srt:force_style='...'" output.mp4
    # 3. Subida del archivo final
    await status_msg.edit("⚙️ **Procesando video con FFmpeg...**\nEsto puede tardar dependiendo del tamaño.")
    
    # Simulación de finalización
    time.sleep(5) 
    await status_msg.edit("✅ **¡Proceso completado! Enviando...**")

bot.run()
