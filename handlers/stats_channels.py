"""
Handler para estadísticas de canales
Comandos: /stats_canales, /add_canal
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS
from database.db_manager import DatabaseManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
db_manager = DatabaseManager()

async def stats_canales_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para ver estadísticas por canal
    Uso: /stats_canales
    """
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Obtener estadísticas del día por defecto
    await send_channel_stats(update, context, period='today')

async def send_channel_stats(update, context, period='today'):
    """Enviar mensaje con estadísticas de canales"""
    try:
        stats = await db_manager.get_channel_stats_by_period(period)
        
        if 'error' in stats:
            await update.effective_message.reply_text(f"❌ Error obteniendo estadísticas: {stats['error']}")
            return
        
        # Formatear mensaje
        period_names = {
            'today': 'HOY',
            'week': 'ESTA SEMANA', 
            'month': 'ESTE MES',
            'total': 'TOTAL (DESDE EL INICIO)'
        }
        
        period_emojis = {
            'today': '📅',
            'week': '📆',
            'month': '🗓️',
            'total': '📊'
        }
        
        message = f"📊 *ESTADÍSTICAS POR CANAL*\n"
        message += f"_{period_emojis[period]} {period_names[period]}_\n\n"
        
        # Botones de período
        buttons_row1 = []
        periods = ['today', 'week', 'month', 'total']
        for p in periods:
            emoji = period_emojis[p]
            if p == period:
                text = f"🔵 {emoji}"
            else:
                text = f"🔘 {emoji}"
            buttons_row1.append(InlineKeyboardButton(text, callback_data=f"stats_period_{p}"))
        
        if not stats['channels']:
            message += "📭 *No hay datos de canales disponibles*\n\n"
            message += "💡 Usa /add_canal para agregar canales y comenzar el tracking"
        else:
            # Mostrar canales
            for i, channel in enumerate(stats['channels'][:10], 1):  # Top 10
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈" 
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}️⃣"
                
                message += f"{medal} *{channel['channel_name']}*\n"
                message += f"   👥 {channel['unique_users']} usuarios únicos\n"
                message += f"   🔗 {channel['total_visits']} clicks totales\n"
                
                if channel['last_visit']:
                    last_visit = channel['last_visit']
                    if isinstance(last_visit, str):
                        try:
                            last_visit = datetime.fromisoformat(last_visit.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    if isinstance(last_visit, datetime):
                        now = datetime.now(last_visit.tzinfo)
                        diff = now - last_visit
                        if diff.days > 0:
                            time_str = f"{diff.days} días"
                        elif diff.seconds > 3600:
                            hours = diff.seconds // 3600
                            time_str = f"{hours} horas"
                        elif diff.seconds > 60:
                            minutes = diff.seconds // 60
                            time_str = f"{minutes} min"
                        else:
                            time_str = "ahora"
                        message += f"   📅 Última visita: hace {time_str}\n"
                
                if period == 'total' and channel['added_at']:
                    added_date = channel['added_at']
                    if isinstance(added_date, str):
                        try:
                            added_date = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                        except:
                            pass
                    if isinstance(added_date, datetime):
                        message += f"   📅 Agregado: {added_date.strftime('%d/%m/%Y')}\n"
                
                message += "\n"
            
            # Totales
            message += "━━━━━━━━━━━━━━━━━━\n"
            message += f"📈 *Total {period_names[period].lower()}:* {stats['total_users']} usuarios\n"
            
            if period != 'today':
                if period == 'week':
                    avg_daily = stats['total_users'] // 7 if stats['total_users'] > 0 else 0
                    message += f"📊 *Promedio diario:* {avg_daily} usuarios\n"
                elif period == 'month':
                    avg_daily = stats['total_users'] // 30 if stats['total_users'] > 0 else 0
                    message += f"📊 *Promedio diario:* {avg_daily} usuarios\n"
            
            # Canal más activo
            if stats['channels']:
                best_channel = stats['channels'][0]
                message += f"🔥 *Más activo:* {best_channel['channel_name']}"
        
        # Crear keyboard
        keyboard = [buttons_row1]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enviar o editar mensaje
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.effective_message.reply_text(
                message,
                parse_mode='Markdown', 
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"Error en send_channel_stats: {e}")
        error_msg = f"❌ Error obteniendo estadísticas: {str(e)}"
        
        if update.callback_query:
            await update.callback_query.answer(error_msg)
        else:
            await update.effective_message.reply_text(error_msg)

async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar callbacks de estadísticas de canales"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    if user.id not in ADMIN_IDS:
        await query.answer("❌ No tienes permisos.")
        return
    
    data = query.data
    
    if data.startswith('stats_period_'):
        period = data.replace('stats_period_', '')
        await send_channel_stats(update, context, period)

async def add_canal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para agregar nuevo canal para tracking
    Uso: /add_canal <channel_id> <channel_name> [descripcion]
    Ejemplo: /add_canal canal_principal @mi_canal_principal Descripcion del canal
    """
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ <b>Uso incorrecto</b>\n\n"
            "<b>Formato:</b> <code>/add_canal &lt;id_canal&gt; &lt;nombre_canal&gt; [descripcion]</code>\n\n"
            "<b>Ejemplo:</b>\n"
            "<code>/add_canal canal_principal @mi_canal Canal principal de películas</code>\n\n"
            "<b>Notas:</b>\n"
            "• <code>id_canal</code>: Identificador único (sin espacios)\n"
            "• <code>nombre_canal</code>: Nombre del canal (ej: @mi_canal)\n"
            "• <code>descripcion</code>: Opcional, descripción del canal",
            parse_mode='HTML'
        )
        return
    
    channel_id = args[0]
    channel_name = args[1]
    description = ' '.join(args[2:]) if len(args) > 2 else None
    
    # Validar ID del canal
    if not channel_id.replace('_', '').replace('-', '').isalnum():
        await update.message.reply_text("❌ El ID del canal solo puede contener letras, números, guiones y guiones bajos.")
        return
    
    # Agregar canal
    success, message = await db_manager.add_channel_source(
        channel_id=channel_id,
        channel_name=channel_name, 
        description=description
    )
    
    if success:
        bot_username = context.bot.username
        tracking_link = f"https://t.me/{bot_username}?start={channel_id}"
        
        response = f"✅ <b>Canal agregado exitosamente</b>\n\n"
        response += f"📺 <b>Canal:</b> {channel_name}\n"
        response += f"🆔 <b>ID:</b> <code>{channel_id}</code>\n"
        if description:
            # Escapar HTML en la descripción
            description_escaped = description.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            response += f"📝 <b>Descripción:</b> {description_escaped}\n"
        response += f"\n🔗 <b>Enlace para usar en posts:</b>\n"
        response += f"<code>{tracking_link}</code>\n\n"
        response += "💡 <b>Cómo usar:</b>\n"
        response += "Publica este enlace en tu canal. Cuando alguien haga click, se registrará automáticamente la visita desde este canal."
        
        await update.message.reply_text(response, parse_mode='HTML')
    else:
        await update.message.reply_text(f"❌ {message}")

async def list_canales_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para listar canales configurados
    Uso: /list_canales
    """
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    try:
        channels = await db_manager.get_active_channel_sources()
        
        if not channels:
            await update.message.reply_text(
                "📭 <b>No hay canales configurados</b>\n\n"
                "Usa /add_canal para agregar tu primer canal.",
                parse_mode='HTML'
            )
            return
        
        message = f"📺 <b>CANALES CONFIGURADOS</b> ({len(channels)})\n\n"
        
        bot_username = context.bot.username
        
        for i, channel in enumerate(channels, 1):
            tracking_link = f"https://t.me/{bot_username}?start={channel.channel_id}"
            
            message += f"{i}️⃣ <b>{channel.channel_name}</b>\n"
            message += f"   🆔 ID: <code>{channel.channel_id}</code>\n"
            if channel.description:
                # Escapar HTML en la descripción
                description = channel.description.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
                message += f"   📝 {description}\n"
            message += f"   📅 Agregado: {channel.added_at.strftime('%d/%m/%Y')}\n"
            message += f"   🔗 <code>{tracking_link}</code>\n\n"
        
        message += "💡 <b>Para ver estadísticas usa:</b> /stats_canales"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error en list_canales: {e}")
        await update.message.reply_text(f"❌ Error obteniendo canales: {str(e)}")