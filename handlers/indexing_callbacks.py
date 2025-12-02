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

db = DatabaseManager()
tmdb = TMDBApi()

# Storage temporal de datos de indexación por usuario
indexing_sessions = {}

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
        self.stats = {
            'indexed': 0,
            'skipped': 0,
            'errors': 0
        }

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
    
    # idx_retry_{msg_id} - Reintentar búsqueda con título original
    elif data.startswith('idx_retry_'):
        await retry_search(update, context, data)
    
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
    
    session = indexing_sessions.get(user_id)
    if not session or not session.search_results:
        await query.edit_message_text("❌ Sesión expirada. Inicia indexación nuevamente.")
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
    
    session = indexing_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión expirada.")
        return
    
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
        
        # Preparar datos para guardar
        video_data = {
            "file_id": session.current_video_data['file_id'],
            "message_id": msg_id,
            "title": movie_data.get("title"),
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
        
        # Publicar en canal de verificación
        channel_msg = await publish_to_verification_channel(context, movie_data, msg_id)
        if channel_msg:
            video_data["channel_message_id"] = channel_msg.message_id
        
        # Guardar en BD
        await db.add_video(**video_data)
        
        # Actualizar estadísticas
        session.stats['indexed'] += 1
        
        await query.edit_message_text(
            f"✅ <b>{movie_data['title']}</b> guardado exitosamente!\n\n"
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
    
    session = indexing_sessions.get(user_id)
    if session:
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
    
    session = indexing_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión expirada.")
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
    session = indexing_sessions.get(user_id)
    
    if not session or not session.awaiting_title_input:
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
    
    session = indexing_sessions.get(user_id)
    if not session or not session.search_results:
        await query.edit_message_text("❌ Sesión expirada.")
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
    
    session = indexing_sessions.get(user_id)
    if session:
        session.stats['skipped'] += 1
    
    await query.edit_message_text(
        f"⏭️ Video {msg_id} saltado.\n\n"
        f"📊 Saltados: {session.stats['skipped'] if session else 1}"
    )

async def stop_indexing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detiene el proceso de indexación"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    session = indexing_sessions.get(user_id)
    
    if session:
        stats_text = (
            f"🛑 <b>Indexación Detenida</b>\n\n"
            f"📊 Resumen:\n"
            f"✅ Indexados: {session.stats['indexed']}\n"
            f"⏭️ Saltados: {session.stats['skipped']}\n"
            f"❌ Errores: {session.stats['errors']}\n"
            f"📍 Último mensaje: {session.current_message_id or 'N/A'}"
        )
        del indexing_sessions[user_id]
    else:
        stats_text = "🛑 Indexación detenida."
    
    await query.edit_message_text(stats_text, parse_mode='HTML')

async def publish_to_verification_channel(context, movie_data, storage_msg_id):
    """Publica película en canal de verificación con poster y botón de deep link"""
    try:
        # Descargar poster
        poster_url = movie_data.get("poster_url")
        if not poster_url:
            return None
        
        response = req.get(poster_url, timeout=10)
        response.raise_for_status()
        photo = io.BytesIO(response.content)
        photo.name = "poster.jpg"
        
        # Crear caption
        title = movie_data.get("title", "Sin título")
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
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{context.bot.username}?start=video_{storage_msg_id}")
        ]])
        
        msg = await context.bot.send_photo(
            chat_id=VERIFICATION_CHANNEL_ID,
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        return msg
        
    except Exception as e:
        print(f"❌ Error publicando en canal: {e}")
        return None
