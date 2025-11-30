#!/usr/bin/env python3
"""
Script de diagnóstico para el bot en producción.
Ejecutar este script en Render para verificar el estado del bot.
"""
import asyncio
import os
from config.settings import DATABASE_URL, VERIFICATION_CHANNEL_ID
from database.db_manager import DatabaseManager

async def diagnose_bot():
    print("🔍 Diagnóstico del Bot CineStelar")
    print("=" * 50)

    # 1. Verificar variables de entorno críticas
    print("1. Variables de entorno:")
    critical_vars = ['DATABASE_URL', 'BOT_TOKEN', 'VERIFICATION_CHANNEL_ID', 'STORAGE_CHANNEL_ID']
    for var in critical_vars:
        value = os.getenv(var)
        status = "✅ Configurada" if value else "❌ Faltante"
        print(f"   {var}: {status}")
        if var == 'DATABASE_URL' and value:
            print(f"      URL: {value[:50]}...")

    print()

    # 2. Probar conexión a base de datos
    print("2. Conexión a base de datos:")
    try:
        db = DatabaseManager()
        await db.init_db()
        print("   ✅ Conexión exitosa")

        # Contar videos
        from database.models import Video
        from sqlalchemy import select, func
        async with db.async_session() as session:
            result = await session.execute(select(func.count()).select_from(Video))
            count = result.scalar()
            print(f"   📊 Videos en BD: {count}")

        # Probar búsqueda
        print("   🔍 Probando búsqueda 'hulk'...")
        videos = await db.search_videos("hulk")
        print(f"   📹 Resultados: {len(videos)}")
        if videos:
            print(f"      Ejemplo: {videos[0].title}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()

    # 3. Verificar configuración del canal
    print("3. Configuración del canal:")
    print(f"   VERIFICATION_CHANNEL_ID: {VERIFICATION_CHANNEL_ID}")
    print(f"   STORAGE_CHANNEL_ID: {os.getenv('STORAGE_CHANNEL_ID')}")

    print()

    # 4. Recomendaciones
    print("4. Recomendaciones:")
    if not DATABASE_URL:
        print("   ❌ Configurar DATABASE_URL en variables de entorno")
    if not os.getenv('BOT_TOKEN'):
        print("   ❌ Configurar BOT_TOKEN en variables de entorno")
    if not VERIFICATION_CHANNEL_ID:
        print("   ❌ Configurar VERIFICATION_CHANNEL_ID en variables de entorno")

    print("   ✅ Si todo está configurado, verificar logs del bot")
    print("   ✅ Verificar que el usuario esté unido al canal de verificación")

if __name__ == "__main__":
    asyncio.run(diagnose_bot())