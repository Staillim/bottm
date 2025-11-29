import asyncio
from telegram import Bot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

async def check_specific_message(message_id):
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"🤖 Bot: @{bot_info.username}")
        print(f"🎯 Verificando mensaje ID: {message_id}")
        print(f"📺 En canal: {STORAGE_CHANNEL_ID}")

        # Intentar reenviar el mensaje específico
        try:
            message = await bot.forward_message(
                chat_id=f"@{bot_info.username}",
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=message_id
            )

            print("✅ ¡Mensaje encontrado!")
            print(f"📝 Tipo: {'Video' if message.video else 'Otro'}")
            if message.video:
                print(f"🎬 Título: {message.caption if message.caption else 'Sin título'}")
                print(f"📊 Duración: {message.video.duration} segundos")
                print(f"📏 Tamaño: {message.video.file_size} bytes")
            else:
                print(f"💬 Contenido: {message.text if message.text else message.caption if message.caption else 'Sin texto'}")

        except Exception as e:
            print(f"❌ Error al acceder al mensaje {message_id}: {e}")

            # Intentar método alternativo: get_chat_history (si el bot es admin)
            try:
                print("🔄 Intentando método alternativo...")
                # Esto solo funciona si el bot es admin y puede leer el historial
                # Pero la API de Bot no permite getChatHistory para bots
                print("⚠️ Los bots no pueden leer historial completo de canales")
            except:
                pass

    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    # Verificar el mensaje 859 específicamente
    asyncio.run(check_specific_message(859))