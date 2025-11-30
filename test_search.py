import asyncio
from database.db_manager import DatabaseManager

async def test_search():
    try:
        db = DatabaseManager()
        await db.init_db()
        print("✅ Conexión a la base de datos exitosa")

        # Probar diferentes búsquedas
        test_queries = ["hulk", "Hulk", "increible", "2008", "cadáver", "novia"]

        for query in test_queries:
            print(f"\n🔍 Probando búsqueda: '{query}'")
            videos = await db.search_videos(query)
            print(f"   Resultados: {len(videos)}")
            for video in videos:
                print(f"   - {video.title}")

        # Probar normalización
        print("\n🔧 Probando normalización:")
        test_texts = ["El Increible Hulk (2008)", "AHORA O NUNCA (2024)", "El Cadáver De La Novia"]
        for text in test_texts:
            normalized = db.normalize_text(text)
            print(f"   '{text}' -> '{normalized}'")

        # Verificar si "hulk" está en "el increible hulk (2008)"
        query = "hulk"
        title = "El Increible Hulk (2008)"
        norm_query = db.normalize_text(query)
        norm_title = db.normalize_text(title)
        print(f"\n🔍 Verificación manual:")
        print(f"   Query normalizado: '{norm_query}'")
        print(f"   Título normalizado: '{norm_title}'")
        print(f"   '{norm_query}' in '{norm_title}': {norm_query in norm_title}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())