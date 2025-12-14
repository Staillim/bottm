from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.verification import is_user_member
from config.settings import VERIFICATION_CHANNEL_USERNAME
from handlers.tickets import process_referral_start, check_and_reward_referral

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    # DEBUG: Log para ver qué args llegan
    print(f"🔍 /start llamado por user {user.id}")
    print(f"🔍 context.args: {context.args}")
    
    # Registrar o actualizar usuario
    db_user = await db.get_user(user.id)
    is_new_user = db_user is None
    if not db_user:
        await db.add_user(user.id, user.username, user.first_name)
    
    # Verificar si viene desde un deep link
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        print(f"🔍 Deep link detectado: {arg}")
        
        # Procesar link de referido: ref_USER_ID
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.split("_")[1])
                print(f"👥 Link de referido detectado: {referrer_id}")
                if is_new_user:
                    await process_referral_start(update, context, referrer_id)
            except Exception as e:
                print(f"Error procesando referido: {e}")
            # Continuar con el flujo normal después de procesar el referido
        
        elif arg.startswith("video_"):
            video_msg_id = int(arg.split("_")[1])
            print(f"🎬 Procesando video con message_id: {video_msg_id}")
            
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
            print(f"✅ Usuario verificado, enviando video...")
            await send_video_by_message_id(update, context, video_msg_id, user.id)
            return
    
    # Verificar si viene desde un deep link de serie (botón "Ver Ahora" de serie)
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        
        if arg.startswith("series_"):
            series_id = int(arg.split("_")[1])
            print(f"📺 Procesando serie con ID: {series_id}")
            
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
            
            # Obtener serie y temporadas
            show = await db.get_tv_show_by_id(series_id)
            if not show:
                await update.message.reply_text("❌ Serie no encontrada.")
                return
            
            seasons = await db.get_seasons_for_show(series_id)
            if not seasons:
                await update.message.reply_text(
                    f"❌ No hay episodios disponibles para <b>{show.name}</b>",
                    parse_mode='HTML'
                )
                return
            
            # Guardar estado del usuario
            await db.set_user_state(user.id, "series_seasons", series_id)
            
            # Construir botones de temporadas
            keyboard = []
            for season_number, episode_count in seasons:
                keyboard.append([
                    InlineKeyboardButton(
                        f"Temporada {season_number} ({episode_count} episodios)",
                        callback_data=f"season_{series_id}_{season_number}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Volver a series", callback_data="menu_series")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = f"📺 <b>{show.name}</b>"
            if show.year:
                message_text += f" ({show.year})"
            message_text += f"\n\n🎬 <b>Temporadas disponibles:</b>"
            
            print(f"✅ Enviando menú de temporadas para {show.name}")
            await update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
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
    """Envía Mini App con anuncio o directo si tiene tickets"""
    db = context.bot_data['db']
    
    try:
        # Usar método existente optimizado
        print(f"\n🔍 DEBUG send_video_by_message_id:")
        print(f"   Buscando video con message_id: {video_msg_id}")
        video = await db.get_video_by_message_id(video_msg_id)
        print(f"   Resultado: {video.title if video else 'None'}")
        
        if not video:
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "❌ Video no encontrado.\n\n"
                    "Puede que haya sido eliminado o no esté disponible."
                )
            return
    except Exception as e:
        print(f"Error buscando video: {e}")
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "❌ Error al buscar el video. Por favor intenta más tarde."
            )
        return

    # Verificar si el usuario tiene tickets disponibles
    user_tickets = await db.get_user_tickets(user_id)
    has_tickets = user_tickets and user_tickets.tickets > 0
    tickets_count = user_tickets.tickets if user_tickets else 0

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
    print(f"   Tickets disponibles: {tickets_count}")
    print(f"   URL: {webapp_url[:100]}...")

    # Crear botones según si tiene tickets
    keyboard = []
    
    if has_tickets:
        # Opción de usar ticket (sin anuncio)
        keyboard.append([
            InlineKeyboardButton(
                f"🎟️ Usar Ticket ({tickets_count} disponibles)",
                callback_data=f"use_ticket_movie_{video.id}"
            )
        ])
    
    # Siempre mostrar opción con anuncio
    keyboard.append([
        InlineKeyboardButton(
            "📺 Ver con Anuncio",
            web_app=WebAppInfo(url=webapp_url)
        )
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Mensaje informativo
    if has_tickets:
        message_text = (
            f"🎬 <b>{video.title}</b>\n\n"
            f"🎟️ Tienes <b>{tickets_count} tickets</b> disponibles.\n"
            f"Puedes usar 1 ticket para ver sin anuncios.\n\n"
            f"👇 Selecciona una opción:"
        )
    else:
        message_text = f"🎬 <b>{video.title}</b>\n\n👇 Presiona el botón para ver la película:"

    # Determinar cómo enviar el mensaje
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        await context.bot.send_message(
            chat_id=user_id,
            text=message_text,
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
            
            # Verificar y recompensar referido si aplica
            reward_result = await check_and_reward_referral(user.id, db)
            if reward_result:
                referrer_id, tickets = reward_result
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 <b>¡Felicidades!</b>\n\n"
                             f"Tu referido <b>{user.first_name}</b> se verificó.\n"
                             f"Recibiste <b>+{tickets} tickets</b> 🎟️\n\n"
                             f"Usa /mistickets para ver tu balance.",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"Error notificando referrer: {e}")
            
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
