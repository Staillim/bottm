import asyncio
from database.db_manager import DatabaseManager

async def test_db_init():
    try:
        db = DatabaseManager()
        await db.init_db()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_init())