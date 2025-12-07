from database.db_manager import DatabaseManager
from database.models import UserPoints
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PointsManager:
    """Gestor de puntos del usuario"""

    # Configuración de puntos
    # POINTS_PER_VIDEO = 0.5  # Puntos ganados por video visto - DESACTIVADO
    # MAX_POINTS_PER_DAY = 5.0  # Máximo de puntos por día - DESACTIVADO
    REFERRAL_POINTS = 5.0  # Puntos por referido completado
    VIDEO_COST = 1.0  # Costo en puntos para ver un video

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # async def award_video_points(self, user_id):
    #     """Otorga puntos por ver un video (con límite diario) - DESACTIVADO"""
    #     return False, "Sistema de puntos por videos desactivado"

    async def use_points_for_video(self, user_id):
        """Usa puntos para ver un video"""
        try:
            user_points = await self.db.get_user_points(user_id)

            if not user_points:
                return False, "No tienes puntos suficientes"

            if user_points.available_points < self.VIDEO_COST:
                return False, f"Necesitas {self.VIDEO_COST} puntos. Tienes {user_points.available_points}"

            # Usar puntos
            success = await self.db.use_user_points(user_id, self.VIDEO_COST)

            if success:
                return True, f"Usaste {self.VIDEO_COST} punto(s) para ver el video"
            else:
                return False, "Error al usar puntos"

        except Exception as e:
            logger.error(f"Error usando puntos para video: {e}")
            return False, "Error interno del sistema"

    async def get_user_balance(self, user_id):
        """Obtiene el balance de puntos del usuario"""
        try:
            user_points = await self.db.get_user_points(user_id)

            if not user_points:
                # Crear registro si no existe
                user_points = await self.db.create_or_update_user_points(user_id, 0.0)

            return {
                'total_points': user_points.total_points,
                'available_points': user_points.available_points,
                'used_points': user_points.used_points,
                'last_activity': user_points.last_activity
            }

        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return None

    async def can_user_watch_video(self, user_id):
        """Verifica si el usuario puede ver un video - SIEMPRE PERMITIDO"""
        try:
            # En este sistema, siempre se puede ver videos
            # Los puntos solo se usan si el usuario elige usarlos
            return True

        except Exception as e:
            logger.error(f"Error verificando permisos de video: {e}")
            return False

    async def _get_today_earned_points(self, user_id):
        """Obtiene los puntos ganados hoy por el usuario"""
        try:
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)

            # Obtener historial de transacciones de hoy
            history = await self.db.get_points_history(user_id, limit=100)

            today_earned = 0.0
            for transaction in history:
                if (transaction.created_at.date() == today and
                    transaction.transaction_type == 'earned' and
                    transaction.amount > 0):
                    today_earned += transaction.amount

            return today_earned

        except Exception as e:
            logger.error(f"Error obteniendo puntos del día: {e}")
            return 0.0

    async def get_points_summary(self, user_id):
        """Obtiene un resumen completo de puntos del usuario"""
        try:
            balance = await self.get_user_balance(user_id)
            if not balance:
                return None

            # No necesitamos today_earned ya que no se ganan puntos por videos
            return {
                'balance': balance,
                'can_watch_free': True,  # Siempre se puede ver gratis
                'next_free_video': True   # Siempre disponible
            }

        except Exception as e:
            logger.error(f"Error obteniendo resumen de puntos: {e}")
            return None

    async def award_bonus_points(self, user_id, amount, reason):
        """Otorga puntos de bonificación"""
        try:
            user_points = await self.db.create_or_update_user_points(user_id, amount)

            await self.db.add_points_transaction(
                user_points_id=user_points.id,
                transaction_type='bonus',
                amount=amount,
                description=f'Bonificación: {reason}'
            )

            return True, f"Bonificación de {amount} puntos otorgada"

        except Exception as e:
            logger.error(f"Error otorgando bonificación: {e}")
            return False, "Error otorgando bonificación"