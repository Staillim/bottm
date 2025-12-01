from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.verification import is_user_member
from config.settings import VERIFICATION_CHANNEL_USERNAME

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    # Registrar o actualizar usuario
    db_user = await db.get_user(user.id)
    if not db_user:
        await db.add_user(user.id, user.username, user.first_name)
    
    # Verificar si viene desde un deep link (botón "Ver Ahora")
    if context.args and context.args[0].startswith("video_"):
        video_msg_id = int(context.args[0].split("_")[1])
        
        # Verificar membresía primero
        if not await is_user_member(user.id, context):
            keyboard = [
                [InlineKeyboardButton("✅ Unirse al Canal", url=f"https://t.me/{VERIFICATION_CHANNEL_USERNAME.strip('@')}")],
                [InlineKeyboardButton("🔄 Verificar y Ver Video", callback_data=f"verify_video_{video_msg_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ Primero debes unirte al canal para ver este video.\n\n"
                f"Únete a {VERIFICATION_CHANNEL_USERNAME} y presiona verificar.",
                reply_markup=reply_markup
            )
            return
        
        # Usuario verificado - buscar y enviar video
        await send_video_by_message_id(update, context, video_msg_id, user.id)
        return
    
    # Verificar si viene desde un deep link de serie (botón "Ver Ahora" de serie)
    if context.args and context.args[0].startswith("series_"):
        series_id = int(context.args[0].split("_")[1])
        
        # Verificar membresía primero
        if not await is_user_member(user.id, context):
            keyboard = [
                [InlineKeyboardButton("✅ Unirse al Canal", url=f"https://t.me/{VERIFICATION_CHANNEL_USERNAME.strip('@')}")],
                [InlineKeyboardButton("🔄 Verificar Membresía", callback_data="verify_membership")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ Primero debes unirte al canal para ver esta serie.\n\n"
                f"Únete a {VERIFICATION_CHANNEL_USERNAME} y presiona verificar.",
                reply_markup=reply_markup
            )
            return
        
        # Usuario verificado - actualizar verificación
        await db.update_user_verification(user.id, True)
        
        # Mostrar la serie directamente
        from handlers.callbacks import show_series_details
        
        # Crear un objeto falso de query para reutilizar la función
        class FakeQuery:
            def __init__(self, message, data):
                self.message = message
                self.data = data
                self.from_user = message.from_user
            
            async def answer(self):
                pass
            
            async def edit_message_text(self, text, **kwargs):
                await self.message.reply_text(text, **kwargs)
        
        fake_query = FakeQuery(update.message, f"series_{series_id}")
        fake_update = Update(update.update_id, message=update.message)
        fake_update.callback_query = fake_query
        
        await show_series_details(fake_update, context, series_id)
        return
    
    # Verificar membresía
    is_member = await is_user_member(user.id, context)
    
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("✅ Unirse al Canal", url=f"https://t.me/{VERIFICATION_CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("🔄 Verificar Membresía", callback_data="verify_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 ¡Hola {user.first_name}!\n\n"
            f"Para usar este bot, debes unirte a nuestro canal oficial:\n"
            f"{VERIFICATION_CHANNEL_USERNAME}\n\n"
            f"Una vez que te hayas unido, presiona el botón de verificación.",
            reply_markup=reply_markup
        )
    else:
        await db.update_user_verification(user.id, True)
        
        # Mostrar menú interactivo de películas/series
        from handlers.menu import main_menu
        await main_menu(update, context)

async def send_video_by_message_id(update, context, video_msg_id, user_id):
    """Envía Mini App con anuncio cuando viene desde canal"""
    db = context.bot_data['db']
    
    try:
        # Usar método existente optimizado
        video = await db.get_video_by_message_id(video_msg_id)
        
        if not video:
            await update.message.reply_text(
                "❌ Video no encontrado.\n\n"
                "Puede que haya sido eliminado o no esté disponible."
            )
            return
    except Exception as e:
        print(f"Error buscando video: {e}")
        await update.message.reply_text(
            "❌ Error al buscar el video. Por favor intenta más tarde."
        )
        return
    
    # Sistema nuevo: user_id + video_id (sin tokens)
    from config.settings import WEBAPP_URL, API_SERVER_URL
    from telegram import WebAppInfo
    import urllib.parse
    
    # Preparar parámetros para la Mini App
    title_encoded = urllib.parse.quote(video.title)
    poster_encoded = urllib.parse.quote(video.poster_url or "https://via.placeholder.com/300x450?text=Sin+Poster")
    api_url_encoded = urllib.parse.quote(API_SERVER_URL)
    
    # Usar user_id y video_id directamente (sin tokens)
    # IMPORTANTE: Usar video.id (ID de base de datos), NO video_msg_id (ID de mensaje en canal)
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}&video_id={video.id}&title={title_encoded}&poster={poster_encoded}&api_url={api_url_encoded}&content_type=movie"
    
    print(f"📱 Abriendo Mini App desde deep link:")
    print(f"   User: {user_id}")
    print(f"   Video DB ID: {video.id} (Msg ID: {video_msg_id})")
    print(f"   URL: {webapp_url[:100]}...")
    
    # Enviar mensaje con botón de Mini App
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [[
        InlineKeyboardButton(
            "🎬 Ver Anuncio para Continuar",
            web_app=WebAppInfo(url=webapp_url)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎬 <b>{video.title}</b>\n\n"
        f"Para ver esta película, primero debes ver un anuncio corto.\n\n"
        f"👇 Toca el botón de abajo para continuar:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def send_episode_by_id(update, context, episode_id, user_id):
    """Envía episodio con Mini App cuando viene desde verificación"""
    db = context.bot_data['db']
    
    try:
        # Obtener episodio
        episode = await db.get_episode_by_id(episode_id)
        
        if not episode:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Episodio no encontrado.\n\n"
                     "Puede que haya sido eliminado o no esté disponible."
            )
            return
        
        # Obtener serie
        show = await db.get_tv_show_by_id(episode.tv_show_id)
        
        if not show:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Serie no encontrada."
            )
            return
            
    except Exception as e:
        print(f"Error buscando episodio: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Error al buscar el episodio. Por favor intenta más tarde."
        )
        return
    
    # Sistema nuevo: user_id + video_id (sin tokens)
    from config.settings import WEBAPP_URL, API_SERVER_URL
    from telegram import WebAppInfo
    import urllib.parse
    
    # Preparar parámetros para la Mini App
    episode_title = f"{show.name} - {episode.season_number}x{episode.episode_number:02d}"
    if episode.title:
        episode_title += f" - {episode.title}"
    
    title_encoded = urllib.parse.quote(episode_title)
    poster_encoded = urllib.parse.quote(show.poster_url or "https://via.placeholder.com/300x450?text=Sin+Poster")
    api_url_encoded = urllib.parse.quote(API_SERVER_URL)
    
    # Usar user_id y episode_id directamente
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}&video_id={episode.id}&title={title_encoded}&poster={poster_encoded}&api_url={api_url_encoded}&content_type=episode"
    
    print(f"📱 Abriendo Mini App para episodio:")
    print(f"   User: {user_id}")
    print(f"   Episode DB ID: {episode.id}")
    print(f"   URL: {webapp_url[:100]}...")
    
    # Enviar mensaje con botón de Mini App
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    
    keyboard = [[
        InlineKeyboardButton(
            "📺 Ver Anuncio para Continuar",
            web_app=WebAppInfo(url=webapp_url)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"📺 <b>{episode_title}</b>\n\n"
             f"Para ver este episodio, primero debes ver un anuncio corto.\n\n"
             f"👇 Toca el botón de abajo para continuar:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    db = context.bot_data['db']
    
    # Verificar si viene desde "Ver Ahora" (película)
    if query.data.startswith("verify_video_"):
        video_msg_id = int(query.data.split("_")[2])
        
        is_member = await is_user_member(user.id, context)
        
        if is_member:
            await db.update_user_verification(user.id, True)
            await query.edit_message_text("✅ Verificado! Enviando película...")
            
            # Enviar el video
            await send_video_by_message_id(query, context, video_msg_id, user.id)
        else:
            await query.edit_message_text(
                "❌ Aún no te has unido al canal.\n"
                "Por favor únete primero y vuelve a presionar el botón."
            )
        return
    
    # Verificar si viene desde "Ver Ahora" (episodio)
    if query.data.startswith("verify_episode_"):
        episode_id = int(query.data.split("_")[2])
        
        is_member = await is_user_member(user.id, context)
        
        if is_member:
            await db.update_user_verification(user.id, True)
            await query.edit_message_text("✅ Verificado! Enviando episodio...")
            
            # Enviar el episodio
            await send_episode_by_id(query, context, episode_id, user.id)
        else:
            await query.edit_message_text(
                "❌ Aún no te has unido al canal.\n"
                "Por favor únete primero y vuelve a presionar el botón."
            )
        return
    
    # Verificación normal
    is_member = await is_user_member(user.id, context)
    
    if is_member:
        await db.update_user_verification(user.id, True)
        await query.edit_message_text(
            f"✅ ¡Verificación exitosa!\n\n"
            f"Ahora puedes usar el bot para buscar videos.\n\n"
            f"Usa /buscar <término> para comenzar."
        )
    else:
        await query.edit_message_text(
            f"❌ Aún no eres miembro del canal.\n\n"
            f"Por favor únete primero y luego presiona verificar nuevamente.",
            reply_markup=query.message.reply_markup
        )
