from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS, STORAGE_CHANNEL_ID, VERIFICATION_CHANNEL_ID
from utils.tmdb_api import TMDBApi
import io
import requests as req

async def indexar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para indexar videos - Empieza desde el último mensaje encontrado"""
    user = update.effective_user
    
    # Verificar si es admin
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    db = context.bot_data['db']
    
    # Obtener todos los videos indexados para encontrar el último message_id
    videos = await db.search_videos("", limit=10000)
    ultimo_msg_id = max([v.message_id for v in videos]) if videos else 599
    
    # Empezar desde el siguiente mensaje después del último encontrado
    start_id = ultimo_msg_id + 1
    
    await update.message.reply_text(f"🔄 Buscando desde mensaje {start_id}...")
    
    indexed = 0
    skipped = 0
    empty_count = 0
    ultimo_encontrado = ultimo_msg_id  # Guardar el último mensaje NO vacío
    
    # Buscar hasta 2000 mensajes después del último (ajustable)
    for msg_id in range(start_id, start_id + 2000):
        try:
            # Intentar obtener el mensaje
            msg = await context.bot.forward_message(
                chat_id=user.id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=msg_id
            )
            
            # Mensaje existe - resetear contador y actualizar último encontrado
            empty_count = 0
            ultimo_encontrado = msg_id
            
            # Si tiene video, procesarlo
            if msg.video:
                title = msg.caption or f"Video {msg_id}"
                
                # Verificar si ya está indexado
                try:
                    existing = await db.get_video_by_id(msg_id)
                    if existing:
                        skipped += 1
                        await context.bot.delete_message(chat_id=user.id, message_id=msg.message_id)
                        continue
                except:
                    pass
                
                # Buscar en TMDB
                tmdb = TMDBApi()
                movie_data = tmdb.search_movie(title)
                
                # Preparar datos para guardar
                video_data = {
                    "file_id": msg.video.file_id,
                    "message_id": msg_id,
                    "title": title,
                    "description": "",
                    "tags": ""
                }
                
                # Si encontró en TMDB, agregar metadata
                if movie_data:
                    video_data.update({
                        "tmdb_id": movie_data.get("tmdb_id"),
                        "original_title": movie_data.get("original_title"),
                        "year": movie_data.get("year"),
                        "overview": movie_data.get("overview"),
                        "poster_url": movie_data.get("poster_url"),
                        "backdrop_url": movie_data.get("backdrop_url"),
                        "vote_average": int(movie_data.get("vote_average", 0) * 10),
                        "genres": ", ".join([str(g) for g in movie_data.get("genre_ids", [])])
                    })
                    
                    # Publicar en canal de verificación
                    try:
                        channel_msg = await publish_to_verification_channel(
                            context, movie_data, msg_id
                        )
                        if channel_msg:
                            video_data["channel_message_id"] = channel_msg.message_id
                    except Exception as e:
                        print(f"Error publicando en canal: {e}")
                
                # Agregar video a la base de datos
                await db.add_video(**video_data)
                indexed += 1
            
            # Borrar mensaje temporal
            try:
                await context.bot.delete_message(chat_id=user.id, message_id=msg.message_id)
            except:
                pass
                
        except Exception:
            # Mensaje no existe - incrementar contador
            empty_count += 1
            
            # Si encuentra 10 mensajes vacíos seguidos, detener
            if empty_count >= 10:
                break
    
    await update.message.reply_text(
        f"✅ Indexación completa:\n\n"
        f"📹 Videos nuevos: {indexed}\n"
        f"⏭️ Ya existentes: {skipped}\n"
        f"📊 Total: {indexed + skipped} videos\n"
        f"🔚 Último mensaje: {ultimo_encontrado}"
    )

async def publish_to_verification_channel(context, movie_data, storage_msg_id):
    """Publica película en canal de verificación con poster y botón"""
    try:
        # Descargar poster
        poster_url = movie_data.get("poster_url")
        if not poster_url:
            return None
        
        response = req.get(poster_url, timeout=10)
        response.raise_for_status()
        photo = io.BytesIO(response.content)
        photo.name = "poster.jpg"
        
        # Crear caption bonito
        title = movie_data.get("title", "Sin título")
        year = movie_data.get("year", "N/A")
        rating = movie_data.get("vote_average", 0)
        overview = movie_data.get("overview", "")
        
        # Limitar descripción a 200 caracteres
        if len(overview) > 200:
            overview = overview[:197] + "..."
        
        caption = (
            f"🎬 <b>{title}</b> ({year})\n"
            f"⭐ {rating}/10\n\n"
            f"{overview}"
        )
        
        # Botón para ver en el bot
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{context.bot.username}?start=video_{storage_msg_id}")
        ]])
        
        # Publicar en canal
        msg = await context.bot.send_photo(
            chat_id=VERIFICATION_CHANNEL_ID,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        return msg
        
    except Exception as e:
        print(f"Error en publish_to_verification_channel: {e}")
        return None

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para ver estadísticas (solo admins)"""
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    db = context.bot_data['db']
    
    # Aquí podrías agregar consultas a la BD para estadísticas
    await update.message.reply_text(
        "📊 *Estadísticas del Bot*\n\n"
        "Funcionalidad en desarrollo...",
        parse_mode='Markdown'
    )
