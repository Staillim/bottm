import secrets
import string
from datetime import datetime, timedelta, timezone
from database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class ReferralSystem:
    """Sistema de gestión de referidos"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def generate_referral_code(self, user_id):
        """Genera un código de referido único para el usuario"""
        try:
            # Generar código alfanumérico único
            while True:
                code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

                # Verificar que no exista
                existing = await self.db.get_referral_by_code(code)
                if not existing:
                    break

            # Crear el referido en la base de datos
            referral = await self.db.create_referral(user_id, code)
            return referral.referral_code

        except Exception as e:
            logger.error(f"Error generando código de referido: {e}")
            return None

    async def get_user_referral_code(self, user_id):
        """Obtiene el código de referido activo del usuario"""
        try:
            referrals = await self.db.get_user_referrals(user_id)

            # Buscar referido activo (no expirado)
            for referral in referrals:
                if referral.status == 'pending' and referral.expires_at > datetime.now(timezone.utc):
                    return referral.referral_code

            # Si no tiene código activo, generar uno nuevo
            return await self.generate_referral_code(user_id)

        except Exception as e:
            logger.error(f"Error obteniendo código de referido: {e}")
            return None

    async def process_referral_join(self, referral_code, new_user_id):
        """Procesa cuando un nuevo usuario se une usando un código de referido"""
        try:
            # Verificar que el código existe y es válido
            referral = await self.db.get_referral_by_code(referral_code)
            if not referral:
                return False, "Código de referido inválido"

            if referral.status != 'pending':
                return False, "Este código ya fue usado"

            if referral.expires_at < datetime.now(timezone.utc):
                return False, "Este código ha expirado"

            # Verificar que no sea auto-referido
            if referral.referrer_id == new_user_id:
                return False, "No puedes referirte a ti mismo"

            # Completar el referido
            success = await self.db.complete_referral(referral_code, new_user_id)
            if success:
                return True, f"¡Bienvenido! Has sido referido por un usuario. El referrer recibió 5 puntos."
            else:
                return False, "Error al procesar el referido"

        except Exception as e:
            logger.error(f"Error procesando referido: {e}")
            return False, "Error interno del sistema"

    async def get_referral_stats(self, user_id):
        """Obtiene estadísticas de referidos del usuario"""
        try:
            referrals = await self.db.get_user_referrals(user_id)

            stats = {
                'total_referrals': len(referrals),
                'completed_referrals': 0,
                'pending_referrals': 0,
                'expired_referrals': 0,
                'total_points_earned': 0
            }

            for referral in referrals:
                if referral.status == 'completed':
                    stats['completed_referrals'] += 1
                    stats['total_points_earned'] += 5  # 5 puntos por referido completado
                elif referral.status == 'pending':
                    if referral.expires_at > datetime.now(timezone.utc):
                        stats['pending_referrals'] += 1
                    else:
                        stats['expired_referrals'] += 1
                else:
                    stats['expired_referrals'] += 1

            return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de referidos: {e}")
            return None

    def generate_referral_link(self, bot_username, referral_code):
        """Genera un enlace de referido para compartir"""
        return f"https://t.me/{bot_username}?start=ref_{referral_code}"

    async def validate_referral_code(self, code):
        """Valida si un código de referido es válido y usable"""
        try:
            referral = await self.db.get_referral_by_code(code)
            if not referral:
                return False, "Código no encontrado"

            if referral.status != 'pending':
                return False, "Código ya utilizado"

            if referral.expires_at < datetime.now(timezone.utc):
                return False, "Código expirado"

            return True, "Código válido"

        except Exception as e:
            logger.error(f"Error validando código de referido: {e}")
            return False, "Error de validación"