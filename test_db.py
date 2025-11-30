import asyncio
from database.db_manager import DatabaseManager
from database.models import Video
from sqlalchemy import select, func

async def test_db():
    try:
        db = DatabaseManager()
        await db.init_db()
        print("✅ Conexión a la base de datos exitosa")

        # Probar una consulta simple para contar videos
        async with db.async_session() as session:
            result = await session.execute(select(func.count()).select_from(Video))
            count = result.scalar()
            print(f"📊 Total de videos en BD: {count}")

        # Probar buscar videos con "hulk"
        print("\n🔍 Probando búsqueda de 'hulk'...")
        hulk_videos = await db.search_videos("hulk")
        print(f"📹 Videos encontrados con 'hulk': {len(hulk_videos)}")
        for video in hulk_videos:
            print(f"  - {video.title}")

        # Mostrar algunos videos de ejemplo
        print("\n📋 Primeros 5 videos en la BD:")
        async with db.async_session() as session:
            result = await session.execute(select(Video).limit(5))
            videos = result.scalars().all()
            for video in videos:
                print(f"  - ID: {video.id}, Título: {video.title}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())