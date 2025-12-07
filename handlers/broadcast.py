"""
Sistema de broadcast para enviar mensajes a usuarios
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from config.settings import ADMIN_IDS, VERIFICATION_CHANNEL_ID
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
        self.custom_buttons = []
        self.awaiting_custom = False
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
    elif data == "broadcast_stats":
        await show_broadcast_stats(update, context)
    elif data == "broadcast_add_button":
        await add_button_prompt(update, context)
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
    
    message_text = update.message.text
    
    # Verificar cancelación
    if message_text == "/cancelar":
        del broadcast_sessions[user_id]
        await update.message.reply_text("❌ Broadcast cancelado.")
        return True
    
    # Estado 1: Esperando mensaje de texto
    if session.awaiting_custom:
        session.custom_message = message_text
        session.awaiting_custom = False
        
        # Preguntar si quiere agregar botones
        keyboard = [
            [InlineKeyboardButton("➕ Agregar Botón", callback_data="broadcast_add_button")],
            [InlineKeyboardButton("✅ Continuar sin botones", callback_data="broadcast_skip_buttons")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📝 <b>Mensaje guardado:</b>\n\n{message_text}\n\n"
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
    
    session = broadcast_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión expirada. Usa /broadcast nuevamente.")
        return
    
    # Obtener todos los usuarios primero
    try:
        users = await db.get_all_users()
        total_users = len(users)
        
        if total_users == 0:
            await query.edit_message_text(
                "⚠️ <b>No hay usuarios registrados</b>\n\n"
                "El bot aún no tiene usuarios en la base de datos.",
                parse_mode='HTML'
            )
            del broadcast_sessions[user_id]
            return
            
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        await query.edit_message_text(
            f"❌ <b>Error obteniendo usuarios</b>\n\n"
            f"Error: {str(e)}",
            parse_mode='HTML'
        )
        del broadcast_sessions[user_id]
        return
    
    # Determinar mensaje a enviar
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
            [InlineKeyboardButton("🔍 Buscar Ahora", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("📺 Ver Catálogo", url=f"https://t.me/{VERIFICATION_CHANNEL_ID.replace('@', '')}")]
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
    else:  # custom
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
    del broadcast_sessions[user_id]
    
    # Mostrar resultados finales editando el mismo mensaje
    await query.edit_message_text(
        f"✅ <b>Broadcast Completado</b>\n\n"
        f"📤 Enviados exitosamente: {sent_count}\n"
        f"❌ Fallidos: {failed_count}\n"
        f"👥 Total usuarios: {total_users}",
        parse_mode='HTML'
    )

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el broadcast"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id in broadcast_sessions:
        del broadcast_sessions[user_id]
    
    await query.edit_message_text("❌ Broadcast cancelado.")

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
