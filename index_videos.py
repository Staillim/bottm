import asyncio
import os
from telegram import Bot
from database.db_manager import DatabaseManager
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

LAST_INDEX_FILE = "last_indexed_message.txt"
MAX_EMPTY_MESSAGES = 10  # Detener después de 10 mensajes vacíos consecutivos

def get_last_indexed():
    """Obtiene el último mensaje indexado desde el archivo"""
    if os.path.exists(LAST_INDEX_FILE):
        try:
            with open(LAST_INDEX_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 1  # Empezar desde 1 si hay error
    return 1  # Empezar desde 1 si no existe el archivo

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
    print(f"Se detendrá después de {MAX_EMPTY_MESSAGES} mensajes vacíos consecutivos")
    print("-" * 50)
    
    indexed = 0
    empty_count = 0
    current_msg_id = start_from
    
    # Iterar hasta encontrar MAX_EMPTY_MESSAGES mensajes vacíos consecutivos
    while empty_count < MAX_EMPTY_MESSAGES:
        try:
            message = await bot.forward_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=current_msg_id
            )
            
            if message.video:
                title = message.caption or f"Video {current_msg_id}"
                await db.add_video(
                    file_id=message.video.file_id,
                    message_id=current_msg_id,
                    title=title,
                    description="",
                    tags=""
                )
                indexed += 1
                empty_count = 0  # Resetear contador de vacíos
                print(f"✅ [{current_msg_id}] Indexado: {title}")
                
                # Guardar progreso cada 10 videos
                if indexed % 10 == 0:
                    save_last_indexed(current_msg_id + 1)
                    print(f"💾 Progreso guardado en mensaje {current_msg_id + 1}")
            else:
                empty_count += 1
                print(f"⏭️  [{current_msg_id}] Sin video ({empty_count}/{MAX_EMPTY_MESSAGES})")
        except Exception as e:
            # Mensaje no existe o error
            empty_count += 1
            print(f"⏭️  [{current_msg_id}] No encontrado ({empty_count}/{MAX_EMPTY_MESSAGES})")
        
        current_msg_id += 1
    
    # Guardar el último mensaje procesado
    save_last_indexed(current_msg_id)
    print("-" * 50)
    print(f"\n✅ Indexación completa: {indexed} videos indexados")
    print(f"📍 Último mensaje procesado: {current_msg_id - 1}")
    print(f"🛑 Detenido después de {MAX_EMPTY_MESSAGES} mensajes vacíos consecutivos")

if __name__ == "__main__":
    asyncio.run(index_channel_videos())
