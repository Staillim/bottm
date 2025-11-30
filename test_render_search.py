#!/usr/bin/env python3
"""
Script para probar la búsqueda desde el entorno de Render.
Simula exactamente lo que hace el comando /buscar del bot.
"""
import asyncio
import os
from config.settings import DATABASE_URL
from database.db_manager import DatabaseManager

async def test_render_search():
    print("🧪 Prueba de búsqueda en entorno Render")
    print("=" * 50)

    # Verificar DATABASE_URL
    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada")
        return

    print(f"📍 Base de datos: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'Desconocida'}")

    try:
        # Inicializar DB como lo hace el bot
        db = DatabaseManager()
        await db.init_db()
        print("✅ Base de datos inicializada")

        # Simular búsqueda como el bot
        test_queries = ["hulk", "cadáver", "ahora"]

        for query in test_queries:
            print(f"\n🔍 Buscando: '{query}'")
            videos = await db.search_videos(query)

            if not videos:
                print(f"   😔 No se encontraron resultados para '{query}'")
            else:
                print(f"   📹 Encontrados {len(videos)} video(s):")
                for video in videos:
                    print(f"      - {video.title}")

        # Mostrar estadísticas
        from database.models import Video, Search
        from sqlalchemy import select, func

        async with db.async_session() as session:
            # Contar videos
            video_count = await session.execute(select(func.count()).select_from(Video))
            print(f"\n📊 Estadísticas:")
            print(f"   Total videos: {video_count.scalar()}")

            # Contar búsquedas
            search_count = await session.execute(select(func.count()).select_from(Search))
            print(f"   Total búsquedas registradas: {search_count.scalar()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_render_search())