#!/usr/bin/env python3
"""
Script de migración para el sistema de puntos y referidos
Ejecutar después de implementar el código
"""

import asyncio
import logging
from database.db_manager import DatabaseManager
from database.models import UserPoints, Referral, PointsTransaction
from config.settings import DATABASE_URL
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    """Ejecuta la migración de la base de datos"""

    if not DATABASE_URL:
        logger.error("DATABASE_URL no está configurada")
        return

    db = DatabaseManager()

    try:
        logger.info("Iniciando migración del sistema de puntos...")

        # Crear tablas usando SQLAlchemy metadata (más confiable)
        async with db.engine.begin() as conn:
            # Crear las tablas desde los modelos
            await conn.run_sync(UserPoints.__table__.create, checkfirst=True)
            await conn.run_sync(Referral.__table__.create, checkfirst=True)
            await conn.run_sync(PointsTransaction.__table__.create, checkfirst=True)

            logger.info("✅ Tablas creadas exitosamente usando SQLAlchemy")

        logger.info("✅ Migración completada exitosamente")
        logger.info("📊 Tablas creadas:")
        logger.info("   - user_points")
        logger.info("   - referrals")
        logger.info("   - points_transactions")
        logger.info("🔍 Índices creados para optimización")

    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        raise
    finally:
        await db.engine.dispose()

async def verify_migration():
    """Verifica que la migración se aplicó correctamente"""
    db = DatabaseManager()

    try:
        logger.info("Verificando migración...")

        async with db.async_session() as session:
            # Verificar que las tablas existen
            tables = ['user_points', 'referrals', 'points_transactions']

            for table in tables:
                result = await session.execute(text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')"))
                exists = result.scalar()
                if exists:
                    logger.info(f"✅ Tabla {table} existe")
                else:
                    logger.error(f"❌ Tabla {table} no existe")
                    return False

            # Verificar índices
            indexes = [
                'idx_referrals_code',
                'idx_referrals_referrer',
                'idx_referrals_status',
                'idx_points_transactions_user',
                'idx_points_transactions_type',
                'idx_user_points_user'
            ]

            for index in indexes:
                result = await session.execute(text(f"SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = '{index}')"))
                exists = result.scalar()
                if exists:
                    logger.info(f"✅ Índice {index} existe")
                else:
                    logger.warning(f"⚠️ Índice {index} no existe")

        logger.info("✅ Verificación completada")
        return True

    except Exception as e:
        logger.error(f"❌ Error durante verificación: {e}")
        return False
    finally:
        await db.engine.dispose()

async def main():
    """Función principal"""
    logger.info("🚀 Iniciando migración del sistema de puntos y referidos")

    # Ejecutar migración
    await run_migration()

    # Verificar migración
    await asyncio.sleep(1)  # Pequeña pausa
    success = await verify_migration()

    if success:
        logger.info("🎉 Migración completada exitosamente")
        logger.info("")
        logger.info("📋 Próximos pasos:")
        logger.info("1. Reinicia el bot para cargar los nuevos handlers")
        logger.info("2. Prueba los comandos /referral y /points")
        logger.info("3. Verifica que los deep links de referidos funcionen")
        logger.info("4. Confirma que el sistema de puntos funcione en videos")
    else:
        logger.error("❌ La migración falló. Revisa los logs anteriores.")

if __name__ == "__main__":
    asyncio.run(main())