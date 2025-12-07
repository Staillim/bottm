"""
Módulo de menús interactivos para películas y series
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú principal: Películas o Series"""
    db = context.bot_data['db']
    
    keyboard = [
        [
            InlineKeyboardButton("🎬 Películas", callback_data="menu_movies"),
            InlineKeyboardButton("📺 Series", callback_data="menu_series")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "🍿 <b>¿Qué quieres ver?</b>\n\n"
        "Selecciona una opción:"
    )
    
    # Limpiar estado previo del usuario
    user_id = update.effective_user.id
    await db.clear_user_state(user_id)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def movies_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú de películas: Instrucciones para buscar"""
    db = context.bot_data['db']
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    await db.set_user_state(user_id, "movies")
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "🎬 <b>Búsqueda de Películas</b>\n\n"
        "Escribe el nombre de la película que buscas.\n\n"
        "Ejemplos:\n"
        "• <code>Thor</code>\n"
        "• <code>Agentes de S.H.I.E.L.D.</code>\n"
        "• <code>Avengers</code>"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def series_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú de series: Instrucciones para buscar"""
    db = context.bot_data['db']
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    await db.set_user_state(user_id, "series")
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "📺 <b>Búsqueda de Series</b>\n\n"
        "Escribe el nombre de la serie que buscas.\n\n"
        "Ejemplos:\n"
        "• <code>Loki</code>\n"
        "• <code>Breaking Bad</code>\n"
        "• <code>The Office</code>"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_movie_results(update: Update, context: ContextTypes.DEFAULT_TYPE, results, query_text):
    """Muestra resultados de búsqueda de películas"""
    if not results:
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ No se encontraron películas para: <b>{query_text}</b>\n\n"
            "Intenta con otro nombre.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Construir botones con resultados
    keyboard = []
    for video in results[:10]:  # Máximo 10 resultados
        title_display = f"{video.title}"
        if video.year:
            title_display += f" ({video.year})"
        
        keyboard.append([
            InlineKeyboardButton(
                title_display, 
                callback_data=f"movie_{video.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"🎬 <b>Resultados para:</b> {query_text}\n\n"
        f"Encontré {len(results)} película(s). Selecciona una:"
    )
    
    await update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_series_results(update: Update, context: ContextTypes.DEFAULT_TYPE, results, query_text):
    """Muestra resultados de búsqueda de series"""
    if not results:
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ No se encontraron series para: <b>{query_text}</b>\n\n"
            "Intenta con otro nombre.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Construir botones con resultados
    keyboard = []
    for show in results[:10]:  # Máximo 10 resultados
        title_display = f"{show.name}"
        if show.year:
            title_display += f" ({show.year})"
        
        keyboard.append([
            InlineKeyboardButton(
                title_display, 
                callback_data=f"series_{show.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"📺 <b>Resultados para:</b> {query_text}\n\n"
        f"Encontré {len(results)} serie(s). Selecciona una:"
    )
    
    await update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_seasons_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, show_id: int):
    """Muestra menú de temporadas disponibles para una serie"""
    db = context.bot_data['db']
    query = update.callback_query
    await query.answer()
    
    # Obtener serie y temporadas
    show = await db.get_tv_show_by_id(show_id)
    if not show:
        await query.edit_message_text("❌ Serie no encontrada.")
        return
    
    seasons = await db.get_seasons_for_show(show_id)
    if not seasons:
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ No hay episodios disponibles para <b>{show.name}</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Guardar estado del usuario
    user_id = update.effective_user.id
    await db.set_user_state(user_id, "series_seasons", show_id)
    
    # Construir botones de temporadas
    keyboard = []
    for season_number, episode_count in seasons:
        keyboard.append([
            InlineKeyboardButton(
                f"Temporada {season_number} ({episode_count} episodios)",
                callback_data=f"season_{show_id}_{season_number}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Volver a series", callback_data="menu_series")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"📺 <b>{show.name}</b>"
    )
    if show.year:
        message_text += f" ({show.year})"
    
    message_text += f"\n\n🎬 <b>Temporadas disponibles:</b>"
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_episodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, show_id: int, season_number: int):
    """Muestra menú de episodios de una temporada"""
    db = context.bot_data['db']
    query = update.callback_query
    await query.answer()
    
    # Obtener serie y episodios
    show = await db.get_tv_show_by_id(show_id)
    if not show:
        await query.edit_message_text("❌ Serie no encontrada.")
        return
    
    episodes = await db.get_episodes_by_season(show_id, season_number)
    if not episodes:
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver a temporadas", callback_data=f"series_{show_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ No hay episodios para Temporada {season_number}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Construir botones de episodios
    keyboard = []
    for episode in episodes:
        episode_title = f"{episode.season_number}x{episode.episode_number:02d}"
        if episode.title:
            episode_title += f" - {episode.title}"
        
        keyboard.append([
            InlineKeyboardButton(
                episode_title,
                callback_data=f"episode_{episode.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Volver a temporadas", callback_data=f"series_{show_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"📺 <b>{show.name}</b>\n"
        f"🎬 <b>Temporada {season_number}</b>\n\n"
        f"Selecciona un episodio:"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
