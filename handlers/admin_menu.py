"""
Menú de administración para gestionar series
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from config.settings import ADMIN_IDS
import logging

db = DatabaseManager()
logger = logging.getLogger(__name__)

async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /admin - Muestra menú de administración de series
    """
    user_id = update.effective_user.id
    
    # Verificar si es admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📺 Gestionar Series", callback_data="admin_manage_series")],
        [InlineKeyboardButton("🎬 Indexar Nueva Serie", callback_data="admin_new_series")],
        [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 <b>Panel de Administración</b>\n\n"
        "Selecciona una opción:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_manage_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra lista de series para gestionar
    """
    query = update.callback_query
    await query.answer()
    
    # Obtener todas las series
    # Usamos un límite alto para obtener todas
    from sqlalchemy import select
    from database.models import TvShow
    
    async with db.async_session() as session:
        result = await session.execute(
            select(TvShow).order_by(TvShow.added_at.desc()).limit(50)
        )
        all_shows = result.scalars().all()
    
    if not all_shows:
        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ No hay series indexadas.\n\n"
            "Usa el botón 'Indexar Nueva Serie' para comenzar.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Crear botones para cada serie
    keyboard = []
    for show in all_shows[:20]:  # Máximo 20 series
        title = f"{show.name}"
        if show.year:
            title += f" ({show.year})"
        
        keyboard.append([
            InlineKeyboardButton(title, callback_data=f"admin_show_{show.id}")
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Volver", callback_data="admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📺 <b>Series Indexadas</b>\n\n"
        "Selecciona una serie para gestionar:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_show_details(update: Update, context: ContextTypes.DEFAULT_TYPE, show_id: int):
    """
    Muestra detalles de una serie y opciones de gestión
    """
    query = update.callback_query
    await query.answer()
    
    # Obtener serie
    show = await db.get_tv_show_by_id(show_id)
    if not show:
        await query.edit_message_text("❌ Serie no encontrada.")
        return
    
    # Obtener estadísticas
    seasons = await db.get_seasons_for_show(show_id)
    total_episodes = sum(count for _, count in seasons)
    
    # Encontrar último episodio
    all_episodes = await db.get_episodes_by_show(show_id)
    last_episode = None
    if all_episodes:
        last_episode = max(all_episodes, key=lambda ep: (ep.season_number, ep.episode_number))
    
    message_text = f"📺 <b>{show.name}</b>"
    if show.year:
        message_text += f" ({show.year})"
    message_text += f"\n\n"
    message_text += f"🎬 Temporadas: {len(seasons)}\n"
    message_text += f"📹 Total episodios: {total_episodes}\n"
    
    if last_episode:
        message_text += f"\n📌 Último episodio: S{last_episode.season_number}x{last_episode.episode_number:02d}"
        if last_episode.title:
            message_text += f"\n   {last_episode.title}"
    
    keyboard = [
        [InlineKeyboardButton("➕ Agregar Nuevo Episodio", callback_data=f"admin_add_episode_{show_id}")],
        [InlineKeyboardButton("📋 Ver Episodios", callback_data=f"admin_list_episodes_{show_id}")],
        [InlineKeyboardButton("⬅️ Volver a Series", callback_data="admin_manage_series")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_add_episode(update: Update, context: ContextTypes.DEFAULT_TYPE, show_id: int):
    """
    Inicia el proceso de agregar un nuevo episodio
    """
    query = update.callback_query
    await query.answer()
    
    # Obtener serie
    show = await db.get_tv_show_by_id(show_id)
    if not show:
        await query.edit_message_text("❌ Serie no encontrada.")
        return
    
    # Encontrar último episodio
    all_episodes = await db.get_episodes_by_show(show_id)
    last_episode = None
    if all_episodes:
        last_episode = max(all_episodes, key=lambda ep: (ep.season_number, ep.episode_number))
    
    # Guardar en contexto para auto-indexación
    context.user_data['auto_index_show_id'] = show_id
    context.user_data['auto_index_show_name'] = show.name
    context.user_data['waiting_for_first_episode'] = True
    
    message_text = f"➕ <b>Agregar Nuevos Episodios</b>\n\n"
    message_text += f"📺 Serie: <b>{show.name}</b>\n\n"
    
    if last_episode:
        message_text += f"📌 Último episodio en DB:\n"
        message_text += f"   S{last_episode.season_number}x{last_episode.episode_number:02d}"
        if last_episode.title:
            message_text += f" - {last_episode.title}"
        message_text += f"\n\n"
    
    message_text += f"📝 <b>Instrucciones:</b>\n"
    message_text += f"1️⃣ Sube los videos al canal de almacenamiento con caption <code>#x#</code>\n"
    message_text += f"2️⃣ Reenvía el PRIMER episodio nuevo aquí\n"
    message_text += f"3️⃣ El bot escaneará automáticamente hasta encontrar todos los episodios\n"
    message_text += f"4️⃣ Se detendrá tras 5 mensajes vacíos\n\n"
    message_text += f"Ejemplo: <code>1x5</code>, <code>2x1</code> o <code>Loki 1x5</code>"
    
    keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data=f"admin_show_{show_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def process_new_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el mensaje reenviado para agregar nuevo episodio
    """
    if not context.user_data.get('waiting_for_new_episode'):
        return False
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return False
    
    # Verificar que sea un mensaje reenviado del canal
    if not update.message.forward_from_chat:
        await update.message.reply_text(
            "❌ Debes reenviar un mensaje del canal de almacenamiento.\n\n"
            "Usa /admin para cancelar."
        )
        return True
    
    show_id = context.user_data.get('adding_episode_show_id')
    show_name = context.user_data.get('adding_episode_show_name')
    
    if not show_id:
        await update.message.reply_text("❌ Error: No hay serie seleccionada.")
        return True
    
    # Verificar que el mensaje tenga video
    if not update.message.video:
        await update.message.reply_text("❌ El mensaje debe contener un video.")
        return True
    
    # Buscar patrón #x# en el caption (puede estar en cualquier parte)
    import re
    text_to_search = update.message.caption if update.message.caption else ""
    pattern = r'(\d+)[xX](\d+)'
    match = re.search(pattern, text_to_search)
    
    if not match:
        await update.message.reply_text(
            "❌ No se encontró el formato #x# en el caption del video.\n\n"
            "Ejemplo: <code>1x5</code>, <code>2x1</code>",
            parse_mode='HTML'
        )
        return True
    
    season_number = int(match.group(1))
    episode_number = int(match.group(2))
    
    # Verificar si ya existe
    existing = await db.get_episode(show_id, season_number, episode_number)
    if existing:
        await update.message.reply_text(
            f"⚠️ El episodio S{season_number}x{episode_number:02d} ya existe en la base de datos.\n\n"
            f"Usa /admin para gestionar series."
        )
        context.user_data.pop('waiting_for_new_episode', None)
        return True
    
    # Obtener información del mensaje
    file_id = update.message.video.file_id
    message_id = update.message.forward_from_message_id
    
    # Buscar info en TMDB
    from utils.tmdb_api import TMDBApi
    tmdb = TMDBApi()
    show = await db.get_tv_show_by_id(show_id)
    
    season_details = tmdb.get_season_details(show.tmdb_id, season_number)
    episode_info = None
    if season_details and season_details.get('episodes'):
        for ep in season_details['episodes']:
            if ep['episode_number'] == episode_number:
                episode_info = ep
                break
    
    # Guardar episodio
    episode = await db.add_episode(
        tv_show_id=show_id,
        file_id=file_id,
        message_id=message_id,
        season_number=season_number,
        episode_number=episode_number,
        title=episode_info.get('name') if episode_info else None,
        overview=episode_info.get('overview') if episode_info else None,
        air_date=episode_info.get('air_date') if episode_info else None,
        runtime=episode_info.get('runtime') if episode_info else None,
        still_path=episode_info.get('still_path') if episode_info else None,
        channel_message_id=message_id
    )
    
    # Limpiar contexto
    context.user_data.pop('waiting_for_new_episode', None)
    context.user_data.pop('adding_episode_show_id', None)
    context.user_data.pop('adding_episode_show_name', None)
    
    if episode:
        message_text = f"✅ <b>Episodio agregado exitosamente</b>\n\n"
        message_text += f"📺 {show_name}\n"
        message_text += f"🎬 S{season_number}x{episode_number:02d}"
        if episode_info and episode_info.get('name'):
            message_text += f" - {episode_info['name']}"
        message_text += f"\n\n"
        message_text += f"Usa /admin para agregar más episodios."
        
        await update.message.reply_text(message_text, parse_mode='HTML')
    else:
        await update.message.reply_text("❌ Error al guardar el episodio.")
    
    return True

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja callbacks del menú de administración
    """
    query = update.callback_query
    data = query.data
    
    if data == "admin_back":
        await admin_menu_command(update, context)
    
    elif data == "admin_manage_series":
        await admin_manage_series(update, context)
    
    elif data == "admin_new_series":
        await query.answer()
        await query.edit_message_text(
            "📝 Para indexar una nueva serie, usa:\n\n"
            "<code>/indexar_serie Nombre de la Serie (Año)</code>\n\n"
            "Ejemplo:\n"
            "<code>/indexar_serie Loki (2021)</code>",
            parse_mode='HTML'
        )
    
    elif data.startswith("admin_show_"):
        show_id = int(data.split("_")[2])
        await admin_show_details(update, context, show_id)
    
    elif data.startswith("admin_add_episode_"):
        show_id = int(data.split("_")[3])
        await admin_add_episode(update, context, show_id)
    
    elif data == "admin_stats":
        await query.answer()
        await query.edit_message_text("📊 Estadísticas - En desarrollo")
