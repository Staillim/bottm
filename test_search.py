import asyncio
from database.db_manager import DatabaseManager
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def test_search():
    print("🔄 Inicializando base de datos...")
    db = DatabaseManager()
    await db.init_db()
    
    query = "Agentes"
    print(f"\n🔍 Buscando: '{query}'")
    
    try:
        videos = await db.search_videos(query)
        
        if not videos:
            print("❌ No se encontraron resultados.")
        else:
            print(f"✅ Encontrados {len(videos)} resultados:")
            for idx, video in enumerate(videos, 1):
                print(f"   {idx}. {video.title} ({video.year})")
                print(f"      ID: {video.id}")
                print(f"      Original: {video.original_title}")
                print(f"      TMDB ID: {video.tmdb_id}")
                
    except Exception as e:
        print(f"❌ Error durante la búsqueda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())