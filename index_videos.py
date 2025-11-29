import asyncio
import os
from telegram import Bot
from database.db_manager import DatabaseManager
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

LAST_INDEX_FILE = "last_indexed_message.txt"
MAX_MESSAGE_ID = 10000  # Ajusta según el tamaño de tu canal

def get_last_indexed():
    """Obtiene el último mensaje indexado desde el archivo"""
    if os.path.exists(LAST_INDEX_FILE):
        try:
            with open(LAST_INDEX_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 600  # Valor por defecto si hay error
    return 600  # Empezar desde 600 si no existe el archivo

def save_last_indexed(msg_id):
    """Guarda el último mensaje indexado en el archivo"""
    with open(LAST_INDEX_FILE, 'w') as f:
        f.write(str(msg_id))

async def index_channel_videos():
    bot = Bot(token=BOT_TOKEN)
    db = DatabaseManager()
    await db.init_db()
    
    start_from = get_last_indexed()
    
    print("Iniciando indexación de videos...")
    print(f"Canal de almacén: {STORAGE_CHANNEL_ID}")
    print(f"Comenzando desde mensaje: {start_from}")
    print(f"Rango máximo: {MAX_MESSAGE_ID}")
    print("-" * 50)
    
    indexed = 0
    last_indexed_id = start_from
    
    # Iterar desde el último indexado hasta MAX_MESSAGE_ID
    for msg_id in range(start_from, MAX_MESSAGE_ID + 1):
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
                last_indexed_id = msg_id
                print(f"✅ [{msg_id}] Indexado: {title}")
                
                # Guardar progreso cada 10 videos
                if indexed % 10 == 0:
                    save_last_indexed(msg_id)
                    print(f"💾 Progreso guardado en mensaje {msg_id}")
        except Exception as e:
            # Ignorar mensajes que no existen o no tienen video
            continue
    
    # Guardar el último mensaje procesado
    save_last_indexed(last_indexed_id)
    print("-" * 50)
    print(f"\n✅ Indexación completa: {indexed} videos indexados")
    print(f"📍 Último mensaje procesado: {last_indexed_id}")

if __name__ == "__main__":
    asyncio.run(index_channel_videos())
