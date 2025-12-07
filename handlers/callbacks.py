"""
Handler unificado de callbacks para el sistema de menús interactivos
"""
from telegram import Update
from telegram.ext import ContextTypes
from handlers.menu import (
    main_menu, movies_menu, series_menu,
    show_seasons_menu, show_episodes_menu
)
from config.settings import STORAGE_CHANNEL_ID, WEBAPP_URL, API_SERVER_URL
import logging
import urllib.parse

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los callbacks del sistema de menús"""
    db = context.bot_data['db']
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = update.effective_user.id
    
    try:
        # ==================== NAVEGACIÓN DE MENÚS ====================
        
        if callback_data == "menu_main":
            await main_menu(update, context)
        
        elif callback_data == "menu_movies":
            await movies_menu(update, context)
        
        elif callback_data == "menu_series":
            await series_menu(update, context)
        
        # ==================== SELECCIÓN DE PELÍCULA ====================
        
        elif callback_data.startswith("movie_"):
            video_id = int(callback_data.split("_")[1])
            await handle_movie_selection(update, context, video_id)
        
        # ==================== SELECCIÓN DE SERIE ====================
        
        elif callback_data.startswith("series_"):
            show_id = int(callback_data.split("_")[1])
            await show_seasons_menu(update, context, show_id)
        
        # ==================== SELECCIÓN DE TEMPORADA ====================
        
        elif callback_data.startswith("season_"):
            parts = callback_data.split("_")
            show_id = int(parts[1])
            season_number = int(parts[2])
            await show_episodes_menu(update, context, show_id, season_number)
        
        # ==================== SELECCIÓN DE EPISODIO ====================
        
        elif callback_data.startswith("episode_"):
            episode_id = int(callback_data.split("_")[1])
            await handle_episode_selection(update, context, episode_id)
        
        # ==================== CALLBACK DESCONOCIDO ====================
        
        else:
            logger.warning(f"Callback desconocido: {callback_data}")
            await query.edit_message_text("❌ Acción no reconocida.")
    
    except Exception as e:
        logger.error(f"Error en callback handler: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Ocurrió un error. Intenta nuevamente.",
            parse_mode='HTML'
        )

async def handle_movie_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: int):
    """Maneja la selección de una película"""
    db = context.bot_data['db']
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Obtener video de la base de datos
    video = await db.get_video_by_id(video_id)
    
    if not video:
        await query.edit_message_text("❌ Película no encontrada.")
        return
    
    try:
        # Verificar si el usuario tiene un token válido
        user = await db.get_user(user_id)
        has_valid_token = await db.has_valid_token(user_id, video_id)
        
        if has_valid_token:
            # Usuario ya vio el anuncio, enviar video directamente
            await send_movie_video(update, context, video)
        else:
            # Mostrar anuncio primero
            await show_movie_ad(update, context, video, user)
    
    except Exception as e:
        logger.error(f"Error al procesar película: {e}", exc_info=True)
        await query.edit_message_text("❌ Error al procesar la película.")

async def handle_episode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, episode_id: int):
    """Maneja la selección de un episodio"""
    db = context.bot_data['db']
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Obtener episodio de la base de datos
    episode = await db.get_episode_by_id(episode_id)
    
    if not episode:
        await query.edit_message_text("❌ Episodio no encontrado.")
        return
    
    # Obtener información de la serie
    show = await db.get_tv_show_by_id(episode.tv_show_id)
    if not show:
        await query.edit_message_text("❌ Serie no encontrada.")
        return
    
    try:
        # Verificar si el usuario tiene un token válido para este episodio
        # Usamos el episode_id como identificador único
        has_valid_token = await db.has_valid_token(user_id, episode_id)
        
        if has_valid_token:
            # Usuario ya vio el anuncio, enviar episodio directamente
            await send_episode_video(update, context, episode, show)
        else:
            # Mostrar anuncio primero
            await show_episode_ad(update, context, episode, show)
    
    except Exception as e:
        logger.error(f"Error al procesar episodio: {e}", exc_info=True)
        await query.edit_message_text("❌ Error al procesar el episodio.")

async def send_movie_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video):
    """Envía el video de la película al usuario"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        # Copiar mensaje del canal al usuario
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=video.message_id
        )
        
        # Registrar la búsqueda
        await db.add_search(user_id, video.title, video.id)
        
        await query.edit_message_text(
            f"✅ <b>{video.title}</b> enviada correctamente.\n\n"
            "¿Quieres buscar otra película?",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error enviando película: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error al enviar la película. Contacta al administrador."
        )

async def send_episode_video(update: Update, context: ContextTypes.DEFAULT_TYPE, episode, show):
    """Envía el video del episodio al usuario"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        # Copiar mensaje del canal al usuario
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=STORAGE_CHANNEL_ID,
            message_id=episode.message_id
        )
        
        # Registrar la búsqueda (usando el nombre de la serie + episodio)
        episode_name = f"{show.name} {episode.season_number}x{episode.episode_number:02d}"
        await db.add_search(user_id, episode_name, episode.id)
        
        await query.edit_message_text(
            f"✅ <b>{show.name}</b>\n"
            f"Temporada {episode.season_number}, Episodio {episode.episode_number}\n\n"
            "Enviado correctamente. ¿Quieres ver otro episodio?",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error enviando episodio: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error al enviar el episodio. Contacta al administrador."
        )

async def show_movie_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, video, user):
    """Muestra anuncio antes de enviar película"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Construir URL con parámetros
    title_encoded = urllib.parse.quote(video.title or "Película")
    poster_encoded = urllib.parse.quote(video.poster_url or "")
    api_url_encoded = urllib.parse.quote(API_SERVER_URL)
    
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}&video_id={video.id}&title={title_encoded}&poster={poster_encoded}&api_url={api_url_encoded}&content_type=movie"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver anuncio", web_app={"url": webapp_url})],
        [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎬 <b>{video.title}</b>\n\n"
        "⏳ Para ver esta película, primero debes ver un breve anuncio.\n\n"
        "Toca el botón de abajo y completa el anuncio.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_episode_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, episode, show):
    """Muestra anuncio antes de enviar episodio"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Construir título y URL con parámetros
    episode_title = f"{show.name} - {episode.season_number}x{episode.episode_number:02d}"
    if episode.title:
        episode_title += f" - {episode.title}"
    
    title_encoded = urllib.parse.quote(episode_title)
    poster_encoded = urllib.parse.quote(show.poster_url or "")
    api_url_encoded = urllib.parse.quote(API_SERVER_URL)
    
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}&video_id={episode.id}&title={title_encoded}&poster={poster_encoded}&api_url={api_url_encoded}&content_type=episode"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver anuncio", web_app={"url": webapp_url})],
        [InlineKeyboardButton("⬅️ Volver a episodios", callback_data=f"season_{show.id}_{episode.season_number}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📺 <b>{show.name}</b>\n"
        f"Temporada {episode.season_number}, Episodio {episode.episode_number}\n\n"
        "⏳ Para ver este episodio, primero debes ver un breve anuncio.\n\n"
        "Toca el botón de abajo y completa el anuncio.",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
