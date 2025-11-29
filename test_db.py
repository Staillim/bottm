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

        # Probar buscar un video específico (mensaje 859)
        video_859 = await db.get_video_by_message_id(859)
        if video_859:
            print(f"📹 Video 859 encontrado: {video_859.title}")
        else:
            print("📭 Video 859 no encontrado en BD")

    except Exception as e:
        print(f"❌ Error en la conexión a BD: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())