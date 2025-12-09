"""
Sistema de Tickets y Referidos
Comandos: /mistickets, /invitar, /misreferidos
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS, BOT_USERNAME
import logging

logger = logging.getLogger(__name__)

# Configuración de recompensas
REFERRAL_REWARD = 5  # Tickets por referido verificado

async def mis_tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /mistickets - Muestra los tickets del usuario
    """
    user = update.effective_user
    db = context.bot_data['db']
    
    # Obtener tickets del usuario
    user_tickets = await db.get_user_tickets(user.id)
    
    if not user_tickets:
        tickets = 0
        used = 0
        earned = 0
    else:
        tickets = user_tickets.tickets
        used = user_tickets.tickets_used
        earned = user_tickets.tickets_earned
    
    # Obtener historial reciente
    transactions = await db.get_ticket_transactions(user.id, limit=5)
    
    # Construir mensaje
    message = (
        f"🎟️ <b>Mis Tickets</b>\n\n"
        f"📦 Tickets disponibles: <b>{tickets}</b>\n"
        f"✅ Total ganados: {earned}\n"
        f"🎬 Total usados: {used}\n\n"
    )
    
    if transactions:
        message += "<b>📋 Últimas transacciones:</b>\n"
        for t in transactions:
            emoji = "➕" if t.amount > 0 else "➖"
            message += f"{emoji} {abs(t.amount)} - {t.description or t.reason}\n"
    
    message += (
        f"\n💡 <b>¿Cómo conseguir más tickets?</b>\n"
        f"• Invita amigos con /invitar\n"
        f"• Cada amigo verificado = {REFERRAL_REWARD} tickets\n"
        f"• Los tickets te permiten ver sin anuncios"
    )
    
    keyboard = [
        [InlineKeyboardButton("📨 Invitar Amigos", callback_data="tickets_invite")],
        [InlineKeyboardButton("📊 Ver Mis Referidos", callback_data="tickets_referrals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def invitar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /invitar - Genera link de invitación
    """
    user = update.effective_user
    db = context.bot_data['db']
    
    # Generar link de referido
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"
    
    # Obtener estadísticas
    stats = await db.get_referral_stats(user.id)
    
    message = (
        f"📨 <b>Invita Amigos y Gana Tickets</b>\n\n"
        f"🔗 Tu link personal:\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 <b>Tus estadísticas:</b>\n"
        f"👥 Total invitados: {stats['total']}\n"
        f"✅ Verificados: {stats['verified']}\n"
        f"⏳ Pendientes: {stats['pending']}\n\n"
        f"🎁 <b>Recompensa:</b>\n"
        f"Recibes <b>{REFERRAL_REWARD} tickets</b> por cada amigo que:\n"
        f"1. Use tu link para abrir el bot\n"
        f"2. Se una al canal de verificación\n\n"
        f"💡 Comparte tu link en grupos, redes sociales, etc."
    )
    
    # Botón para compartir
    share_text = f"🎬 ¡Descubre CineStelar! Películas y series gratis.\n{ref_link}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Compartir Link", url=f"https://t.me/share/url?url={ref_link}&text=🎬 Películas y series gratis en CineStelar!")],
        [InlineKeyboardButton("📊 Ver Mis Referidos", callback_data="tickets_referrals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def mis_referidos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /misreferidos - Lista de referidos
    """
    user = update.effective_user
    db = context.bot_data['db']
    
    await show_referrals_list(update, context, user.id)

async def show_referrals_list(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Muestra la lista de referidos (usado por comando y callback)"""
    db = context.bot_data['db']
    
    referrals = await db.get_user_referrals(user_id)
    stats = await db.get_referral_stats(user_id)
    
    message = (
        f"👥 <b>Mis Referidos</b>\n\n"
        f"📊 Total: {stats['total']} | ✅ Verificados: {stats['verified']} | ⏳ Pendientes: {stats['pending']}\n\n"
    )
    
    if not referrals:
        message += (
            "📭 Aún no tienes referidos.\n\n"
            "¡Comparte tu link con /invitar para empezar a ganar tickets!"
        )
    else:
        message += "<b>Lista de referidos:</b>\n"
        for ref in referrals[:15]:  # Máximo 15 para no hacer el mensaje muy largo
            status_emoji = "✅" if ref.status in ['verified', 'rewarded'] else "⏳"
            # Intentar obtener info del usuario referido
            referred_user = await db.get_user(ref.referred_id)
            name = referred_user.first_name if referred_user else f"Usuario {ref.referred_id}"
            message += f"{status_emoji} {name}\n"
    
    keyboard = [
        [InlineKeyboardButton("📨 Obtener Link", callback_data="tickets_invite")],
        [InlineKeyboardButton("🎟️ Ver Mis Tickets", callback_data="tickets_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Determinar si es callback o mensaje
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def handle_tickets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks del sistema de tickets"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db = context.bot_data['db']
    data = query.data
    
    if data == "tickets_invite":
        # Mostrar link de invitación
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"
        stats = await db.get_referral_stats(user.id)
        
        message = (
            f"📨 <b>Tu Link de Invitación</b>\n\n"
            f"🔗 <code>{ref_link}</code>\n\n"
            f"📊 Invitados: {stats['total']} | Verificados: {stats['verified']}\n\n"
            f"🎁 Ganas {REFERRAL_REWARD} tickets por cada verificado"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Compartir", url=f"https://t.me/share/url?url={ref_link}&text=🎬 Películas y series gratis!")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="tickets_balance")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    elif data == "tickets_referrals":
        await show_referrals_list(update, context, user.id)
    
    elif data == "tickets_balance":
        # Mostrar balance
        user_tickets = await db.get_user_tickets(user.id)
        tickets = user_tickets.tickets if user_tickets else 0
        earned = user_tickets.tickets_earned if user_tickets else 0
        used = user_tickets.tickets_used if user_tickets else 0
        
        message = (
            f"🎟️ <b>Mis Tickets</b>\n\n"
            f"📦 Disponibles: <b>{tickets}</b>\n"
            f"✅ Ganados: {earned}\n"
            f"🎬 Usados: {used}\n\n"
            f"💡 Invita amigos para ganar más tickets"
        )
        
        keyboard = [
            [InlineKeyboardButton("📨 Invitar Amigos", callback_data="tickets_invite")],
            [InlineKeyboardButton("📊 Ver Referidos", callback_data="tickets_referrals")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

async def process_referral_start(update: Update, context: ContextTypes.DEFAULT_TYPE, referrer_id: int):
    """Procesa un usuario que llega por link de referido"""
    user = update.effective_user
    db = context.bot_data['db']
    
    # No puede auto-referirse
    if user.id == referrer_id:
        return
    
    # Verificar si ya existe este usuario como referido
    existing = await db.get_referral_by_referred(user.id)
    if existing:
        return  # Ya fue referido antes
    
    # Crear referido pendiente
    referral = await db.create_referral(referrer_id, user.id)
    
    if referral:
        logger.info(f"Nuevo referido: {user.id} invitado por {referrer_id}")
        
        # Notificar al usuario que fue invitado
        try:
            referrer = await db.get_user(referrer_id)
            referrer_name = referrer.first_name if referrer else "alguien"
            
            await update.message.reply_text(
                f"🎉 ¡Fuiste invitado por <b>{referrer_name}</b>!\n\n"
                f"Para completar la invitación, únete al canal de verificación.\n"
                f"Tu amigo recibirá {REFERRAL_REWARD} tickets cuando te verifiques.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error notificando referido: {e}")

async def check_and_reward_referral(user_id: int, db):
    """Verifica y recompensa referidos cuando un usuario se verifica"""
    try:
        # Verificar el referido
        referral = await db.verify_referral(user_id)
        
        if referral:
            # Recompensar al referrer
            result = await db.reward_referral(user_id, REFERRAL_REWARD)
            
            if result:
                referrer_id, total_tickets = result
                logger.info(f"Referido recompensado: {referrer_id} recibió {REFERRAL_REWARD} tickets")
                return referrer_id, REFERRAL_REWARD
    
    except Exception as e:
        logger.error(f"Error procesando recompensa de referido: {e}")
    
    return None
