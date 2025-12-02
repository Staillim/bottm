"""Script de debug para verificar videos en la base de datos"""
import asyncio
from database.db_manager import DatabaseManager
from config.settings import DATABASE_URL

async def main():
    db = DatabaseManager(DATABASE_URL)
    await db.connect()
    
    # Obtener todos los videos
    result = await db.execute(
        "SELECT message_id, title, year, channel_message_id FROM videos ORDER BY message_id DESC LIMIT 10"
    )
    
    print("\n📊 Últimos 10 videos en la base de datos:\n")
    print(f"{'message_id':<15} {'channel_msg_id':<15} {'Título':<40} {'Año'}")
    print("-" * 100)
    
    for row in result:
        msg_id = row[0]
        title = row[1] or "Sin título"
        year = row[2] or "N/A"
        ch_msg_id = row[3] or "N/A"
        print(f"{msg_id:<15} {ch_msg_id:<15} {title:<40} {year}")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
