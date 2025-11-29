from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.verification import is_user_member

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    # Verificar membresía
    if not await is_user_member(user.id, context):
        await update.message.reply_text(
            "❌ Debes estar verificado para usar este comando.\n"
            "Usa /start para verificarte."
        )
        return
    
    # Obtener término de búsqueda
    if not context.args:
        await update.message.reply_text(
            "❓ Uso: /buscar <término de búsqueda>\n"
            "Ejemplo: /buscar tutorial python"
        )
        return
    
    query = " ".join(context.args)
    
    # Buscar en la base de datos
    videos = await db.search_videos(query)
    
    if not videos:
        await update.message.reply_text(
            f"😔 No se encontraron resultados para: '{query}'\n\n"
            f"Intenta con otros términos de búsqueda."
        )
        return
    
    # Registrar búsqueda
    await db.log_search(user.id, query, len(videos))
    
    # Crear botones con resultados
    keyboard = []
    text = f"🔍 Resultados para: *{query}*\n\n"
    
    for idx, video in enumerate(videos, 1):
        text += f"{idx}. {video.title}\n"
        keyboard.append([
            InlineKeyboardButton(
                f"📹 {idx}. {video.title[:50]}...",
                callback_data=f"video_{video.id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Obtener ID del video
    video_id = int(query.data.split('_')[1])
    db = context.bot_data['db']
    
    video = await db.get_video_by_id(video_id)
    
    if not video:
        await query.edit_message_text("❌ Video no encontrado.")
        return
    
    # Crear token de anuncio
    from config.settings import BOT_USERNAME, WEBAPP_URL, API_SERVER_URL
    import urllib.parse
    
    token = await db.create_ad_token(query.from_user.id, video.id)
    
    # Preparar parámetros para la Mini App
    title_encoded = urllib.parse.quote(video.title)
    poster_encoded = urllib.parse.quote(video.poster_url or "https://via.placeholder.com/300x450?text=Sin+Poster")
    api_url_encoded = urllib.parse.quote(API_SERVER_URL)
    
    webapp_url = f"{WEBAPP_URL}?token={token}&title={title_encoded}&poster={poster_encoded}&api_url={api_url_encoded}"
    
    # Enviar mensaje con botón de Mini App
    keyboard = [[
        InlineKeyboardButton(
            "📺 Ver Anuncio para Continuar",
            web_app={"url": webapp_url}
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎬 <b>{video.title}</b>\n\n"
        f"Para ver esta película, primero debes ver un anuncio corto.\n\n"
        f"👇 Toca el botón de abajo para continuar:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
