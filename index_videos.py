import asyncio
from telegram import Bot
from database.db_manager import DatabaseManager
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

async def index_channel_videos():
    bot = Bot(token=BOT_TOKEN)
    db = DatabaseManager()
    await db.init_db()
    
    print("Iniciando indexación de videos...")
    print(f"Canal de almacén: {STORAGE_CHANNEL_ID}")
    
    indexed = 0
    
    # Nota: Telegram limita a obtener mensajes de uno en uno
    # Para indexación masiva, necesitarás iterar
    for msg_id in range(1, 100):  # Ajusta el rango según necesites
        try:
            message = await bot.forward_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=msg_id
            )
            
            if message.video:
                title = message.caption or f"Video {msg_id}"
                await db.add_video(
                    file_id=message.video.file_id,
                    message_id=msg_id,
                    title=title,
                    description="",
                    tags=""
                )
                indexed += 1
                print(f"✅ Indexado: {title}")
        except Exception as e:
            # Ignorar mensajes que no existen o no tienen video
            continue
    
    print(f"\n✅ Indexación completa: {indexed} videos indexados")

if __name__ == "__main__":
    asyncio.run(index_channel_videos())
