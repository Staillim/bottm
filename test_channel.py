import asyncio
from telegram import Bot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

async def test_channel_access():
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"🤖 Bot: @{bot_info.username} (ID: {bot_info.id})")
        print(f"📺 Canal objetivo: {STORAGE_CHANNEL_ID}")

        # Intentar obtener información del canal
        try:
            chat = await bot.get_chat(STORAGE_CHANNEL_ID)
            print(f"✅ Canal encontrado: {chat.title}")
            print(f"📝 Tipo: {chat.type}")
            print(f"👥 Miembros: {chat.members_count if hasattr(chat, 'members_count') else 'N/A'}")
        except Exception as e:
            print(f"❌ Error al acceder al canal: {e}")

        # Intentar enviar un mensaje de prueba (esto fallará si no somos admin)
        try:
            sent = await bot.send_message(
                chat_id=STORAGE_CHANNEL_ID,
                text="🧪 Prueba de acceso - ignorar este mensaje",
                disable_notification=True
            )
            print("✅ El bot puede enviar mensajes al canal (es admin)")
            # Borrar el mensaje de prueba
            await bot.delete_message(STORAGE_CHANNEL_ID, sent.message_id)
            print("✅ Mensaje de prueba borrado")
        except Exception as e:
            print(f"⚠️ El bot NO puede enviar mensajes al canal: {e}")

    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    asyncio.run(test_channel_access())