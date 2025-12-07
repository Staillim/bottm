#!/usr/bin/env python3
"""
Script de pruebas para el sistema de puntos y referidos
Ejecutar después de la migración para validar funcionamiento
"""

import asyncio
import logging
import time
from database.db_manager import DatabaseManager
from utils.referral_system import ReferralSystem
from utils.points_manager import PointsManager
from config.settings import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_referral_system():
    """Prueba el sistema de referidos"""
    logger.info("🧪 Probando sistema de referidos...")

    db = DatabaseManager()
    referral_system = ReferralSystem(db)

    try:
        # Crear usuario de prueba 1 con ID único
        base_id = int(time.time() * 1000000) % 1000000000
        user1_id = base_id
        user2_id = base_id + 1
        await db.add_user(user1_id, "testuser1", "Test User 1")

        # Generar código de referido
        code = await referral_system.generate_referral_code(user1_id)
        logger.info(f"✅ Código generado: {code}")

        # Verificar código
        valid, message = await referral_system.validate_referral_code(code)
        assert valid, f"Código debería ser válido: {message}"
        logger.info("✅ Validación de código correcta")

        # Crear usuario de prueba 2
        await db.add_user(user2_id, "testuser2", "Test User 2")

        # Procesar referido
        success, message = await referral_system.process_referral_join(code, user2_id)
        assert success, f"Referido debería procesarse: {message}"
        logger.info("✅ Referido procesado correctamente")

        # Verificar puntos otorgados
        points = await db.get_user_points(user1_id)
        assert points and points.total_points >= 5, "Deberían otorgarse 5 puntos"
        logger.info(f"✅ Puntos otorgados: {points.total_points}")

        # Verificar estadísticas
        stats = await referral_system.get_referral_stats(user1_id)
        assert stats['completed_referrals'] == 1, "Debería haber 1 referido completado"
        logger.info(f"✅ Estadísticas correctas: {stats}")

        logger.info("🎉 Sistema de referidos funciona correctamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error en pruebas de referidos: {e}")
        return False
    finally:
        await db.engine.dispose()

async def test_points_system():
    """Prueba el sistema de puntos (solo referidos)"""
    logger.info("🧪 Probando sistema de puntos...")

    db = DatabaseManager()
    points_manager = PointsManager(db)

    try:
        # Crear usuario de prueba con ID único
        user_id = int(time.time() * 1000000) % 1000000000 + 100
        await db.add_user(user_id, "testuser3", "Test User 3")

        # Verificar balance inicial
        balance = await points_manager.get_user_balance(user_id)
        assert balance['total_points'] == 0, "Balance inicial debería ser 0"
        logger.info("✅ Balance inicial correcto")

        # Simular puntos obtenidos por referidos (creamos manualmente)
        user_points = await db.create_or_update_user_points(user_id, 5.0)  # 5 puntos por referido
        logger.info("✅ Puntos creados manualmente (simulando referido)")

        # Verificar balance actualizado
        balance = await points_manager.get_user_balance(user_id)
        assert balance['total_points'] == 5.0, "Debería tener 5.0 puntos"
        logger.info(f"✅ Balance actualizado: {balance['total_points']}")

        # Verificar que puede ver video
        can_watch = await points_manager.can_user_watch_video(user_id)
        assert can_watch, "Debería poder ver video (siempre permitido)"
        logger.info("✅ Permisos de video correctos")

        # Intentar usar puntos para video sin suficientes
        success, message = await points_manager.use_points_for_video(user_id)
        assert success, f"Debería poder usar puntos: {message}"
        logger.info(f"✅ Puntos usados correctamente: {message}")

        # Verificar balance después de usar puntos
        balance = await points_manager.get_user_balance(user_id)
        assert balance['available_points'] == 4.0, "Debería quedar 4.0 puntos disponibles"
        assert balance['used_points'] == 1.0, "Debería tener 1.0 punto usado"
        logger.info(f"✅ Balance después de uso correcto: {balance}")

        # Intentar usar más puntos de los disponibles
        success, message = await points_manager.use_points_for_video(user_id)
        assert success, f"Debería poder usar puntos: {message}"
        logger.info("✅ Segundo uso de puntos correcto")

        # Verificar balance final
        balance = await points_manager.get_user_balance(user_id)
        assert balance['available_points'] == 3.0, "Debería quedar 3.0 puntos disponibles"
        assert balance['used_points'] == 2.0, "Debería tener 2.0 puntos usados"
        logger.info(f"✅ Balance final correcto: {balance}")

        logger.info("🎉 Sistema de puntos funciona correctamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error en pruebas de puntos: {e}")
        return False
    finally:
        await db.engine.dispose()

async def test_database_methods():
    """Prueba los métodos de base de datos"""
    logger.info("🧪 Probando métodos de base de datos...")

    db = DatabaseManager()

    try:
        # Crear usuario de prueba con ID único
        user_id = int(time.time() * 1000000) % 1000000000 + 200
        await db.add_user(user_id, "testuser4", "Test User 4")

        # Probar get_user_points (debería ser None inicialmente)
        points = await db.get_user_points(user_id)
        assert points is None, "Usuario nuevo no debería tener puntos"
        logger.info("✅ get_user_points correcto para usuario nuevo")

        # Probar create_or_update_user_points
        points = await db.create_or_update_user_points(user_id, 10.0)
        assert points.total_points == 10.0, "Debería crear puntos"
        logger.info("✅ create_or_update_user_points correcto")

        # Probar get_user_points nuevamente
        points = await db.get_user_points(user_id)
        assert points.total_points == 10.0, "Debería recuperar puntos"
        logger.info("✅ get_user_points correcto para usuario existente")

        # Probar add_points_transaction
        transaction = await db.add_points_transaction(
            points.id, 'test', 5.0, 'Prueba de transacción'
        )
        assert transaction.amount == 5.0, "Debería crear transacción"
        logger.info("✅ add_points_transaction correcto")

        # Probar get_points_history
        history = await db.get_points_history(user_id)
        assert len(history) > 0, "Debería haber historial"
        logger.info(f"✅ get_points_history correcto: {len(history)} transacciones")

        logger.info("🎉 Métodos de base de datos funcionan correctamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error en pruebas de base de datos: {e}")
        return False
    finally:
        await db.engine.dispose()

async def main():
    """Función principal de pruebas"""
    logger.info("🚀 Iniciando pruebas del sistema de puntos y referidos")
    logger.info("=" * 60)

    results = []

    # Ejecutar pruebas
    results.append(await test_database_methods())
    results.append(await test_points_system())
    results.append(await test_referral_system())

    # Resultado final
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        logger.info(f"🎉 Todas las pruebas pasaron ({passed}/{total})")
        logger.info("")
        logger.info("✅ El sistema de puntos y referidos está listo para producción")
        logger.info("💡 Recuerda ejecutar el bot y probar los comandos /referral y /points")
    else:
        logger.error(f"❌ {total - passed} pruebas fallaron ({passed}/{total})")
        logger.info("🔧 Revisa los logs anteriores para identificar los problemas")

if __name__ == "__main__":
    asyncio.run(main())