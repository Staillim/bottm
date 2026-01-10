"""
Sistema de broadcast para enviar mensajes a usuarios
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from config.settings import ADMIN_IDS, VERIFICATION_CHANNEL_ID, VERIFICATION_CHANNEL_USERNAME
import logging
import asyncio

db = DatabaseManager()
logger = logging.getLogger(__name__)

# Storage temporal para estados de broadcast
broadcast_sessions = {}

class BroadcastSession:
    """Clase para gestionar sesión de broadcast"""
    def __init__(self, admin_id):
        self.admin_id = admin_id
        self.message_type = None  # 'welcome', 'thanks', 'custom'
        self.custom_message = None
        self.custom_video = None  # Para almacenar video
        self.custom_photo = None  # Para almacenar foto
        self.custom_audio = None  # Para almacenar audio
        self.custom_document = None  # Para almacenar documento
        self.custom_buttons = []
        self.awaiting_custom = False
        self.awaiting_video = False  # Estado para recibir multimedia
        self.awaiting_button_text = False
        self.awaiting_button_url = False
        self.current_button_text = None

async def broadcast_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /broadcast - Muestra menú de mensajes broadcast
    """
    user_id = update.effective_user.id
    
    # Verificar si es admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    keyboard = [
        [InlineKeyboardButton("👋 Mensaje de Bienvenida", callback_data="broadcast_welcome")],
        [InlineKeyboardButton("🙏 Mensaje de Agradecimiento", callback_data="broadcast_thanks")],
        [InlineKeyboardButton("✍️ Mensaje Personalizado", callback_data="broadcast_custom")],
        [InlineKeyboardButton("🗑️ Eliminar Mensajes", callback_data="broadcast_delete")],
        [InlineKeyboardButton("📊 Ver Estadísticas", callback_data="broadcast_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📢 <b>Sistema de Broadcast</b>\n\n"
        "Selecciona el tipo de mensaje a enviar a todos los usuarios:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks del sistema de broadcast"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "broadcast_welcome":
        await send_welcome_broadcast(update, context)
    elif data == "broadcast_thanks":
        await send_thanks_broadcast(update, context)
    elif data == "broadcast_custom":
        await request_custom_message(update, context)

    elif data == "broadcast_delete":
        await request_delete_broadcast(update, context)
    elif data == "broadcast_delete_confirm":
        await confirm_delete_broadcast(update, context)
    elif data == "broadcast_stats":
        await show_broadcast_stats(update, context)
    elif data == "broadcast_add_button":
        await add_button_prompt(update, context)
    elif data == "broadcast_add_media":
        await add_media_prompt(update, context)
    elif data == "broadcast_add_text":
        await add_text_prompt(update, context)
    elif data == "broadcast_skip_buttons":
        await skip_buttons_and_preview(update, context)
    elif data == "broadcast_confirm":
        await confirm_broadcast(update, context)
    elif data == "broadcast_cancel":
        await cancel_broadcast(update, context)
    elif data == "broadcast_back":
        # Volver al menú principal
        keyboard = [
            [InlineKeyboardButton("👋 Mensaje de Bienvenida", callback_data="broadcast_welcome")],
            [InlineKeyboardButton("🙏 Mensaje de Agradecimiento", callback_data="broadcast_thanks")],
            [InlineKeyboardButton("✍️ Mensaje Personalizado", callback_data="broadcast_custom")],
            [InlineKeyboardButton("🗑️ Eliminar Mensajes", callback_data="broadcast_delete")],
            [InlineKeyboardButton("📊 Ver Estadísticas", callback_data="broadcast_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 <b>Sistema de Broadcast</b>\n\n"
            "Selecciona el tipo de mensaje a enviar a todos los usuarios:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def send_welcome_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía mensaje de bienvenida interactivo a todos los usuarios"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Crear sesión
    session = BroadcastSession(user_id)
    session.message_type = 'welcome'
    broadcast_sessions[user_id] = session
    
    # Preview del mensaje
    preview_text = (
        "👋 <b>¡Hola! ¿Estás aburrido?</b>\n\n"
        "¿Qué quieres ver hoy? Tenemos varias opciones para ti:\n\n"
        "🔍 Usa /buscar para encontrar películas o series\n"
        "📺 Visita nuestro canal de verificación para ver el catálogo completo\n"
        "💡 ¿No encuentras algo? ¡Solicita una nueva película o serie!\n\n"
        "¡Disfruta! 🍿"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Enviar a todos", callback_data="broadcast_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📝 <b>Preview del Mensaje:</b>\n\n{preview_text}\n\n"
        "¿Deseas enviar este mensaje a todos los usuarios?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def send_thanks_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía mensaje de agradecimiento a todos los usuarios"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Crear sesión
    session = BroadcastSession(user_id)
    session.message_type = 'thanks'
    broadcast_sessions[user_id] = session
    
    # Preview del mensaje
    preview_text = (
        "🙏 <b>¡Gracias por usar CineStelar!</b>\n\n"
        "Esperamos que hayas disfrutado tu película o serie. "
        "Tu apoyo nos motiva a seguir mejorando.\n\n"
        "Si tienes alguna sugerencia o quieres solicitar contenido, "
        "¡no dudes en contactarnos!\n\n"
        "🌟 ¡Hasta la próxima! 🌟"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Enviar a todos", callback_data="broadcast_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📝 <b>Preview del Mensaje:</b>\n\n{preview_text}\n\n"
        "¿Deseas enviar este mensaje a todos los usuarios?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def request_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita mensaje personalizado al admin"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Crear sesión
    session = BroadcastSession(user_id)
    session.message_type = 'custom'
    session.awaiting_custom = True
    broadcast_sessions[user_id] = session
    
    await query.edit_message_text(
        "✍️ <b>Mensaje Personalizado - Paso 1/2</b>\n\n"
        "Escribe el mensaje que deseas enviar a todos los usuarios.\n\n"
        "Puedes usar HTML para formato:\n"
        "• <code>&lt;b&gt;texto&lt;/b&gt;</code> para <b>negrita</b>\n"
        "• <code>&lt;i&gt;texto&lt;/i&gt;</code> para <i>cursiva</i>\n"
        "• <code>&lt;code&gt;texto&lt;/code&gt;</code> para <code>código</code>\n\n"
        "Luego podrás agregar botones (opcional).\n\n"
        "Envía /cancelar para cancelar.",
        parse_mode='HTML'
    )

async def handle_custom_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el input del mensaje personalizado y botones"""
    user_id = update.effective_user.id
    
    # Verificar si hay sesión activa
    session = broadcast_sessions.get(user_id)
    if not session:
        return False
    
    # Verificar cancelación
    if update.message and update.message.text == "/cancelar":
        del broadcast_sessions[user_id]
        await update.message.reply_text("❌ Broadcast cancelado.")
        return True
    
    # Estado 1: Esperando multimedia
    if session.awaiting_video:
        media_type = None
        media_id = None
        media_emoji = None
        
        if update.message.video:
            session.custom_video = update.message.video.file_id
            media_type = "video"
            media_emoji = "🎥"
        elif update.message.photo:
            session.custom_photo = update.message.photo[-1].file_id  # Obtener la foto de mayor calidad
            media_type = "foto"
            media_emoji = "📷"
        elif update.message.audio:
            session.custom_audio = update.message.audio.file_id
            media_type = "audio"
            media_emoji = "🎵"
        elif update.message.document:
            session.custom_document = update.message.document.file_id
            media_type = "documento"
            media_emoji = "📄"
        
        if media_type:
            session.awaiting_video = False
            
            # Si ya hay mensaje, ir a preview
            if session.custom_message:
                # Preguntar si quiere agregar botones
                keyboard = [
                    [InlineKeyboardButton("➕ Agregar Botón", callback_data="broadcast_add_button")],
                    [InlineKeyboardButton("🎥 Cambiar Multimedia", callback_data="broadcast_add_media")],
                    [InlineKeyboardButton("✅ Continuar sin botones", callback_data="broadcast_skip_buttons")],
                    [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"{media_emoji} <b>{media_type.capitalize()} agregado al mensaje!</b>\n\n"
                    f"📝 <b>Mensaje actual:</b>\n{session.custom_message}\n\n"
                    "¿Deseas agregar botones al mensaje?",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                # Si no hay mensaje previo, preguntar si quiere agregar texto
                keyboard = [
                    [InlineKeyboardButton("✍️ Agregar Texto", callback_data="broadcast_add_text")],
                    [InlineKeyboardButton("➕ Agregar Botón", callback_data="broadcast_add_button")],
                    [InlineKeyboardButton("🔄 Cambiar Multimedia", callback_data="broadcast_add_media")],
                    [InlineKeyboardButton("✅ Enviar Solo Multimedia", callback_data="broadcast_skip_buttons")],
                    [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"{media_emoji} <b>{media_type.capitalize()} guardado!</b>\n\n"
                    "¿Qué deseas hacer ahora?",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                "❌ Por favor, envía un archivo multimedia válido:\n"
                "📹 Video, 📷 Foto, 🎵 Audio o 📄 Documento\n\n"
                "Envía /cancelar para cancelar el broadcast."
            )
        return True
    
    # Estado 2: Esperando mensaje de texto
    if session.awaiting_custom:
        message_text = update.message.text if update.message and update.message.text else None
        
        # Si no hay texto, verificar si está intentando cancelar o hacer skip
        if not message_text:
            # Si no hay texto y no es un comando, ignorar este mensaje
            return True
        
        # Permitir skip si hay cualquier tipo de multimedia
        has_media = any([session.custom_video, session.custom_photo, session.custom_audio, session.custom_document])
        if message_text == "/skip" and has_media:
            session.custom_message = ""
        else:
            session.custom_message = message_text
            
        session.awaiting_custom = False
        
        # Determinar si ya hay multimedia
        media_buttons = []
        if has_media:
            media_buttons.append([InlineKeyboardButton("🔄 Cambiar Multimedia", callback_data="broadcast_add_media")])
        else:
            media_buttons.append([InlineKeyboardButton("🎥 Agregar Video/Multimedia", callback_data="broadcast_add_media")])
        
        # Preguntar si quiere agregar botones o multimedia
        keyboard = [
            [InlineKeyboardButton("➕ Agregar Botón", callback_data="broadcast_add_button")],
            *media_buttons,
            [InlineKeyboardButton("✅ Continuar sin botones", callback_data="broadcast_skip_buttons")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        preview_text = f"📝 <b>Mensaje guardado:</b>\n\n{message_text}\n\n"
        
        # Determinar qué tipo de multimedia hay
        if session.custom_video:
            preview_text = f"🎥 <b>Video + Mensaje guardados!</b>\n\n📝 <b>Texto:</b>\n{message_text}\n\n"
        elif session.custom_photo:
            preview_text = f"📷 <b>Foto + Mensaje guardados!</b>\n\n📝 <b>Texto:</b>\n{message_text}\n\n"
        elif session.custom_audio:
            preview_text = f"🎵 <b>Audio + Mensaje guardados!</b>\n\n📝 <b>Texto:</b>\n{message_text}\n\n"
        elif session.custom_document:
            preview_text = f"📄 <b>Documento + Mensaje guardados!</b>\n\n📝 <b>Texto:</b>\n{message_text}\n\n"
        
        await update.message.reply_text(
            f"{preview_text}"
            "¿Deseas agregar botones al mensaje?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return True
    
    # Estado 2: Esperando texto del botón
    elif session.awaiting_button_text:
        session.current_button_text = message_text
        session.awaiting_button_text = False
        session.awaiting_button_url = True
        
        await update.message.reply_text(
            f"🔗 <b>Texto del botón:</b> {message_text}\n\n"
            "Ahora envía la URL del botón:\n"
            "(Debe empezar con http:// o https://)\n\n"
            "Ejemplos:\n"
            "• https://t.me/tu_canal\n"
            "• https://ejemplo.com\n\n"
            "Envía /cancelar para cancelar.",
            parse_mode='HTML'
        )
        return True
    
    # Estado 3: Esperando URL del botón
    elif session.awaiting_button_url:
        # Validar URL
        if not message_text.startswith(('http://', 'https://')):
            await update.message.reply_text(
                "❌ URL inválida. Debe empezar con http:// o https://\n"
                "Intenta de nuevo o envía /cancelar"
            )
            return True
        
        # Guardar botón
        session.custom_buttons.append({
            'text': session.current_button_text,
            'url': message_text
        })
        session.awaiting_button_url = False
        session.current_button_text = None
        
        # Preguntar si quiere más botones
        buttons_preview = "\n".join([f"• {btn['text']} → {btn['url']}" for btn in session.custom_buttons])
        
        keyboard = [
            [InlineKeyboardButton("➕ Agregar otro botón", callback_data="broadcast_add_button")],
            [InlineKeyboardButton("✅ Finalizar y enviar", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ <b>Botón agregado!</b>\n\n"
            f"<b>Botones actuales:</b>\n{buttons_preview}\n\n"
            "¿Qué deseas hacer?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return True
    
    return False

async def add_button_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita texto para un nuevo botón"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    session = broadcast_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión expirada. Usa /broadcast nuevamente.")
        return
    
    session.awaiting_button_text = True
    
    await query.edit_message_text(
        "🔤 <b>Agregar Botón - Paso 1/2</b>\n\n"
        "Envía el texto que aparecerá en el botón.\n\n"
        "Ejemplos:\n"
        "• 🔍 Buscar Películas\n"
        "• 📺 Ver Canal\n"
        "• 💬 Contactar Soporte\n\n"
        "Envía /cancelar para cancelar.",
        parse_mode='HTML'
    )

async def skip_buttons_and_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Salta la adición de botones y muestra preview final"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    session = broadcast_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión expirada. Usa /broadcast nuevamente.")
        return
    
    # Mostrar preview final
    keyboard = [
        [InlineKeyboardButton("✅ Enviar a todos", callback_data="broadcast_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📝 <b>Preview del Mensaje:</b>\n\n{session.custom_message}\n\n"
        "¿Deseas enviar este mensaje a todos los usuarios?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y ejecuta el broadcast"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        logger.info(f"Iniciando broadcast para user {user_id}")
        
        session = broadcast_sessions.get(user_id)
        if not session:
            logger.warning(f"No hay sesión para user {user_id}")
            await query.edit_message_text("❌ Sesión expirada. Usa /broadcast nuevamente.")
            return
        
        logger.info(f"Sesión encontrada, tipo: {session.message_type}")
        
        # Obtener todos los usuarios primero
        try:
            logger.info("Obteniendo lista de usuarios...")
            users = await db.get_all_users()
            total_users = len(users)
            logger.info(f"Usuarios encontrados: {total_users}")
            
            if total_users == 0:
                await query.edit_message_text(
                    "⚠️ <b>No hay usuarios registrados</b>\n\n"
                    "El bot aún no tiene usuarios en la base de datos.",
                    parse_mode='HTML'
                )
                del broadcast_sessions[user_id]
                return
                
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}", exc_info=True)
            await query.edit_message_text(
                f"❌ <b>Error obteniendo usuarios</b>\n\n"
                f"Error: {str(e)}",
                parse_mode='HTML'
            )
            if user_id in broadcast_sessions:
                del broadcast_sessions[user_id]
            return
        
        # Determinar mensaje a enviar
        logger.info(f"Determinando mensaje para tipo: {session.message_type}")
        if session.message_type == 'welcome':
            message_text = (
                "👋 <b>¡Hola! ¿Estás aburrido?</b>\n\n"
                "¿Qué quieres ver hoy? Tenemos varias opciones para ti:\n\n"
                "🔍 Usa /buscar para encontrar películas o series\n"
                "📺 Visita nuestro canal de verificación para ver el catálogo completo\n"
                "💡 ¿No encuentras algo? ¡Solicita una nueva película o serie!\n\n"
                "¡Disfruta! 🍿"
            )
            # Botones interactivos
            keyboard = [
                [InlineKeyboardButton("🔍 Buscar Ahora", callback_data="menu_main")],
                [InlineKeyboardButton("📺 Ver Catálogo", url="https://t.me/CineStellar_S")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        elif session.message_type == 'thanks':
            message_text = (
                "🙏 <b>¡Gracias por usar CineStelar!</b>\n\n"
                "Esperamos que hayas disfrutado tu película o serie. "
                "Tu apoyo nos motiva a seguir mejorando.\n\n"
                "Si tienes alguna sugerencia o quieres solicitar contenido, "
                "¡no dudes en contactarnos!\n\n"
                "🌟 ¡Hasta la próxima! 🌟"
            )
            reply_markup = None
        else:  # custom o custom_video
            message_text = session.custom_message
            # Crear botones personalizados si existen
            if session.custom_buttons:
                keyboard = [[InlineKeyboardButton(btn['text'], url=btn['url'])] for btn in session.custom_buttons]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                reply_markup = None
        
        # Enviar a todos los usuarios
        sent_count = 0
        failed_count = 0
        
        # Editar mensaje existente para mostrar progreso inicial
        await query.edit_message_text(
            f"📤 <b>Enviando mensajes...</b>\n\n"
            f"👥 Total usuarios: {total_users}\n"
            f"📊 Progreso: 0/{total_users} (0%)",
            parse_mode='HTML'
        )
        
        for index, user in enumerate(users, 1):
            try:
                # Verificar si hay multimedia y enviar el tipo correspondiente
                if session.custom_video:
                    await context.bot.send_video(
                        chat_id=user.user_id,
                        video=session.custom_video,
                        caption=message_text if message_text else None,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                elif session.custom_photo:
                    await context.bot.send_photo(
                        chat_id=user.user_id,
                        photo=session.custom_photo,
                        caption=message_text if message_text else None,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                elif session.custom_audio:
                    await context.bot.send_audio(
                        chat_id=user.user_id,
                        audio=session.custom_audio,
                        caption=message_text if message_text else None,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                elif session.custom_document:
                    await context.bot.send_document(
                        chat_id=user.user_id,
                        document=session.custom_document,
                        caption=message_text if message_text else None,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                else:
                    # Enviar mensaje de texto normal
                    await context.bot.send_message(
                        chat_id=user.user_id,
                        text=message_text,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error enviando a usuario {user.user_id}: {e}")
            
            # Actualizar progreso cada 10 usuarios o al final
            if index % 10 == 0 or index == total_users:
                try:
                    percentage = int((index / total_users) * 100)
                    await query.edit_message_text(
                        f"📤 <b>Enviando mensajes...</b>\n\n"
                        f"👥 Total usuarios: {total_users}\n"
                        f"📊 Progreso: {index}/{total_users} ({percentage}%)\n"
                        f"✅ Enviados: {sent_count}\n"
                        f"❌ Fallidos: {failed_count}",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error actualizando progreso: {e}")
            
            # Pequeña pausa para evitar rate limit
            await asyncio.sleep(0.05)
        
        # Limpiar sesión
        if user_id in broadcast_sessions:
            del broadcast_sessions[user_id]
        
        # Mostrar resultados finales editando el mismo mensaje
        logger.info(f"Broadcast completado: enviados={sent_count}, fallidos={failed_count}")
        await query.edit_message_text(
            f"✅ <b>Broadcast Completado</b>\n\n"
            f"📤 Enviados exitosamente: {sent_count}\n"
            f"❌ Fallidos: {failed_count}\n"
            f"👥 Total usuarios: {total_users}",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error general en confirm_broadcast: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                f"❌ <b>Error ejecutando broadcast</b>\n\n"
                f"Error: {str(e)}\n\n"
                f"Por favor revisa los logs del servidor.",
                parse_mode='HTML'
            )
        except:
            pass
        if user_id in broadcast_sessions:
            del broadcast_sessions[user_id]

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el broadcast"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id in broadcast_sessions:
        del broadcast_sessions[user_id]
    
    await query.edit_message_text("❌ Broadcast cancelado.")

async def request_delete_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita confirmación para eliminar mensajes de broadcast"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Crear sesión
    session = BroadcastSession(user_id)
    session.message_type = 'delete'
    broadcast_sessions[user_id] = session
    
    keyboard = [
        [InlineKeyboardButton("⚠️ SÍ, Eliminar Todos", callback_data="broadcast_delete_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗑️ <b>Eliminar Mensajes de Broadcast</b>\n\n"
        "⚠️ <b>ADVERTENCIA:</b> Esta acción intentará eliminar el último mensaje enviado "
        "a cada usuario del bot.\n\n"
        "Esto es útil si enviaste un mensaje con errores.\n\n"
        "<i>Nota: Solo se pueden eliminar mensajes de las últimas 48 horas.</i>\n\n"
        "¿Deseas continuar?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def confirm_delete_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina el último mensaje enviado a todos los usuarios"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        logger.info(f"Iniciando eliminación de mensajes broadcast para admin {user_id}")
        
        session = broadcast_sessions.get(user_id)
        if not session:
            await query.edit_message_text("❌ Sesión expirada. Usa /broadcast nuevamente.")
            return
        
        # Obtener todos los usuarios
        users = await db.get_all_users()
        total_users = len(users)
        
        if total_users == 0:
            await query.edit_message_text(
                "⚠️ No hay usuarios registrados.",
                parse_mode='HTML'
            )
            del broadcast_sessions[user_id]
            return
        
        # Actualizar mensaje
        await query.edit_message_text(
            f"🗑️ <b>Eliminando mensajes...</b>\n\n"
            f"👥 Total usuarios: {total_users}\n"
            f"📊 Progreso: 0/{total_users} (0%)",
            parse_mode='HTML'
        )
        
        deleted_count = 0
        failed_count = 0
        
        # Intentar eliminar el último mensaje del bot en cada chat
        for index, user in enumerate(users, 1):
            try:
                # Obtener los últimos mensajes del chat
                # Nota: Telegram no permite obtener historial directo, así que
                # intentaremos eliminar usando el message_id almacenado en contexto
                # Si no hay message_id, fallará silenciosamente
                
                # Intentar obtener el último message_id del contexto del usuario
                user_data = await context.bot.get_chat(user.user_id)
                
                # Como no podemos obtener el message_id directamente,
                # esta funcionalidad requeriría almacenar los message_ids
                # de los broadcasts en la base de datos
                logger.warning(f"No se puede eliminar mensaje para user {user.user_id} - message_id no disponible")
                failed_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error eliminando mensaje de usuario {user.user_id}: {e}")
            
            # Actualizar progreso cada 10 usuarios
            if index % 10 == 0 or index == total_users:
                try:
                    percentage = int((index / total_users) * 100)
                    await query.edit_message_text(
                        f"🗑️ <b>Eliminando mensajes...</b>\n\n"
                        f"👥 Total usuarios: {total_users}\n"
                        f"📊 Progreso: {index}/{total_users} ({percentage}%)\n"
                        f"✅ Eliminados: {deleted_count}\n"
                        f"❌ No eliminados: {failed_count}",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Error actualizando progreso: {e}")
            
            await asyncio.sleep(0.05)
        
        # Limpiar sesión
        if user_id in broadcast_sessions:
            del broadcast_sessions[user_id]
        
        # Mostrar resultados
        await query.edit_message_text(
            f"🗑️ <b>Proceso Completado</b>\n\n"
            f"⚠️ <b>Limitación Técnica:</b>\n"
            f"Telegram no permite eliminar mensajes sin conocer sus IDs.\n\n"
            f"💡 <b>Solución:</b>\n"
            f"Para implementar esta función completamente, necesitamos:\n"
            f"1. Almacenar los message_ids cuando enviamos broadcasts\n"
            f"2. Crear una tabla en la BD para rastrear mensajes\n\n"
            f"📊 Usuarios procesados: {total_users}\n"
            f"❌ No se pudieron eliminar: {failed_count}\n\n"
            f"<i>Si deseas implementar esta función, avísame.</i>",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error general en confirm_delete_broadcast: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                f"❌ <b>Error eliminando mensajes</b>\n\n"
                f"Error: {str(e)}",
                parse_mode='HTML'
            )
        except:
            pass
        if user_id in broadcast_sessions:
            del broadcast_sessions[user_id]

async def show_broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas de usuarios para broadcast"""
    query = update.callback_query
    
    try:
        users = await db.get_all_users()
        total_users = len(users)
        
        if total_users == 0:
            await query.edit_message_text(
                "⚠️ <b>No hay usuarios registrados</b>\n\n"
                "El bot aún no tiene usuarios en la base de datos.",
                parse_mode='HTML'
            )
            return
        
        # Contar usuarios activos (últimos 7 días)
        from datetime import datetime, timedelta, timezone
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        active_users = sum(1 for user in users if user.last_active and user.last_active > week_ago)
        
        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="broadcast_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📊 <b>Estadísticas de Usuarios</b>\n\n"
            f"👥 Total de usuarios: {total_users}\n"
            f"🟢 Activos (últimos 7 días): {active_users}\n"
            f"📉 Inactivos: {total_users - active_users}\n\n"
            f"El mensaje se enviará a todos los {total_users} usuarios.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        await query.edit_message_text(
            f"❌ <b>Error obteniendo estadísticas</b>\n\n"
            f"Error: {str(e)}",
            parse_mode='HTML'
        )

async def add_media_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita al admin que envíe multimedia para agregar al mensaje personalizado"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Obtener sesión
    session = broadcast_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión no encontrada. Inicia un nuevo broadcast.")
        return
    
    # Limpiar multimedia anterior si existe
    session.custom_video = None
    session.custom_photo = None
    session.custom_audio = None
    session.custom_document = None
    
    # Cambiar estado para esperar multimedia
    session.awaiting_video = True
    
    await query.edit_message_text(
        "🎥 <b>Agregar Multimedia</b>\n\n"
        "Envía el archivo multimedia:\n\n"
        "📹 Video\n"
        "📷 Foto\n"
        "🎵 Audio\n"
        "📄 Documento\n\n"
        "Envía /cancelar para cancelar.",
        parse_mode='HTML'
    )

async def add_text_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita al admin que agregue texto al multimedia"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Obtener sesión
    session = broadcast_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión no encontrada. Inicia un nuevo broadcast.")
        return
    
    # Cambiar estado para esperar texto
    session.awaiting_custom = True
    
    await query.edit_message_text(
        "✍️ <b>Agregar Texto</b>\n\n"
        "Escribe el mensaje que acompañará al archivo multimedia.\n\n"
        "Puedes usar HTML para formato:\n"
        "• <code>&lt;b&gt;texto&lt;/b&gt;</code> para <b>negrita</b>\n"
        "• <code>&lt;i&gt;texto&lt;/i&gt;</code> para <i>cursiva</i>\n\n"
        "Envía /cancelar para cancelar.",
        parse_mode='HTML'
    )
