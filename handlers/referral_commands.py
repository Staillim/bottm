from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database.db_manager import DatabaseManager
from utils.referral_system import ReferralSystem
from utils.points_manager import PointsManager
from config.settings import BOT_USERNAME
import logging

logger = logging.getLogger(__name__)

class ReferralCommands:
    """Manejadores para comandos de referidos y puntos"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.referral_system = ReferralSystem(db_manager)
        self.points_manager = PointsManager(db_manager)

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /referral - Muestra el código de referido del usuario"""
        user = update.effective_user
        if not user:
            return

        try:
            # Obtener o generar código de referido
            referral_code = await self.referral_system.get_user_referral_code(user.id)

            if not referral_code:
                await update.message.reply_text(
                    "❌ Error al generar tu código de referido. Inténtalo de nuevo."
                )
                return

            # Obtener estadísticas de referidos
            stats = await self.referral_system.get_referral_stats(user.id)

            # Generar enlace de referido
            referral_link = self.referral_system.generate_referral_link(BOT_USERNAME, referral_code)

            # Crear mensaje con estadísticas
            message = f"""
🎯 **Sistema de Referidos**

Tu código de referido: `{referral_code}`
Enlace para compartir: {referral_link}

📊 **Estadísticas:**
• Referidos totales: {stats['total_referrals']}
• Referidos completados: {stats['completed_referrals']}
• Puntos ganados: {stats['total_points_earned']}

💡 **Cómo funciona:**
1. Comparte tu enlace con amigos
2. Cuando se unan usando tu código, ¡ganas 5 puntos!
3. Máximo 5 puntos por referido completado

🔗 Comparte este enlace: {referral_link}
"""

            # Crear botones inline
            keyboard = [
                [InlineKeyboardButton("📊 Ver mis puntos", callback_data="show_points")],
                [InlineKeyboardButton("🔄 Actualizar código", callback_data="refresh_referral")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error en comando referral: {e}")
            await update.message.reply_text(
                "❌ Error al procesar el comando. Inténtalo de nuevo."
            )

    async def points_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /points - Muestra el balance de puntos del usuario"""
        user = update.effective_user
        if not user:
            return

        try:
            # Obtener resumen de puntos
            summary = await self.points_manager.get_points_summary(user.id)

            if not summary:
                await update.message.reply_text(
                    "❌ Error al obtener tu balance de puntos. Inténtalo de nuevo."
                )
                return

            balance = summary['balance']

            message = f"""
💰 **Tu Balance de Puntos**

⭐ **Puntos Totales:** {balance['total_points']}
✅ **Puntos Disponibles:** {balance['available_points']}
❌ **Puntos Usados:** {balance['used_points']}

🎯 **Sistema de Puntos:**
• Los puntos se obtienen únicamente por referir amigos
• 5 puntos por referido completado
• 1 punto = 1 video premium (sin anuncio)

💡 **Cómo ganar puntos:**
• Usa `/referral` para obtener tu código de referido
• Comparte el enlace con amigos
• Gana 5 puntos cuando se unan usando tu código

🔥 **Beneficios:**
• Ve videos sin anuncios
• Sin límites de visualización
• Puntos ilimitados por referidos
"""

            # Crear botones inline
            keyboard = [
                [InlineKeyboardButton("🎯 Ver referidos", callback_data="show_referrals")],
                [InlineKeyboardButton("📈 Historial", callback_data="show_history")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error en comando points: {e}")
            await update.message.reply_text(
                "❌ Error al obtener tu balance. Inténtalo de nuevo."
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los callbacks de los botones inline"""
        query = update.callback_query
        await query.answer()

        user = query.from_user
        data = query.data

        try:
            if data == "show_points":
                await self._show_points_callback(query, user.id)
            elif data == "show_referrals":
                await self._show_referrals_callback(query, user.id)
            elif data == "show_history":
                await self._show_history_callback(query, user.id)
            elif data == "refresh_referral":
                await self._refresh_referral_callback(query, user.id, context)
            elif data.startswith("use_points_video_"):
                video_id = int(data.split("_")[3])
                await self._use_points_for_video_callback(query, user.id, video_id, context)

        except Exception as e:
            logger.error(f"Error en callback {data}: {e}")
            await query.edit_message_text(
                "❌ Error al procesar la solicitud. Inténtalo de nuevo."
            )

    async def _show_points_callback(self, query, user_id):
        """Muestra el balance de puntos en callback"""
        summary = await self.points_manager.get_points_summary(user_id)

        if not summary:
            await query.edit_message_text("❌ Error al obtener puntos.")
            return

        balance = summary['balance']

        message = f"""
💰 **Balance de Puntos**

⭐ Totales: {balance['total_points']}
✅ Disponibles: {balance['available_points']}
❌ Usados: {balance['used_points']}

💡 Los puntos se obtienen únicamente por referir amigos
"""

        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_referral")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def _show_referrals_callback(self, query, user_id):
        """Muestra estadísticas de referidos en callback"""
        stats = await self.referral_system.get_referral_stats(user_id)

        if not stats:
            await query.edit_message_text("❌ Error al obtener referidos.")
            return

        message = f"""
🎯 **Estadísticas de Referidos**

📊 **Resumen:**
• Total: {stats['total_referrals']}
• Completados: {stats['completed_referrals']}
• Pendientes: {stats['pending_referrals']}
• Expirados: {stats['expired_referrals']}

💰 **Puntos ganados:** {stats['total_points_earned']}

🎁 Cada referido completado = 5 puntos
"""

        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_points")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def _show_history_callback(self, query, user_id):
        """Muestra historial de transacciones"""
        history = await self.db.get_points_history(user_id, limit=10)

        if not history:
            message = "📈 **Historial de Puntos**\n\nNo hay transacciones registradas."
        else:
            message = "📈 **Últimas Transacciones**\n\n"
            for transaction in history[:10]:
                emoji = "➕" if transaction.amount > 0 else "➖"
                message += f"{emoji} {transaction.amount} pts - {transaction.description}\n"
                message += f"   _{transaction.created_at.strftime('%d/%m/%Y %H:%M')}_\n\n"

        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_points")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def _refresh_referral_callback(self, query, user_id, context):
        """Refresca el código de referido"""
        # Generar nuevo código
        new_code = await self.referral_system.generate_referral_code(user_id)

        if not new_code:
            await query.edit_message_text("❌ Error al generar nuevo código.")
            return

        # Generar nuevo enlace
        new_link = self.referral_system.generate_referral_link(BOT_USERNAME, new_code)

        message = f"""
🔄 **Código Actualizado**

Tu nuevo código: `{new_code}`
Nuevo enlace: {new_link}

¡Comparte este enlace con tus amigos!
"""

        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_referral")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def _use_points_for_video_callback(self, query, user_id, video_id, context):
        """Maneja el uso de puntos para ver un video sin anuncio"""
        try:
            # Verificar que el usuario tenga suficientes puntos
            user_balance = await self.points_manager.get_user_balance(user_id)
            if not user_balance or user_balance['available_points'] < PointsManager.VIDEO_COST:
                await query.edit_message_text(
                    f"❌ No tienes suficientes puntos.\n\n"
                    f"💰 Puntos disponibles: {user_balance['available_points'] if user_balance else 0}\n"
                    f"💡 Necesitas {PointsManager.VIDEO_COST} punto(s) para ver sin anuncio."
                )
                return

            # Usar los puntos
            success, message = await self.points_manager.use_points_for_video(user_id)
            if not success:
                await query.edit_message_text("❌ Error al usar puntos. Inténtalo de nuevo.")
                return

            # Obtener información del video
            video = await self.db.get_video_by_id(video_id)
            if not video:
                await query.edit_message_text("❌ Video no encontrado.")
                return

            # Actualizar mensaje con confirmación
            await query.edit_message_text(
                f"✅ <b>¡Puntos usados exitosamente!</b>\n\n"
                f"🎬 Enviando video: <b>{video.title}</b>\n\n"
                f"💰 Usaste {PointsManager.VIDEO_COST} punto(s)\n"
                f"⏳ Preparando envío...",
                parse_mode='HTML'
            )

            # Enviar el poster primero si existe
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
                    logger.error(f"Error enviando poster: {e}")

            # Enviar el video
            try:
                caption_text = f"🎬 {video.title}"
                if video.year:
                    caption_text += f" ({video.year})"

                await context.bot.send_video(
                    chat_id=user_id,
                    video=video.file_id,
                    caption=caption_text,
                    supports_streaming=True,
                    read_timeout=60,
                    write_timeout=60,
                    connect_timeout=60
                )

                # Mensaje de confirmación
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ ¡Disfruta tu video premium sin anuncios!\n\n"
                         "💰 Usa /points para ver tu balance\n"
                         "🎯 Usa /referral para ganar más puntos"
                )

            except Exception as e:
                logger.error(f"Error enviando video: {e}")
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Hubo un error al enviar el video. Por favor intenta más tarde."
                )

        except Exception as e:
            logger.error(f"Error en _use_points_for_video_callback: {e}")
            await query.edit_message_text(
                "❌ Error al procesar la solicitud. Inténtalo de nuevo."
            )

    def get_handlers(self):
        """Retorna los handlers para registrar en el bot"""
        return [
            CommandHandler("referral", self.referral_command),
            CommandHandler("points", self.points_command),
            CallbackQueryHandler(self.handle_callback, pattern="^(show_points|show_referrals|show_history|refresh_referral|back_to_referral|back_to_points|use_points_video_.*)$")
        ]