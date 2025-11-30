import os
import asyncio
from database.db_manager import DatabaseManager
from config.settings import DATABASE_URL

async def test_env_db():
    print("🔧 Probando conexión con variables de entorno del bot")
    print(f"DATABASE_URL configurada: {'✅ Sí' if DATABASE_URL else '❌ No'}")

    if not DATABASE_URL:
        print("❌ DATABASE_URL no está configurada")
        return

    print(f"DATABASE_URL: {DATABASE_URL[:50]}...")  # Solo mostrar parte por seguridad

    try:
        # Crear instancia del DatabaseManager (que usa DATABASE_URL)
        db = DatabaseManager()
        await db.init_db()
        print("✅ Conexión exitosa con DATABASE_URL")

        # Probar búsqueda
        print("\n🔍 Probando búsqueda con 'hulk'...")
        videos = await db.search_videos("hulk")
        print(f"📹 Videos encontrados: {len(videos)}")
        for video in videos:
            print(f"  - {video.title}")

        # Contar total de videos
        from database.models import Video
        from sqlalchemy import select, func
        async with db.async_session() as session:
            result = await session.execute(select(func.count()).select_from(Video))
            count = result.scalar()
            print(f"📊 Total videos en BD: {count}")

    except Exception as e:
        print(f"❌ Error conectando con DATABASE_URL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_env_db())