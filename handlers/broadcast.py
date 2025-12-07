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
        self.awaiting_custom = False

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
    elif data == "broadcast_confirm":
        await confirm_broadcast(update, context)
    elif data == "broadcast_cancel":
        await cancel_broadcast(update, context)

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
        "✍️ <b>Mensaje Personalizado</b>\n\n"
        "Escribe el mensaje que deseas enviar a todos los usuarios.\n\n"
        "Puedes usar HTML para formato:\n"
        "• <code>&lt;b&gt;texto&lt;/b&gt;</code> para <b>negrita</b>\n"
        "• <code>&lt;i&gt;texto&lt;/i&gt;</code> para <i>cursiva</i>\n"
        "• <code>&lt;code&gt;texto&lt;/code&gt;</code> para <code>código</code>\n\n"
        "Envía /cancelar para cancelar.",
        parse_mode='HTML'
    )

async def handle_custom_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el input del mensaje personalizado"""
    user_id = update.effective_user.id
    
    # Verificar si hay sesión activa
    session = broadcast_sessions.get(user_id)
    if not session or not session.awaiting_custom:
        return False
    
    message_text = update.message.text
    
    # Verificar cancelación
    if message_text == "/cancelar":
        del broadcast_sessions[user_id]
        await update.message.reply_text("❌ Broadcast cancelado.")
        return True
    
    # Guardar mensaje
    session.custom_message = message_text
    session.awaiting_custom = False
    
    # Mostrar preview
    keyboard = [
        [InlineKeyboardButton("✅ Enviar a todos", callback_data="broadcast_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📝 <b>Preview del Mensaje:</b>\n\n{message_text}\n\n"
        "¿Deseas enviar este mensaje a todos los usuarios?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return True

async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y ejecuta el broadcast"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    session = broadcast_sessions.get(user_id)
    if not session:
        await query.edit_message_text("❌ Sesión expirada. Usa /broadcast nuevamente.")
        return
    
    await query.edit_message_text("📤 <b>Enviando mensajes...</b>\n\nEsto puede tomar unos momentos.", parse_mode='HTML')
    
    # Obtener todos los usuarios
    users = await db.get_all_users()
    
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
        reply_markup = None
    
    # Enviar a todos los usuarios
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            sent_count += 1
            
            # Pequeña pausa para evitar rate limit
            await asyncio.sleep(0.05)
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Error enviando a usuario {user.user_id}: {e}")
    
    # Limpiar sesión
    del broadcast_sessions[user_id]
    
    # Reportar resultados
    await query.message.reply_text(
        f"✅ <b>Broadcast Completado</b>\n\n"
        f"📤 Enviados: {sent_count}\n"
        f"❌ Fallidos: {failed_count}\n"
        f"👥 Total usuarios: {len(users)}",
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
    
    users = await db.get_all_users()
    total_users = len(users)
    
    # Contar usuarios activos (últimos 7 días)
    from datetime import datetime, timedelta, timezone
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    active_users = sum(1 for user in users if user.last_activity and user.last_activity > week_ago)
    
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
