"""
Panel de Administración de Usuarios
- Dar/quitar tickets
- Enviar mensaje directo
- Ver información de usuario
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS
from database.db_manager import DatabaseManager
import logging

db = DatabaseManager()
logger = logging.getLogger(__name__)

# Sesiones de admin activas
admin_sessions = {}

class AdminUserSession:
    """Sesión de gestión de usuario"""
    def __init__(self, admin_id):
        self.admin_id = admin_id
        self.target_user_id = None
        self.action = None  # 'give_tickets', 'send_message', 'view_info'
        self.awaiting_input = False
        self.pending_message = None
        self.pending_tickets = None

async def admin_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /usuarios - Panel de gestión de usuarios
    """
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Crear sesión
    admin_sessions[user_id] = AdminUserSession(user_id)
    admin_sessions[user_id].awaiting_input = True
    admin_sessions[user_id].action = 'select_user'
    
    await update.message.reply_text(
        "👥 <b>Gestión de Usuarios</b>\n\n"
        "Envía el <b>ID de usuario</b> o <b>@username</b> del usuario que quieres gestionar.\n\n"
        "💡 Puedes obtener el ID desde /stats o cuando un usuario usa el bot.",
        parse_mode='HTML'
    )

async def handle_admin_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el input de texto para gestión de usuarios"""
    user_id = update.effective_user.id
    
    if user_id not in admin_sessions:
        return False
    
    session = admin_sessions[user_id]
    
    if not session.awaiting_input:
        return False
    
    text = update.message.text.strip()
    
    # Seleccionar usuario
    if session.action == 'select_user':
        target_user = None
        
        # Buscar por ID o username
        if text.isdigit():
            target_user = await db.get_user(int(text))
        elif text.startswith('@'):
            # Buscar por username
            from sqlalchemy import select
            from database.models import User
            async with db.async_session() as db_session:
                result = await db_session.execute(
                    select(User).where(User.username == text.lstrip('@'))
                )
                target_user = result.scalar_one_or_none()
        else:
            # Intentar como ID
            try:
                target_user = await db.get_user(int(text))
            except:
                pass
        
        if not target_user:
            await update.message.reply_text(
                "❌ Usuario no encontrado.\n"
                "Verifica el ID o username e intenta de nuevo."
            )
            return True
        
        session.target_user_id = target_user.user_id
        session.awaiting_input = False
        
        # Mostrar menú de acciones
        await show_user_management_menu(update, context, target_user)
        return True
    
    # Dar tickets
    elif session.action == 'give_tickets':
        try:
            amount = int(text)
            if amount == 0:
                await update.message.reply_text("❌ La cantidad debe ser diferente de 0.")
                return True
            
            # Dar o quitar tickets
            new_balance = await db.add_tickets(
                user_id=session.target_user_id,
                amount=amount,
                reason='admin_gift' if amount > 0 else 'admin_remove',
                description=f'{"Dado" if amount > 0 else "Quitado"} por admin {user_id}',
                reference_id=user_id
            )
            
            session.awaiting_input = False
            
            # Notificar al usuario
            try:
                if amount > 0:
                    await context.bot.send_message(
                        chat_id=session.target_user_id,
                        text=f"🎁 <b>¡Recibiste tickets!</b>\n\n"
                             f"Un administrador te ha dado <b>+{amount} tickets</b> 🎟️\n\n"
                             f"Usa /mistickets para ver tu balance.",
                        parse_mode='HTML'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=session.target_user_id,
                        text=f"⚠️ <b>Tickets ajustados</b>\n\n"
                             f"Se han ajustado <b>{amount} tickets</b> de tu cuenta.\n\n"
                             f"Usa /mistickets para ver tu balance.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Error notificando usuario: {e}")
            
            await update.message.reply_text(
                f"✅ <b>Tickets actualizados</b>\n\n"
                f"Usuario: {session.target_user_id}\n"
                f"Cantidad: {'+' if amount > 0 else ''}{amount}\n"
                f"Nuevo balance: {new_balance}",
                parse_mode='HTML'
            )
            
            del admin_sessions[user_id]
            return True
            
        except ValueError:
            await update.message.reply_text(
                "❌ Debes enviar un número.\n"
                "Ejemplo: <code>5</code> para dar 5 tickets\n"
                "O <code>-3</code> para quitar 3 tickets",
                parse_mode='HTML'
            )
            return True
    
    # Enviar mensaje
    elif session.action == 'send_message':
        message_text = text
        
        try:
            await context.bot.send_message(
                chat_id=session.target_user_id,
                text=f"📬 <b>Mensaje del Administrador:</b>\n\n{message_text}",
                parse_mode='HTML'
            )
            
            session.awaiting_input = False
            del admin_sessions[user_id]
            
            await update.message.reply_text(
                f"✅ Mensaje enviado correctamente al usuario {session.target_user_id}"
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error enviando mensaje: {e}\n\n"
                f"El usuario puede haber bloqueado el bot."
            )
        
        return True
    
    return False

async def show_user_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user):
    """Muestra el menú de gestión para un usuario"""
    # Obtener info adicional
    user_tickets = await db.get_user_tickets(target_user.user_id)
    tickets = user_tickets.tickets if user_tickets else 0
    
    referral_stats = await db.get_referral_stats(target_user.user_id)
    
    message = (
        f"👤 <b>Gestión de Usuario</b>\n\n"
        f"🆔 ID: <code>{target_user.user_id}</code>\n"
        f"👤 Nombre: {target_user.first_name or 'N/A'}\n"
        f"📛 Username: @{target_user.username or 'N/A'}\n"
        f"✅ Verificado: {'Sí' if target_user.verified else 'No'}\n"
        f"📅 Registro: {target_user.joined_at.strftime('%d/%m/%Y') if target_user.joined_at else 'N/A'}\n\n"
        f"🎟️ <b>Tickets:</b> {tickets}\n"
        f"👥 <b>Referidos:</b> {referral_stats['total']} (✅{referral_stats['verified']})\n\n"
        f"¿Qué quieres hacer?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎟️ Dar/Quitar Tickets", callback_data=f"admu_tickets_{target_user.user_id}")],
        [InlineKeyboardButton("📬 Enviar Mensaje", callback_data=f"admu_message_{target_user.user_id}")],
        [InlineKeyboardButton("📊 Ver Historial", callback_data=f"admu_history_{target_user.user_id}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="admu_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_admin_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de gestión de usuarios"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ No tienes permisos.")
        return
    
    if data == "admu_cancel":
        if user_id in admin_sessions:
            del admin_sessions[user_id]
        await query.edit_message_text("❌ Operación cancelada.")
        return
    
    # admu_tickets_{user_id}
    if data.startswith("admu_tickets_"):
        target_user_id = int(data.split("_")[2])
        
        if user_id not in admin_sessions:
            admin_sessions[user_id] = AdminUserSession(user_id)
        
        admin_sessions[user_id].target_user_id = target_user_id
        admin_sessions[user_id].action = 'give_tickets'
        admin_sessions[user_id].awaiting_input = True
        
        await query.edit_message_text(
            f"🎟️ <b>Dar/Quitar Tickets</b>\n\n"
            f"Usuario: <code>{target_user_id}</code>\n\n"
            f"Envía la cantidad de tickets:\n"
            f"• Número positivo para dar (ej: <code>5</code>)\n"
            f"• Número negativo para quitar (ej: <code>-3</code>)",
            parse_mode='HTML'
        )
    
    # admu_message_{user_id}
    elif data.startswith("admu_message_"):
        target_user_id = int(data.split("_")[2])
        
        if user_id not in admin_sessions:
            admin_sessions[user_id] = AdminUserSession(user_id)
        
        admin_sessions[user_id].target_user_id = target_user_id
        admin_sessions[user_id].action = 'send_message'
        admin_sessions[user_id].awaiting_input = True
        
        await query.edit_message_text(
            f"📬 <b>Enviar Mensaje Directo</b>\n\n"
            f"Usuario: <code>{target_user_id}</code>\n\n"
            f"Escribe el mensaje que quieres enviar a este usuario.\n"
            f"Se enviará tal cual lo escribas.",
            parse_mode='HTML'
        )
    
    # admu_history_{user_id}
    elif data.startswith("admu_history_"):
        target_user_id = int(data.split("_")[2])
        
        # Obtener historial de actividad
        history = await db.get_user_watch_history(target_user_id, limit=10)
        transactions = await db.get_ticket_transactions(target_user_id, limit=10)
        
        message = f"📊 <b>Historial de Usuario {target_user_id}</b>\n\n"
        
        if history:
            message += "<b>🎬 Últimos videos vistos:</b>\n"
            for h in history[:5]:
                used = "🎟️" if h.used_ticket else "📺"
                message += f"{used} {h.content_type} ID:{h.content_id}\n"
            message += "\n"
        
        if transactions:
            message += "<b>🎟️ Transacciones de tickets:</b>\n"
            for t in transactions[:5]:
                emoji = "➕" if t.amount > 0 else "➖"
                message += f"{emoji} {abs(t.amount)} - {t.reason}\n"
        
        if not history and not transactions:
            message += "No hay historial disponible."
        
        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data=f"admu_back_{target_user_id}")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    # admu_back_{user_id} - Volver al menú
    elif data.startswith("admu_back_"):
        target_user_id = int(data.split("_")[2])
        target_user = await db.get_user(target_user_id)
        
        if target_user:
            user_tickets = await db.get_user_tickets(target_user.user_id)
            tickets = user_tickets.tickets if user_tickets else 0
            referral_stats = await db.get_referral_stats(target_user.user_id)
            
            message = (
                f"👤 <b>Gestión de Usuario</b>\n\n"
                f"🆔 ID: <code>{target_user.user_id}</code>\n"
                f"👤 Nombre: {target_user.first_name or 'N/A'}\n"
                f"📛 Username: @{target_user.username or 'N/A'}\n"
                f"✅ Verificado: {'Sí' if target_user.verified else 'No'}\n\n"
                f"🎟️ <b>Tickets:</b> {tickets}\n"
                f"👥 <b>Referidos:</b> {referral_stats['total']}\n\n"
                f"¿Qué quieres hacer?"
            )
            
            keyboard = [
                [InlineKeyboardButton("🎟️ Dar/Quitar Tickets", callback_data=f"admu_tickets_{target_user.user_id}")],
                [InlineKeyboardButton("📬 Enviar Mensaje", callback_data=f"admu_message_{target_user.user_id}")],
                [InlineKeyboardButton("📊 Ver Historial", callback_data=f"admu_history_{target_user.user_id}")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="admu_cancel")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
