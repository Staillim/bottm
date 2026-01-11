"""
Handler de callbacks para el sistema de indexación mejorado
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from utils.tmdb_api import TMDBApi
from utils.title_cleaner import clean_title, format_title_with_year
from config.settings import VERIFICATION_CHANNEL_ID
import io
import requests as req
import time

db = DatabaseManager()
tmdb = TMDBApi()

# Storage temporal de datos de indexación por usuario
indexing_sessions = {}

# Duración de sesión en segundos (6 horas)
SESSION_DURATION = 6 * 60 * 60

class IndexingSession:
    """Clase para almacenar el estado de una sesión de indexación"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_message_id = None
        self.current_video_data = None
        self.search_results = None
        self.awaiting_title_input = False
        self.paused_at = None
        self.progress_message_id = None
        self.created_at = time.time()  # Timestamp de creación
        self.last_activity = time.time()  # Última actividad
        self.stats = {
            'indexed': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def update_activity(self):
        """Actualiza el timestamp de última actividad"""
        self.last_activity = time.time()
    
    def is_expired(self):
        """Verifica si la sesión ha expirado"""
        return (time.time() - self.last_activity) > SESSION_DURATION

def clean_expired_sessions():
    """Limpia las sesiones expiradas"""
    current_time = time.time()
    expired_users = []
    
    for user_id, session in indexing_sessions.items():
        if session.is_expired():
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del indexing_sessions[user_id]
    
    return len(expired_users)

def get_or_create_session(user_id):
    """Obtiene una sesión existente o crea una nueva si no existe o ha expirado"""
    # Limpiar sesiones expiradas primero
    clean_expired_sessions()
    
    session = indexing_sessions.get(user_id)
    
    if session is None or session.is_expired():
        # Crear nueva sesión
        session = IndexingSession(user_id)
        indexing_sessions[user_id] = session
    else:
        # Actualizar actividad
        session.update_activity()
    
    return session

async def handle_indexing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los callbacks relacionados con indexación"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # idx_confirm_{msg_id}_{tmdb_id} - Confirmar película encontrada
    if data.startswith('idx_confirm_'):
        await confirm_movie(update, context, data)
    
    # idx_edit_{msg_id} - Editar título para re-buscar
    elif data.startswith('idx_edit_'):
        await request_title_edit(update, context, data)
    
    # idx_skip_{msg_id} - Saltar este video
    elif data.startswith('idx_skip_'):
        await skip_video(update, context, data)
    
    # idx_stop - Detener indexación
    elif data.startswith('idx_stop'):
        await stop_indexing(update, context)
    
    # idx_select_{msg_id}_{result_index} - Seleccionar de múltiples resultados
    elif data.startswith('idx_select_'):
        await select_from_results(update, context, data)
    
    # idx_save_{msg_id}_{tmdb_id} - Guardar confirmado
    elif data.startswith('idx_save_'):
        await save_confirmed_movie(update, context, data)
    
    # idx_cancel_{msg_id} - Cancelar guardado
    elif data.startswith('idx_cancel_'):
        await cancel_save(update, context, data)

async def confirm_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Usuario confirma que la película encontrada es correcta"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Parsear: idx_confirm_{msg_id}_{tmdb_id}
    parts = callback_data.split('_')
    msg_id = int(parts[2])
    tmdb_id = int(parts[3])
    
    session = get_or_create_session(user_id)
    
    # Verificar que hay datos de búsqueda válidos
    if not session.search_results:
        hours_since = (time.time() - session.created_at) / 3600
        await query.edit_message_text(
            f"❌ Sesión expirada.\n"
            f"🕐 Sesión creada hace {hours_since:.1f} horas\n"
            f"⏰ Máximo permitido: {SESSION_DURATION/3600:.0f} horas\n\n"
            f"Inicia indexación nuevamente."
        )
        return
    
    # Buscar el resultado seleccionado
    movie_data = None
    for result in session.search_results:
        if result['tmdb_id'] == tmdb_id:
            movie_data = result
            break
    
    if not movie_data:
        await query.edit_message_text("❌ Error: No se encontró la película seleccionada.")
        return
    
    # Mostrar preview final antes de guardar
    await show_save_preview(update, context, msg_id, movie_data, session.current_video_data)

async def show_save_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, msg_id: int, movie_data: dict, video_data: dict):
    """Muestra preview final antes de guardar"""
    query = update.callback_query
    
    title = movie_data.get('title', 'Sin título')
    year = movie_data.get('year', 'N/A')
    rating = movie_data.get('vote_average', 0)
    overview = movie_data.get('overview', '')[:200]
    
    preview_text = (
        f"📋 <b>Preview Final</b>\n\n"
        f"🎬 <b>{title}</b> ({year})\n"
        f"⭐ {rating}/10\n"
        f"🆔 TMDB ID: {movie_data.get('tmdb_id')}\n\n"
        f"📝 {overview}...\n\n"
        f"¿Guardar este video?"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Guardar", callback_data=f"idx_save_{msg_id}_{movie_data['tmdb_id']}"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"idx_cancel_{msg_id}")
        ]
    ]
    
    await query.edit_message_text(
        preview_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def save_confirmed_movie(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Guarda la película después de confirmación"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Parsear: idx_save_{msg_id}_{tmdb_id}
    parts = callback_data.split('_')
    msg_id = int(parts[2])
    tmdb_id = int(parts[3])
    
    print(f"\n🔍 DEBUG save_confirmed_movie:")
    print(f"   msg_id desde callback: {msg_id}")
    
    session = get_or_create_session(user_id)
    
    # Verificar que la sesión tiene datos válidos
    if not session.search_results:
        hours_since = (time.time() - session.created_at) / 3600
        await query.edit_message_text(
            f"❌ Sesión expirada.\n"
            f"🕐 Sesión creada hace {hours_since:.1f} horas\n"
            f"⏰ Máximo permitido: {SESSION_DURATION/3600:.0f} horas\n\n"
            f"Inicia indexación nuevamente."
        )
        return
    
    print(f"   session.current_message_id: {session.current_message_id}")
    await query.edit_message_text("💾 Guardando...")
    
    try:
        # Buscar datos completos de la película
        movie_data = None
        for result in session.search_results:
            if result['tmdb_id'] == tmdb_id:
                movie_data = result
                break
        
        if not movie_data:
            await query.edit_message_text("❌ Error: Datos de película no encontrados.")
            return
        
        # Usar el título original del caption del canal de almacenamiento
        original_caption = session.current_video_data.get('original_caption', movie_data.get("title"))
        
        # Preparar datos para guardar
        video_data = {
            "file_id": session.current_video_data['file_id'],
            "message_id": msg_id,
            "title": original_caption,  # Usar caption original del canal
            "tmdb_id": movie_data.get("tmdb_id"),
            "original_title": movie_data.get("original_title"),
            "year": movie_data.get("year"),
            "overview": movie_data.get("overview"),
            "poster_url": movie_data.get("poster_url"),
            "backdrop_url": movie_data.get("backdrop_url"),
            "vote_average": int(movie_data.get("vote_average", 0) * 10),
            "genres": ", ".join([str(g) for g in movie_data.get("genre_ids", [])]),
            "description": "",
            "tags": ""
        }
        
        # Verificar si ya existe (re-indexación)
        existing = await db.get_video_by_message_id(msg_id)
        
        # Si es re-indexación, eliminar post antiguo del canal
        if existing and existing.channel_message_id:
            try:
                from config.settings import VERIFICATION_CHANNEL_ID
                await context.bot.delete_message(
                    chat_id=VERIFICATION_CHANNEL_ID,
                    message_id=existing.channel_message_id
                )
            except Exception as e:
                print(f"⚠️ No se pudo eliminar mensaje antiguo del canal: {e}")
        
        # Publicar en canal de verificación (siempre publica nuevo)
        print(f"   Publicando con storage_msg_id: {msg_id}")
        # Pasar el título original del caption
        channel_msg = await publish_to_verification_channel(context, movie_data, msg_id, original_caption)
        if channel_msg:
            video_data["channel_message_id"] = channel_msg.message_id
            print(f"   channel_message_id del post: {channel_msg.message_id}")
        
        if existing:
            # Actualizar video existente
            print(f"   Actualizando video existente con message_id: {msg_id}")
            await db.update_video(
                message_id=msg_id,
                title=video_data["title"],
                tmdb_id=video_data["tmdb_id"],
                original_title=video_data["original_title"],
                year=video_data["year"],
                overview=video_data["overview"],
                poster_url=video_data["poster_url"],
                backdrop_url=video_data["backdrop_url"],
                vote_average=video_data["vote_average"],
                genres=video_data["genres"],
                channel_message_id=video_data.get("channel_message_id")
            )
            action = "actualizado"
        else:
            # Guardar nuevo video en BD
            print(f"   Insertando nuevo video con message_id: {msg_id}")
            print(f"   Datos guardados: title={video_data['title']}, message_id={video_data['message_id']}, channel_message_id={video_data.get('channel_message_id')}")
            await db.add_video(**video_data)
            action = "guardado"
        
        # Actualizar estadísticas
        session.stats['indexed'] += 1
        
        await query.edit_message_text(
            f"✅ <b>{original_caption}</b> guardado exitosamente!\n\n"
            f"🎬 Vinculado con TMDB: {movie_data['title']}\n"
            f"📊 Progreso: {session.stats['indexed']} indexados",
            parse_mode='HTML'
        )
        
        # Si está en modo automático, continuar
        # (esto se manejará en el comando principal)
        
    except Exception as e:
        session.stats['errors'] += 1
        await query.edit_message_text(f"❌ Error al guardar: {str(e)}")

async def cancel_save(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Cancela el guardado de una película"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    parts = callback_data.split('_')
    msg_id = int(parts[2])
    
    session = get_or_create_session(user_id)
    session.stats['skipped'] += 1
    
    await query.edit_message_text(
        f"⏭️ Video {msg_id} saltado.\n\n"
        f"Continuando con el siguiente..."
    )

async def request_title_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Solicita al usuario que envíe un título corregido"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Parsear: idx_edit_{msg_id}
    parts = callback_data.split('_')
    msg_id = int(parts[2])
    
    session = get_or_create_session(user_id)
    
    # Verificar que la sesión es válida
    if not hasattr(session, 'current_video_data') or not session.current_video_data:
        hours_since = (time.time() - session.created_at) / 3600
        await query.edit_message_text(
            f"❌ Sesión expirada.\n"
            f"🕐 Sesión creada hace {hours_since:.1f} horas\n"
            f"⏰ Máximo permitido: {SESSION_DURATION/3600:.0f} horas\n\n"
            f"Inicia indexación nuevamente."
        )
        return
    
    session.awaiting_title_input = True
    session.current_message_id = msg_id
    
    await query.edit_message_text(
        "✏️ <b>Editar Título</b>\n\n"
        "Envía el título correcto de la película.\n"
        "Puedes incluir el año entre paréntesis.\n\n"
        "Ejemplo: <code>Avengers Endgame (2019)</code>\n\n"
        "O envía /cancelar para cancelar.",
        parse_mode='HTML'
    )

async def handle_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el input de título corregido del usuario"""
    user_id = update.effective_user.id
    session = get_or_create_session(user_id)
    
    if not session.awaiting_title_input:
        return False  # No es para nosotros
    
    new_title = update.message.text.strip()
    
    if new_title.lower() == '/cancelar':
        session.awaiting_title_input = False
        await update.message.reply_text("❌ Edición cancelada.")
        return True
    
    session.awaiting_title_input = False
    
    # Buscar con el nuevo título
    await update.message.reply_text(f"🔍 Buscando: <b>{new_title}</b>...", parse_mode='HTML')
    
    cleaned, year = clean_title(new_title)
    results = tmdb.search_movie(cleaned, year=year, return_multiple=True, limit=5)
    
    # Asegurar que results sea lista
    if results is None:
        results = []
    
    if not results:
        keyboard = [
            [InlineKeyboardButton("✏️ Intentar otro título", callback_data=f"idx_edit_{session.current_message_id}")],
            [InlineKeyboardButton("⏭️ Saltar video", callback_data=f"idx_skip_{session.current_message_id}")]
        ]
        await update.message.reply_text(
            f"❌ No se encontraron resultados para: <b>{new_title}</b>\n\n"
            f"¿Qué quieres hacer?",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return True
    
    session.search_results = results
    
    # Mostrar resultados
    await show_search_results(update, context, session.current_message_id, results, new_title)
    return True

async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, msg_id: int, results: list, search_term: str):
    """Muestra múltiples resultados de búsqueda para que el usuario elija"""
    text = f"🔍 <b>Resultados para:</b> {search_term}\n\n"
    text += "Selecciona la película correcta:\n\n"
    
    keyboard = []
    for idx, result in enumerate(results[:5]):
        title = result.get('title', 'Sin título')
        year = result.get('year', 'N/A')
        rating = result.get('vote_average', 0)
        confidence = result.get('confidence', 0)
        
        # Emoji de confianza
        conf_emoji = "🟢" if confidence >= 80 else "🟡" if confidence >= 50 else "🔴"
        
        button_text = f"{conf_emoji} {title} ({year}) ⭐{rating}/10"
        keyboard.append([
            InlineKeyboardButton(
                button_text[:60],  # Limitar tamaño
                callback_data=f"idx_select_{msg_id}_{idx}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("✏️ Buscar otro título", callback_data=f"idx_edit_{msg_id}"),
        InlineKeyboardButton("⏭️ Saltar", callback_data=f"idx_skip_{msg_id}")
    ])
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def select_from_results(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Usuario selecciona una película de los resultados múltiples"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Parsear: idx_select_{msg_id}_{result_index}
    parts = callback_data.split('_')
    msg_id = int(parts[2])
    result_idx = int(parts[3])
    
    session = get_or_create_session(user_id)
    
    # Verificar que hay resultados de búsqueda válidos
    if not session.search_results:
        hours_since = (time.time() - session.created_at) / 3600
        await query.edit_message_text(
            f"❌ Sesión expirada.\n"
            f"🕐 Sesión creada hace {hours_since:.1f} horas\n"
            f"⏰ Máximo permitido: {SESSION_DURATION/3600:.0f} horas\n\n"
            f"Inicia indexación nuevamente."
        )
        return
    
    if result_idx >= len(session.search_results):
        await query.edit_message_text("❌ Selección inválida.")
        return
    
    movie_data = session.search_results[result_idx]
    
    # Mostrar preview final
    await show_save_preview(update, context, msg_id, movie_data, session.current_video_data)

async def skip_video(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Salta un video sin indexar"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    parts = callback_data.split('_')
    msg_id = int(parts[2])
    
    session = get_or_create_session(user_id)
    session.stats['skipped'] += 1
    
    await query.edit_message_text(
        f"⏭️ Video {msg_id} saltado.\n\n"
        f"📊 Saltados: {session.stats['skipped']}"
    )

async def stop_indexing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detiene el proceso de indexación"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    session = get_or_create_session(user_id)
    
    if session:
        stats_text = (
            f"🛑 <b>Indexación Detenida</b>\n\n"
            f"📊 Resumen:\n"
            f"✅ Indexados: {session.stats['indexed']}\n"
            f"⏭️ Saltados: {session.stats['skipped']}\n"
            f"❌ Errores: {session.stats['errors']}\n"
            f"📍 Último mensaje: {session.current_message_id or 'N/A'}"
        )
        # Limpiar completamente la sesión
        session.awaiting_title_input = False
        session.current_message_id = None
        session.current_video_data = None
        session.search_results = None
        del indexing_sessions[user_id]
    else:
        stats_text = "🛑 Indexación detenida."
    
    await query.edit_message_text(stats_text, parse_mode='HTML')

async def publish_to_verification_channel(context, movie_data, storage_msg_id, original_title=None):
    """
    Publica película en todos los canales configurados con poster y botón de deep link
    
    Args:
        original_title: Título original del caption del canal de almacenamiento (opcional)
    
    Returns: Mensaje del primer canal (VERIFICATION_CHANNEL_ID) para guardar en BD
    """
    from config.settings import PUBLICATION_CHANNELS, VERIFICATION_CHANNEL_ID
    import io
    import requests as req
    
    try:
        # Descargar poster
        poster_url = movie_data.get("poster_url")
        if not poster_url:
            print(f"⚠️ No hay poster_url, abortando publicación")
            return None
        
        print(f"📥 Descargando poster desde: {poster_url}")
        response = req.get(poster_url, timeout=10)
        response.raise_for_status()
        photo_bytes = response.content
        
        # Usar el título original del caption si está disponible, sino usar el de TMDB
        title = original_title if original_title else movie_data.get("title", "Sin título")
        year = movie_data.get("year", "N/A")
        rating = movie_data.get("vote_average", 0)
        overview = movie_data.get("overview", "")
        
        if len(overview) > 200:
            overview = overview[:197] + "..."
        
        caption = (
            f"🎬 <b>{title}</b> ({year})\n"
            f"⭐ {rating}/10\n\n"
            f"{overview}"
        )
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{context.bot.username}?start=video_{storage_msg_id}")
        ]])
        
        print(f"📢 Publicando en {len(PUBLICATION_CHANNELS)} canal(es)...")
        
        main_msg = None  # Mensaje del canal principal para retornar
        
        # Publicar en todos los canales
        for idx, channel_id in enumerate(PUBLICATION_CHANNELS):
            try:
                # Crear nuevo BytesIO para cada envío (no se puede reutilizar)
                photo = io.BytesIO(photo_bytes)
                photo.name = "poster.jpg"
                
                msg = await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                
                print(f"✅ Publicado en canal {channel_id} (message_id: {msg.message_id})")
                
                # Guardar el mensaje del canal principal (verificación)
                if channel_id == VERIFICATION_CHANNEL_ID:
                    main_msg = msg
                    
            except Exception as e:
                print(f"❌ Error publicando en canal {channel_id}: {e}")
                continue
        
        # Enviar notificaciones a grupos
        await send_group_notifications(context, title, year, storage_msg_id)
        
        return main_msg
        
    except Exception as e:
        print(f"❌ Error en publish_to_verification_channel: {e}")
        import traceback
        traceback.print_exc()
        return None

async def send_group_notifications(context, title, year, storage_msg_id):
    """
    Envía notificaciones cortas a grupos configurados cuando se agrega una nueva película/serie
    
    Args:
        context: Contexto del bot
        title: Título de la película/serie
        year: Año de la película/serie 
        storage_msg_id: ID del mensaje en el canal de almacenamiento para deep link
    """
    from config.settings import NOTIFICATION_GROUPS
    
    if not NOTIFICATION_GROUPS:
        print("📝 No hay grupos configurados para notificaciones")
        return
    
    # Mensaje corto para grupos
    group_message = f"🆕 Se agregó <b>{title}</b> ({year})"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔍 Ver en el bot", url=f"https://t.me/{context.bot.username}?start=video_{storage_msg_id}")
    ]])
    
    print(f"📱 Enviando notificaciones a {len(NOTIFICATION_GROUPS)} grupo(s)...")
    
    async def delete_message_job(context):
        """Job para borrar el mensaje después de 1 hora"""
        chat_id = context.job.data['chat_id']
        message_id = context.job.data['message_id']
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"🗑️ Mensaje borrado del grupo {chat_id}")
        except Exception as e:
            print(f"⚠️ No se pudo borrar mensaje del grupo {chat_id}: {e}")
    
    for group_id in NOTIFICATION_GROUPS:
        try:
            sent_message = await context.bot.send_message(
                chat_id=group_id,
                text=group_message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            print(f"✅ Notificación enviada al grupo {group_id}")
            
            # Programar borrado en 1 hora
            context.job_queue.run_once(
                delete_message_job,
                when=3600,  # 1 hora (3600 segundos)
                data={'chat_id': group_id, 'message_id': sent_message.message_id},
                name=f"delete_notification_{group_id}_{sent_message.message_id}"
            )
            print(f"⏰ Programado borrado en 1h para grupo {group_id}")
            
        except Exception as e:
            print(f"❌ Error enviando notificación al grupo {group_id}: {e}")
            continue

