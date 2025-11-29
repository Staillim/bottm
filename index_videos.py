import asyncio
import os
from telegram import Bot
from database.db_manager import DatabaseManager
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

LAST_INDEX_FILE = "last_indexed_message.txt"
MAX_EMPTY_MESSAGES = 10  # Detener después de 10 mensajes vacíos consecutivos

def get_last_indexed():
    """Obtiene el último mensaje indexado desde el archivo o comienza desde 812."""
    if os.path.exists(LAST_INDEX_FILE):
        try:
            with open(LAST_INDEX_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 812  # Empezar desde 812 si hay error
    return 812  # Empezar desde 812 si no existe el archivo

def save_last_indexed(msg_id):
    """Guarda el último mensaje indexado en el archivo"""
    try:
        with open(LAST_INDEX_FILE, 'w') as f:
            f.write(str(msg_id))
    except Exception as e:
        print(f"Error al guardar el progreso: {e}")

async def index_channel_videos():
    bot = Bot(token=BOT_TOKEN)
    db = DatabaseManager()
    await db.init_db()
    
    # Obtener información del bot para usar su chat ID personal
    bot_info = await bot.get_me()
    bot_chat_id = f"@{bot_info.username}"
    
    start_from = get_last_indexed()
    
    print("Iniciando indexación de videos...")
    print(f"Canal de almacén: {STORAGE_CHANNEL_ID}")
    print(f"Chat del bot: {bot_chat_id}")
    print(f"Comenzando desde mensaje: {start_from}")
    print(f"Se detendrá después de {MAX_EMPTY_MESSAGES} mensajes vacíos consecutivos")
    print("-" * 50)
    
    indexed = 0
    empty_count = 0
    current_msg_id = start_from
    last_video_msg_id = start_from - 1  # Último mensaje que tuvo video
    
    # Iterar hasta encontrar MAX_EMPTY_MESSAGES mensajes vacíos consecutivos
    while empty_count < MAX_EMPTY_MESSAGES:
        try:
            # Verificar si el video ya existe en la base de datos
            existing_video = await db.get_video_by_message_id(current_msg_id)
            if existing_video:
                print(f"⚠️ Video ya indexado: {current_msg_id}")
                last_video_msg_id = current_msg_id  # Actualizar último mensaje con video
                try:
                    save_last_indexed(current_msg_id + 1)
                except Exception as e:
                    print(f"Error al guardar el progreso: {e}")
                finally:
                    pass
                current_msg_id += 1
                continue

            # Intentar obtener el mensaje del canal
            try:
                print(f"🔍 Intentando acceder al mensaje {current_msg_id}...")
                if current_msg_id == 859:
                    print(f"🎯 Buscando específicamente el mensaje 859 que mencionaste...")

                message = await bot.forward_message(
                    chat_id=bot_chat_id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=current_msg_id
                )

                if current_msg_id == 859:
                    print(f"✅ ¡Mensaje 859 encontrado! Contenido: {message.caption if message.caption else 'Sin título'}")
                    print(f"📹 ¿Tiene video?: {message.video is not None}")

                print(f"✅ Mensaje {current_msg_id} reenviado exitosamente")

                if message.video:
                    title = message.caption or f"Video {current_msg_id}"

                    # Verificar nuevamente si el video ya existe antes de agregarlo
                    existing_video = await db.get_video_by_message_id(current_msg_id)
                    if existing_video:
                        print(f"⚠️ Video duplicado detectado al agregar: {current_msg_id}")
                        last_video_msg_id = current_msg_id  # Actualizar último mensaje con video
                        try:
                            save_last_indexed(current_msg_id + 1)
                        except Exception as e:
                            print(f"Error al guardar el progreso: {e}")
                        finally:
                            pass
                        current_msg_id += 1
                        continue

                    await db.add_video(
                        file_id=message.video.file_id,
                        message_id=current_msg_id,
                        title=title,
                        description="",
                        tags=""
                    )
                    indexed += 1
                    last_video_msg_id = current_msg_id  # Actualizar último mensaje con video
                    print(f"✅ [{current_msg_id}] Indexado: {title}")

                    # Guardar progreso después de cada video indexado
                    try:
                        save_last_indexed(current_msg_id + 1)
                    except Exception as e:
                        print(f"Error al guardar el progreso: {e}")
                else:
                    empty_count += 1
                    print(f"⏭️  [{current_msg_id}] Sin video ({empty_count}/{MAX_EMPTY_MESSAGES})")
            except Exception as e:
                empty_count += 1
                print(f"⏭️  [{current_msg_id}] No encontrado o error ({empty_count}/{MAX_EMPTY_MESSAGES}): {e}")
            finally:
                current_msg_id += 1
        except Exception as e:
            print(f"Error general en la verificación de video {current_msg_id}: {e}")
            empty_count += 1
            current_msg_id += 1
            continue
    
    # Guardar el último mensaje procesado (último video + 1)
    try:
        save_last_indexed(last_video_msg_id + 1)
    except Exception as e:
        print(f"Error al guardar el último mensaje procesado: {e}")
    finally:
        pass
    print("-" * 50)
    print(f"\n✅ Indexación completa: {indexed} videos indexados")
    print(f"📍 Último mensaje procesado: {last_video_msg_id}")
    print(f"🛑 Detenido después de {MAX_EMPTY_MESSAGES} mensajes vacíos consecutivos")

if __name__ == "__main__":
    asyncio.run(index_channel_videos())
