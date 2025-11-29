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
        await update.message.reply_text(
            f"✅ ¡Bienvenido {user.first_name}!\n\n"
            f"Ya estás verificado. Puedes comenzar a buscar videos.\n\n"
            f"📝 Comandos disponibles:\n"
            f"/buscar <término> - Buscar videos\n"
            f"/search <término> - Search videos\n"
            f"/help - Ver ayuda completa"
        )

async def send_video_by_message_id(update, context, video_msg_id, user_id):
    """Envía video completo con ficha cuando viene desde canal"""
    db = context.bot_data['db']
    
    # Buscar video por message_id
    videos = await db.search_videos("", limit=10000)
    video = None
    for v in videos:
        if v.message_id == video_msg_id:
            video = v
            break
    
    if not video:
        await update.message.reply_text("❌ Video no encontrado.")
        return
    
    # Enviar ficha con poster si tiene metadata
    if video.poster_url:
        try:
            import io
            import requests as req
            
            response = req.get(video.poster_url, timeout=10)
            response.raise_for_status()
            photo = io.BytesIO(response.content)
            photo.name = "poster.jpg"
            
            caption = f"🎬 <b>{video.title}</b>\n"
            if video.year:
                caption += f"📅 {video.year}\n"
            if video.vote_average:
                caption += f"⭐ {video.vote_average/10:.1f}/10\n"
            if video.runtime:
                caption += f"⏱️ {video.runtime} min\n"
            if video.genres:
                caption += f"🎭 {video.genres}\n"
            if video.overview:
                caption += f"\n📝 {video.overview}\n"
            
            await context.bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=caption,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error enviando poster: {e}")
    
    # Enviar video
    caption_text = f"📹 *{video.title}*"
    await context.bot.send_video(
        chat_id=user_id,
        video=video.file_id,
        caption=caption_text,
        parse_mode='Markdown'
    )

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    db = context.bot_data['db']
    
    # Verificar si viene desde "Ver Ahora"
    if query.data.startswith("verify_video_"):
        video_msg_id = int(query.data.split("_")[2])
        
        is_member = await is_user_member(user.id, context)
        
        if is_member:
            await db.update_user_verification(user.id, True)
            await query.edit_message_text("✅ Verificado! Enviando video...")
            
            # Enviar el video
            await send_video_by_message_id(query, context, video_msg_id, user.id)
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
