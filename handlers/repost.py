"""
Handler para re-publicar videos antiguos en canales nuevos
Comando: /repost
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS, VERIFICATION_CHANNEL_ID
from database.db_manager import DatabaseManager
import io
import requests as req
import asyncio

# Sesiones de repost activas
repost_sessions = {}

class RepostSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.target_channel_id = None
        self.mode = None  # 'all' o 'interval'
        self.interval = None  # segundos entre posts
        self.videos_to_post = []
        self.current_index = 0
        self.is_running = False
        self.task = None
        
    def cancel(self):
        self.is_running = False
        if self.task and not self.task.done():
            self.task.cancel()

async def repost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para re-publicar videos antiguos en un canal nuevo
    
    Uso: /repost
    """
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Cancelar sesión anterior si existe
    if user.id in repost_sessions:
        repost_sessions[user.id].cancel()
        del repost_sessions[user.id]
    
    # Crear nueva sesión
    session = RepostSession(user.id)
    repost_sessions[user.id] = session
    
    db = context.bot_data['db']
    
    # Obtener total de videos en BD
    try:
        # Contar videos indexados
        from sqlalchemy import select, func
        from database.models import Video
        
        async with db.async_session() as db_session:
            result = await db_session.execute(
                select(func.count(Video.id)).where(Video.tmdb_id.isnot(None))
            )
            total_videos = result.scalar()
        
        if total_videos == 0:
            await update.message.reply_text(
                "❌ No hay videos indexados en la base de datos.\n"
                "Usa /indexar primero."
            )
            del repost_sessions[user.id]
            return
        
    except Exception as e:
        print(f"Error contando videos: {e}")
        await update.message.reply_text(
            f"❌ Error al contar videos: {e}"
        )
        del repost_sessions[user.id]
        return
    
    # Mostrar menú inicial
    await update.message.reply_text(
        f"📢 <b>Re-publicación de Videos</b>\n\n"
        f"📊 Total de videos indexados: <b>{total_videos}</b>\n\n"
        f"Por favor, envíame el <b>ID del canal</b> donde quieres publicar.\n\n"
        f"💡 <i>Ejemplo:</i> <code>-1001234567890</code>\n\n"
        f"⚠️ El bot debe ser administrador en ese canal.",
        parse_mode='HTML'
    )

async def handle_repost_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el input del ID del canal"""
    user = update.effective_user
    
    # Si no hay usuario (mensaje de canal, etc.), ignorar
    if not user:
        return
    
    # Si no hay mensaje de texto, ignorar
    if not update.message or not update.message.text:
        return
    
    # Verificar si hay sesión activa
    if user.id not in repost_sessions:
        return
    
    session = repost_sessions[user.id]
    
    # Si ya tiene canal, ignorar
    if session.target_channel_id:
        return
    
    # Parsear ID del canal
    text = update.message.text.strip()
    
    if not text.lstrip('-').isdigit():
        await update.message.reply_text(
            "❌ ID inválido. Debe ser un número.\n"
            "Ejemplo: <code>-1001234567890</code>",
            parse_mode='HTML'
        )
        return
    
    channel_id = int(text)
    
    # Verificar que el bot tenga acceso al canal
    try:
        chat = await context.bot.get_chat(channel_id)
        
        # Verificar que el bot sea admin
        bot_member = await context.bot.get_chat_member(channel_id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                f"❌ El bot no es administrador en <b>{chat.title}</b>.\n\n"
                f"Agrégalo como administrador con permisos para publicar mensajes.",
                parse_mode='HTML'
            )
            return
        
        session.target_channel_id = channel_id
        
        # Preguntar modo de publicación
        keyboard = [
            [InlineKeyboardButton("🚀 Todos de una vez", callback_data="repost_mode_all")],
            [InlineKeyboardButton("⏱️ Con intervalo de tiempo", callback_data="repost_mode_interval")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="repost_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Canal seleccionado: <b>{chat.title}</b>\n\n"
            f"¿Cómo quieres publicar los videos?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error al verificar canal: {e}\n\n"
            f"Verifica que:\n"
            f"• El ID sea correcto\n"
            f"• El bot esté en el canal\n"
            f"• El bot sea administrador",
            parse_mode='HTML'
        )

async def handle_repost_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de repost"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in repost_sessions:
        await query.edit_message_text("❌ Sesión expirada. Usa /repost de nuevo.")
        return
    
    session = repost_sessions[user_id]
    data = query.data
    
    # Cancelar
    if data == "repost_cancel":
        session.cancel()
        del repost_sessions[user_id]
        await query.edit_message_text("❌ Re-publicación cancelada.")
        return
    
    # Modo: todos de una vez
    if data == "repost_mode_all":
        session.mode = 'all'
        await confirm_repost(query, context, session)
        return
    
    # Modo: con intervalo
    if data == "repost_mode_interval":
        session.mode = 'interval'
        
        keyboard = [
            [
                InlineKeyboardButton("30 seg", callback_data="repost_interval_30"),
                InlineKeyboardButton("1 min", callback_data="repost_interval_60")
            ],
            [
                InlineKeyboardButton("5 min", callback_data="repost_interval_300"),
                InlineKeyboardButton("10 min", callback_data="repost_interval_600")
            ],
            [
                InlineKeyboardButton("30 min", callback_data="repost_interval_1800"),
                InlineKeyboardButton("1 hora", callback_data="repost_interval_3600")
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="repost_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⏱️ Selecciona el intervalo entre publicaciones:",
            reply_markup=reply_markup
        )
        return
    
    # Seleccionar intervalo
    if data.startswith("repost_interval_"):
        interval = int(data.split("_")[2])
        session.interval = interval
        await confirm_repost(query, context, session)
        return
    
    # Confirmar inicio
    if data == "repost_confirm":
        await start_repost(query, context, session)
        return

async def confirm_repost(query, context, session):
    """Muestra confirmación antes de iniciar"""
    db = context.bot_data['db']
    
    # Obtener todos los videos
    try:
        from sqlalchemy import select
        from database.models import Video
        
        async with db.async_session() as db_session:
            result = await db_session.execute(
                select(Video).where(Video.tmdb_id.isnot(None)).order_by(Video.added_at)
            )
            videos = result.scalars().all()
        
        session.videos_to_post = videos
        
        if not videos:
            await query.edit_message_text("❌ No hay videos para publicar.")
            del repost_sessions[session.user_id]
            return
        
        # Calcular tiempo estimado
        total = len(videos)
        
        if session.mode == 'all':
            time_estimate = "unos minutos"
        else:
            total_seconds = total * session.interval
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            if hours > 0:
                time_estimate = f"{hours}h {minutes}min"
            else:
                time_estimate = f"{minutes}min"
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar y comenzar", callback_data="repost_confirm")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="repost_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        mode_text = "🚀 Todos de una vez" if session.mode == 'all' else f"⏱️ Cada {format_interval(session.interval)}"
        
        await query.edit_message_text(
            f"📊 <b>Resumen de Re-publicación</b>\n\n"
            f"📺 Total de videos: <b>{total}</b>\n"
            f"📢 Canal destino: <code>{session.target_channel_id}</code>\n"
            f"⚙️ Modo: {mode_text}\n"
            f"⏳ Tiempo estimado: ~{time_estimate}\n\n"
            f"¿Deseas continuar?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"Error en confirm_repost: {e}")
        await query.edit_message_text(f"❌ Error: {e}")
        del repost_sessions[session.user_id]

async def start_repost(query, context, session):
    """Inicia el proceso de re-publicación"""
    await query.edit_message_text(
        "🚀 <b>Re-publicación iniciada...</b>\n\n"
        f"📊 Videos a publicar: {len(session.videos_to_post)}\n"
        f"⚙️ Modo: {'Todos de una vez' if session.mode == 'all' else f'Cada {format_interval(session.interval)}'}\n\n"
        f"⏳ Por favor espera...",
        parse_mode='HTML'
    )
    
    session.is_running = True
    
    if session.mode == 'all':
        # Publicar todos de una vez
        session.task = asyncio.create_task(
            repost_all_videos(query, context, session)
        )
    else:
        # Publicar con intervalo
        session.task = asyncio.create_task(
            repost_videos_with_interval(query, context, session)
        )

async def repost_all_videos(query, context, session):
    """Publica todos los videos de una vez"""
    success = 0
    failed = 0
    
    for i, video in enumerate(session.videos_to_post):
        if not session.is_running:
            break
        
        try:
            await publish_video_to_channel(context, video, session.target_channel_id)
            success += 1
            
            # Actualizar progreso cada 10 videos
            if (i + 1) % 10 == 0:
                await query.edit_message_text(
                    f"🚀 <b>Publicando...</b>\n\n"
                    f"✅ Publicados: {success}\n"
                    f"❌ Errores: {failed}\n"
                    f"📊 Progreso: {i+1}/{len(session.videos_to_post)}",
                    parse_mode='HTML'
                )
            
        except Exception as e:
            print(f"Error publicando video {video.id}: {e}")
            failed += 1
        
        # Pequeña pausa para no sobrecargar Telegram
        await asyncio.sleep(1)
    
    # Resumen final
    await query.edit_message_text(
        f"✅ <b>Re-publicación completada</b>\n\n"
        f"✅ Publicados exitosamente: <b>{success}</b>\n"
        f"❌ Errores: <b>{failed}</b>\n"
        f"📊 Total: {len(session.videos_to_post)}",
        parse_mode='HTML'
    )
    
    # Limpiar sesión
    if session.user_id in repost_sessions:
        del repost_sessions[session.user_id]

async def repost_videos_with_interval(query, context, session):
    """Publica videos con intervalo de tiempo"""
    success = 0
    failed = 0
    total = len(session.videos_to_post)
    
    for i, video in enumerate(session.videos_to_post):
        if not session.is_running:
            await query.edit_message_text(
                f"🛑 <b>Re-publicación detenida</b>\n\n"
                f"✅ Publicados: {success}\n"
                f"❌ Errores: {failed}",
                parse_mode='HTML'
            )
            break
        
        try:
            await publish_video_to_channel(context, video, session.target_channel_id)
            success += 1
            
        except Exception as e:
            print(f"Error publicando video {video.id}: {e}")
            failed += 1
        
        # Actualizar progreso
        remaining = total - (i + 1)
        time_left = format_interval(remaining * session.interval) if remaining > 0 else "0s"
        
        await query.edit_message_text(
            f"⏱️ <b>Publicando con intervalo...</b>\n\n"
            f"✅ Publicados: {success}\n"
            f"❌ Errores: {failed}\n"
            f"📊 Progreso: {i+1}/{total}\n"
            f"⏳ Tiempo restante: ~{time_left}\n\n"
            f"🎬 Último: <i>{video.title}</i>",
            parse_mode='HTML'
        )
        
        # Esperar intervalo (excepto en el último)
        if i < total - 1 and session.is_running:
            await asyncio.sleep(session.interval)
    
    # Resumen final
    if session.is_running:
        await query.edit_message_text(
            f"✅ <b>Re-publicación completada</b>\n\n"
            f"✅ Publicados exitosamente: <b>{success}</b>\n"
            f"❌ Errores: <b>{failed}</b>\n"
            f"📊 Total: {total}",
            parse_mode='HTML'
        )
    
    # Limpiar sesión
    if session.user_id in repost_sessions:
        del repost_sessions[session.user_id]

async def publish_video_to_channel(context, video, channel_id):
    """Publica un video en el canal especificado"""
    # Descargar poster
    if not video.poster_url:
        raise Exception("Video sin poster")
    
    response = req.get(video.poster_url, timeout=10)
    response.raise_for_status()
    photo_bytes = response.content
    
    # Crear caption
    title = video.title or "Sin título"
    year = video.year or "N/A"
    rating = video.vote_average / 10 if video.vote_average else 0
    overview = video.overview or ""
    
    if len(overview) > 200:
        overview = overview[:197] + "..."
    
    caption = (
        f"🎬 <b>{title}</b> ({year})\n"
        f"⭐ {rating:.1f}/10\n\n"
        f"{overview}"
    )
    
    # Crear botón de deep link
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{context.bot.username}?start=video_{video.message_id}")
    ]])
    
    # Publicar
    photo = io.BytesIO(photo_bytes)
    photo.name = "poster.jpg"
    
    await context.bot.send_photo(
        chat_id=channel_id,
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard
    )

def format_interval(seconds):
    """Formatea segundos en texto legible"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}min"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}min"
        return f"{hours}h"
