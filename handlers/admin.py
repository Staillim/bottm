from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS, STORAGE_CHANNEL_ID, VERIFICATION_CHANNEL_ID
from utils.tmdb_api import TMDBApi
from utils.title_cleaner import clean_title, format_title_with_year
from handlers.indexing_callbacks import IndexingSession, indexing_sessions, show_search_results
import io
import requests as req
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

async def indexar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando mejorado para indexar videos - Proceso interactivo y eficiente"""
    user = update.effective_user
    
    # Verificar si es admin
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    db = context.bot_data['db']
    
    # Crear sesión de indexación
    session = IndexingSession(user.id)
    indexing_sessions[user.id] = session
    
    # Obtener último mensaje indexado
    last_indexed_str = await db.get_config('last_indexed_message', '812')
    start_id = int(last_indexed_str)
    
    # Mensaje inicial
    initial_msg = await update.message.reply_text(
        f"🔄 <b>Iniciando Indexación Mejorada</b>\n\n"
        f"📍 Desde mensaje: {start_id}\n"
        f"🎯 Modo: Interactivo con confirmación\n\n"
        f"⏳ Escaneando canal...",
        parse_mode='HTML'
    )
    
    session.progress_message_id = initial_msg.message_id
    
    tmdb = TMDBApi()
    current_id = start_id
    consecutive_empty = 0
    max_empty = 10
    max_scan = 2000
    
    try:
        for offset in range(max_scan):
            msg_id = start_id + offset
            
            # Actualizar progreso cada 20 mensajes
            if offset > 0 and offset % 20 == 0:
                await context.bot.edit_message_text(
                    chat_id=user.id,
                    message_id=session.progress_message_id,
                    text=(
                        f"📊 <b>Progreso</b>\n\n"
                        f"🔍 Escaneando: mensaje {msg_id}\n"
                        f"✅ Indexados: {session.stats['indexed']}\n"
                        f"⏭️ Saltados: {session.stats['skipped']}\n"
                        f"❌ Errores: {session.stats['errors']}"
                    ),
                    parse_mode='HTML'
                )
            
            # Verificar si la sesión fue detenida
            if user.id not in indexing_sessions:
                break
            
            try:
                # Obtener mensaje sin forward (más eficiente)
                # Usamos copy_message que es más ligero que forward
                try:
                    copied_msg = await context.bot.copy_message(
                        chat_id=user.id,
                        from_chat_id=STORAGE_CHANNEL_ID,
                        message_id=msg_id
                    )
                except Exception as copy_error:
                    # Mensaje no existe o no accesible - continuar al siguiente
                    print(f"⚠️ Mensaje {msg_id} no accesible: {copy_error}")
                    consecutive_empty += 1
                    continue
                
                # Mensaje existe - resetear contador de vacíos
                consecutive_empty = 0
                consecutive_empty = 0
                current_id = msg_id
                
                # Obtener el mensaje original para ver si tiene video
                try:
                    # Intentar forward para obtener el objeto completo
                    original_msg = await context.bot.forward_message(
                        chat_id=user.id,
                        from_chat_id=STORAGE_CHANNEL_ID,
                        message_id=msg_id
                    )
                    
                    # Borrar mensajes temporales
                    try:
                        await context.bot.delete_message(chat_id=user.id, message_id=copied_msg.message_id)
                        await context.bot.delete_message(chat_id=user.id, message_id=original_msg.message_id)
                    except:
                        pass
                    
                    # Procesar solo si tiene video
                    if original_msg.video:
                        # Verificar si ya está indexado
                        existing = await db.get_video_by_message_id(msg_id)
                        if existing:
                            session.stats['skipped'] += 1
                            await db.set_config('last_indexed_message', str(msg_id + 1))
                            continue
                        
                        # NUEVO FLUJO: Procesar con confirmación
                        await process_video_with_confirmation(
                            update, context, original_msg, msg_id, tmdb, db, session
                        )
                        
                        # Guardar progreso
                        await db.set_config('last_indexed_message', str(msg_id + 1))
                        
                        # Pausa para dar tiempo al admin de confirmar
                        # El flujo continúa después de la confirmación
                        return  # Detener aquí, continuar manualmente o en siguiente comando
                        
                except Exception as e:
                    # Error obteniendo mensaje original
                    try:
                        await context.bot.delete_message(chat_id=user.id, message_id=copied_msg.message_id)
                    except:
                        pass
                    continue
            
            except Exception as e:
                # Error en el procesamiento del mensaje
                logger.error(f"Error procesando mensaje {msg_id}: {e}")
                continue

            # Verificar si hemos alcanzado el límite de mensajes vacíos consecutivos
            if consecutive_empty >= max_empty:
                break        # Finalizar sesión
        await finalize_indexing(update, context, session, current_id, db)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error durante indexación: {str(e)}")
        if user.id in indexing_sessions:
            del indexing_sessions[user.id]

async def process_video_with_confirmation(update, context, msg, msg_id, tmdb, db, session):
    """Procesa un video con flujo de confirmación interactivo"""
    user_id = update.effective_user.id
    title = msg.caption or f"Video {msg_id}"
    
    # Limpiar título
    cleaned, year = clean_title(title)
    
    # Guardar datos del video en sesión
    session.current_message_id = msg_id
    session.current_video_data = {
        'file_id': msg.video.file_id,
        'original_caption': title,
        'cleaned_title': cleaned,
        'year': year
    }
    
    # Buscar en TMDB
    results = tmdb.search_movie(cleaned, year=year, return_multiple=True, limit=5)
    
    # Asegurar que results sea lista
    if results is None:
        results = []
    
    if not results:
        # NO SE ENCONTRÓ - Pedir confirmación
        keyboard = [
            [InlineKeyboardButton("✏️ Editar título", callback_data=f"idx_edit_{msg_id}")],
            [InlineKeyboardButton("⏭️ Saltar video", callback_data=f"idx_skip_{msg_id}")],
            [InlineKeyboardButton("🛑 Detener indexación", callback_data="idx_stop")]
        ]
        
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❓ <b>No encontrado en TMDB</b>\n\n"
                f"📝 Título original: <code>{title}</code>\n"
                f"🧹 Título limpio: <code>{cleaned}</code>\n"
                f"📅 Año detectado: {year or 'N/A'}\n\n"
                f"¿Qué quieres hacer?"
            ),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        session.search_results = []
        return
    
    # SE ENCONTRÓ - Verificar confianza
    best_match = results[0]
    confidence = best_match.get('confidence', 0)
    
    session.search_results = results
    
    if confidence >= 80:
        # Alta confianza - Confirmar directamente
        keyboard = [
            [InlineKeyboardButton("✅ Correcto", callback_data=f"idx_confirm_{msg_id}_{best_match['tmdb_id']}")],
            [InlineKeyboardButton("❌ Ver más opciones", callback_data=f"idx_edit_{msg_id}")],
            [InlineKeyboardButton("⏭️ Saltar", callback_data=f"idx_skip_{msg_id}")]
        ]
        
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎯 <b>Match encontrado</b> (Confianza: {confidence:.0f}%)\n\n"
                f"🎬 <b>{best_match['title']}</b> ({best_match['year']})\n"
                f"⭐ {best_match['vote_average']}/10\n"
                f"🆔 TMDB ID: {best_match['tmdb_id']}\n\n"
                f"📝 {best_match.get('overview', '')[:150]}...\n\n"
                f"¿Es correcto?"
            ),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Confianza media/baja - Mostrar opciones
        await show_search_results(update, context, msg_id, results, cleaned)

async def finalize_indexing(update, context, session, last_msg_id, db):
    """Finaliza el proceso de indexación"""
    user_id = update.effective_user.id
    
    await db.set_config('last_indexed_message', str(last_msg_id + 1))
    
    final_text = (
        f"✅ <b>Indexación Completada</b>\n\n"
        f"📊 <b>Resumen:</b>\n"
        f"✅ Indexados: {session.stats['indexed']}\n"
        f"⏭️ Saltados: {session.stats['skipped']}\n"
        f"❌ Errores: {session.stats['errors']}\n\n"
        f"📍 Último mensaje: {last_msg_id}\n"
        f"💾 Progreso guardado: {last_msg_id + 1}"
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=final_text,
        parse_mode='HTML'
    )
    
    # Limpiar sesión
    if user_id in indexing_sessions:
        del indexing_sessions[user_id]

async def indexar_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Indexa un mensaje específico del canal de almacenamiento
    
    Uso: /indexar_manual <message_id>
    Ejemplo: /indexar_manual 1523
    """
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "❌ <b>Uso incorrecto</b>\n\n"
            "Formato: <code>/indexar_manual {message_id}</code>\n"
            "Ejemplo: <code>/indexar_manual 1523</code>",
            parse_mode='HTML'
        )
        return
    
    msg_id = int(context.args[0])
    db = context.bot_data['db']
    
    # Verificar si ya está indexado
    existing = await db.get_video_by_message_id(msg_id)
    if existing:
        await update.message.reply_text(
            f"⚠️ El mensaje {msg_id} ya está indexado:\n\n"
            f"🎬 <b>{existing.title}</b> ({existing.year})\n"
            f"🆔 TMDB ID: {existing.tmdb_id}\n\n"
            f"Usa /reindexar {msg_id} para re-procesar.",
            parse_mode='HTML'
        )
        return
    
    await update.message.reply_text(f"🔍 Obteniendo mensaje {msg_id}...")
    
    try:
        # Obtener mensaje
        msg = await context.bot.forward_message(
            chat_id=user.id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=msg_id
        )
        
        if not msg.video:
            await update.message.reply_text(f"❌ El mensaje {msg_id} no contiene un video.")
            try:
                await context.bot.delete_message(chat_id=user.id, message_id=msg.message_id)
            except:
                pass
            return
        
        # Borrar forward temporal
        try:
            await context.bot.delete_message(chat_id=user.id, message_id=msg.message_id)
        except:
            pass
        
        # Crear sesión de indexación
        session = IndexingSession(user.id)
        indexing_sessions[user.id] = session
        
        # Procesar con confirmación
        tmdb = TMDBApi()
        await process_video_with_confirmation(
            update, context, msg, msg_id, tmdb, db, session
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al obtener mensaje {msg_id}: {str(e)}")

async def reindexar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Re-indexa un video ya existente en la base de datos
    
    Uso: /reindexar <message_id>
    Ejemplo: /reindexar 1523
    """
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "❌ <b>Uso incorrecto</b>\n\n"
            "Formato: <code>/reindexar {message_id}</code>\n"
            "Ejemplo: <code>/reindexar 1523</code>",
            parse_mode='HTML'
        )
        return
    
    msg_id = int(context.args[0])
    db = context.bot_data['db']
    
    # Verificar que existe
    existing = await db.get_video_by_message_id(msg_id)
    if not existing:
        await update.message.reply_text(
            f"❌ El mensaje {msg_id} no está en la base de datos.\n"
            f"Usa /indexar_manual {msg_id} para indexarlo."
        )
        return
    
    # Mostrar info actual
    current_info = (
        f"📊 <b>Video Actual en BD:</b>\n\n"
        f"🎬 <b>{existing.title}</b>\n"
        f"📅 Año: {existing.year or 'N/A'}\n"
        f"🆔 TMDB ID: {existing.tmdb_id or 'N/A'}\n"
        f"⭐ Rating: {existing.vote_average/10 if existing.vote_average else 'N/A'}/10\n\n"
        f"¿Qué quieres hacer?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Re-buscar en TMDB", callback_data=f"ridx_research_{msg_id}")],
        [InlineKeyboardButton("✏️ Buscar con nuevo título", callback_data=f"ridx_newtitle_{msg_id}")],
        [InlineKeyboardButton("📢 Re-publicar en canal", callback_data=f"ridx_republish_{msg_id}")],
        [InlineKeyboardButton("🗑️ Eliminar de BD", callback_data=f"ridx_delete_{msg_id}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="ridx_cancel")]
    ]
    
    await update.message.reply_text(
        current_info,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_reindex_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de re-indexación"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "ridx_cancel":
        await query.edit_message_text("❌ Cancelado.")
        return
    
    # ridx_research_{msg_id}
    if data.startswith('ridx_research_'):
        msg_id = int(data.split('_')[2])
        await reindex_search_tmdb(update, context, msg_id)
    
    # ridx_newtitle_{msg_id}
    elif data.startswith('ridx_newtitle_'):
        msg_id = int(data.split('_')[2])
        await reindex_request_new_title(update, context, msg_id)
    
    # ridx_republish_{msg_id}
    elif data.startswith('ridx_republish_'):
        msg_id = int(data.split('_')[2])
        await reindex_republish(update, context, msg_id)
    
    # ridx_delete_{msg_id}
    elif data.startswith('ridx_delete_'):
        msg_id = int(data.split('_')[2])
        await reindex_delete(update, context, msg_id)

async def reindex_search_tmdb(update, context, msg_id):
    """Re-busca en TMDB con el título actual"""
    query = update.callback_query
    db = context.bot_data['db']
    
    existing = await db.get_video_by_message_id(msg_id)
    if not existing:
        await query.edit_message_text("❌ Video no encontrado en BD.")
        return
    
    await query.edit_message_text(f"🔍 Buscando en TMDB: <b>{existing.title}</b>...", parse_mode='HTML')
    
    # Crear sesión temporal
    user_id = update.effective_user.id
    session = IndexingSession(user_id)
    session.current_message_id = msg_id
    session.current_video_data = {'file_id': existing.file_id}
    indexing_sessions[user_id] = session
    
    # Buscar
    tmdb = TMDBApi()
    cleaned, year = clean_title(existing.title)
    results = tmdb.search_movie(cleaned, year=year, return_multiple=True, limit=5)
    
    # Asegurar que results sea lista
    if results is None:
        results = []
    
    if not results:
        await query.edit_message_text(
            f"❌ No se encontraron resultados para: <b>{existing.title}</b>",
            parse_mode='HTML'
        )
        return
    
    session.search_results = results
    await show_search_results(update, context, msg_id, results, existing.title)

async def reindex_request_new_title(update, context, msg_id):
    """Solicita nuevo título para buscar"""
    query = update.callback_query
    user_id = update.effective_user.id
    db = context.bot_data['db']
    
    # Obtener video existente para guardar file_id
    existing = await db.get_video_by_message_id(msg_id)
    if not existing:
        await query.edit_message_text("❌ Video no encontrado en BD.")
        return
    
    session = IndexingSession(user_id)
    session.current_message_id = msg_id
    session.awaiting_title_input = True
    session.current_video_data = {'file_id': existing.file_id}
    indexing_sessions[user_id] = session
    
    await query.edit_message_text(
        "✏️ <b>Buscar con nuevo título</b>\n\n"
        "Envía el título correcto de la película.\n"
        "Ejemplo: <code>Avengers Endgame (2019)</code>",
        parse_mode='HTML'
    )

async def reindex_republish(update, context, msg_id):
    """Re-publica la película en el canal"""
    query = update.callback_query
    db = context.bot_data['db']
    
    existing = await db.get_video_by_message_id(msg_id)
    if not existing:
        await query.edit_message_text("❌ Video no encontrado.")
        return
    
    await query.edit_message_text("📢 Publicando en canal...")
    
    # Eliminar mensaje antiguo del canal si existe
    if existing.channel_message_id:
        try:
            await context.bot.delete_message(
                chat_id=VERIFICATION_CHANNEL_ID,
                message_id=existing.channel_message_id
            )
        except Exception as e:
            print(f"⚠️ No se pudo eliminar mensaje antiguo: {e}")
    
    movie_data = {
        'title': existing.title,
        'year': existing.year,
        'vote_average': existing.vote_average / 10 if existing.vote_average else 0,
        'overview': existing.overview or '',
        'poster_url': existing.poster_url,
        'tmdb_id': existing.tmdb_id
    }
    
    from handlers.indexing_callbacks import publish_to_verification_channel
    channel_msg = await publish_to_verification_channel(context, movie_data, msg_id)
    
    if channel_msg:
        # Actualizar channel_message_id
        await db.update_video(
            message_id=msg_id,
            channel_message_id=channel_msg.message_id
        )
        await query.edit_message_text(f"✅ Publicado en canal (message_id: {channel_msg.message_id})")
    else:
        await query.edit_message_text("❌ Error al publicar en canal.")

async def reindex_delete(update, context, msg_id):
    """Elimina el video de la base de datos"""
    query = update.callback_query
    db = context.bot_data['db']
    
    # Confirmar
    keyboard = [
        [InlineKeyboardButton("✅ Sí, eliminar", callback_data=f"ridx_delete_confirm_{msg_id}")],
        [InlineKeyboardButton("❌ No, cancelar", callback_data="ridx_cancel")]
    ]
    
    await query.edit_message_text(
        f"⚠️ <b>¿Seguro que quieres eliminar el video {msg_id} de la BD?</b>\n\n"
        f"Esta acción NO se puede deshacer.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
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
