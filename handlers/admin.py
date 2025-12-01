from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS, STORAGE_CHANNEL_ID, VERIFICATION_CHANNEL_ID
from utils.tmdb_api import TMDBApi
import io
import requests as req
import os

async def indexar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para indexar videos - Empieza desde el último mensaje encontrado"""
    user = update.effective_user
    
    # Verificar si es admin
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    db = context.bot_data['db']
    
    # Obtener último mensaje indexado desde la base de datos
    last_indexed_str = await db.get_config('last_indexed_message', '812')
    start_id = int(last_indexed_str)
    
    await update.message.reply_text(f"🔄 Buscando desde mensaje {start_id}...")
    
    indexed = 0
    skipped = 0
    empty_count = 0
    ultimo_encontrado = start_id - 1  # Guardar el último mensaje NO vacío
    
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
                print(f"\n{'='*60}")
                print(f"🎬 Procesando: {title}")
                print(f"   Message ID: {msg_id}")
                
                # Verificar si ya está indexado
                try:
                    existing = await db.get_video_by_message_id(msg_id)
                    if existing:
                        print(f"⏭️  Ya indexado, saltando...")
                        skipped += 1
                        # Guardar progreso
                        await db.set_config('last_indexed_message', msg_id + 1)
                        await context.bot.delete_message(chat_id=user.id, message_id=msg.message_id)
                        continue
                except:
                    pass
                
                # Buscar en TMDB
                print(f"🔍 Buscando en TMDB: {title}")
                tmdb = TMDBApi()
                movie_data = tmdb.search_movie(title)
                
                if movie_data:
                    print(f"✅ TMDB encontrado: {movie_data.get('title')} ({movie_data.get('year')})")
                    print(f"   - TMDB ID: {movie_data.get('tmdb_id')}")
                    print(f"   - Poster: {movie_data.get('poster_url', 'No poster')[:50]}...")
                else:
                    print(f"❌ No se encontró en TMDB")
                
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
                        print(f"📢 Intentando publicar en canal: {title}")
                        channel_msg = await publish_to_verification_channel(
                            context, movie_data, msg_id
                        )
                        if channel_msg:
                            video_data["channel_message_id"] = channel_msg.message_id
                            print(f"✅ Publicado en canal con message_id: {channel_msg.message_id}")
                        else:
                            print(f"⚠️ No se pudo publicar en canal (función retornó None)")
                    except Exception as e:
                        print(f"❌ Error publicando en canal: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"⚠️ No se encontró metadata en TMDB para: {title}")
                
                # Agregar video a la base de datos
                await db.add_video(**video_data)
                indexed += 1
                
                # Guardar progreso después de cada video indexado
                await db.set_config('last_indexed_message', msg_id + 1)
            
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
    
    # Guardar el último mensaje procesado
    await db.set_config('last_indexed_message', ultimo_encontrado + 1)
    
    await update.message.reply_text(
        f"✅ Indexación completa:\n\n"
        f"📹 Videos nuevos: {indexed}\n"
        f"⏭️ Ya existentes: {skipped}\n"
        f"📊 Total: {indexed + skipped} videos\n"
        f"🔚 Último mensaje: {ultimo_encontrado}\n"
        f"💾 Guardado en BD: {ultimo_encontrado + 1}"
    )

async def publish_to_verification_channel(context, movie_data, storage_msg_id):
    """Publica película en canal de verificación con poster y botón de deep link"""
    try:
        print(f"🔍 publish_to_verification_channel llamada con:")
        print(f"   - movie_data keys: {list(movie_data.keys())}")
        print(f"   - storage_msg_id: {storage_msg_id}")
        print(f"   - VERIFICATION_CHANNEL_ID: {VERIFICATION_CHANNEL_ID}")
        
        # Descargar poster
        poster_url = movie_data.get("poster_url")
        if not poster_url:
            print(f"⚠️ No hay poster_url, abortando publicación")
            return None
        
        print(f"📥 Descargando poster desde: {poster_url}")
        response = req.get(poster_url, timeout=10)
        response.raise_for_status()
        photo = io.BytesIO(response.content)
        photo.name = "poster.jpg"
        
        # Crear caption bonito
        title = movie_data.get("title", "Sin título")
        year = movie_data.get("year", "N/A")
        rating = movie_data.get("vote_average", 0)
        overview = movie_data.get("overview", "")
        
        print(f"📝 Preparando mensaje: {title} ({year})")
        
        # Limitar descripción a 200 caracteres
        if len(overview) > 200:
            overview = overview[:197] + "..."
        
        caption = (
            f"🎬 <b>{title}</b> ({year})\n"
            f"⭐ {rating}/10\n\n"
            f"{overview}"
        )
        
        # NOTA: En canales públicos NO se puede usar web_app (da Button_type_invalid)
        # Usamos deep linking normal: usuario hace clic → se abre bot → handler /start procesa
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{context.bot.username}?start=video_{storage_msg_id}")
        ]])
        
        print(f"🔗 Deep link generado: https://t.me/{context.bot.username}?start=video_{storage_msg_id}")
                # Publicar en canal
        msg = await context.bot.send_photo(
            chat_id=VERIFICATION_CHANNEL_ID,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        print(f"✅ Mensaje enviado exitosamente, message_id: {msg.message_id}")
        return msg
        
    except Exception as e:
        print(f"❌ Error en publish_to_verification_channel: {e}")
        import traceback
        traceback.print_exc()
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
