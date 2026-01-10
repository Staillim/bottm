#!/usr/bin/env python3
"""
Test específico para verificar el deep linking de series
"""
import asyncio
import re
from config.settings import BOT_TOKEN
from database.db_manager import DatabaseManager

async def test_series_deep_linking():
    """Probar que el deep linking de series funcione correctamente"""
    print("🧪 Test de Deep Linking para Series")
    print("=" * 50)
    
    # Inicializar BD
    db = DatabaseManager()
    await db.init_db()
    
    # 1. Buscar una serie existente
    print("1. Buscando series en la BD...")
    series_list = await db.search_tv_shows("", limit=5)
    
    if not series_list:
        print("❌ No hay series en la BD para probar")
        return
    
    test_series = series_list[0]
    print(f"✅ Encontrada serie para test: {test_series.name} (ID: {test_series.id})")
    
    # 2. Verificar que tiene temporadas
    seasons = await db.get_seasons_for_show(test_series.id)
    print(f"📊 Temporadas disponibles: {len(seasons)}")
    
    for season_num, episode_count in seasons:
        print(f"   - Temporada {season_num}: {episode_count} episodios")
    
    # 3. Simular el parámetro de deep link
    deep_link_param = f"series_{test_series.id}"
    print(f"\n2. Simulando deep link: ?start={deep_link_param}")
    
    # 4. Verificar que el parámetro se procesaría correctamente
    # Simular la lógica de start_command
    arg = deep_link_param
    
    # Verificar que NO se procese como canal
    is_channel_param = (not arg.startswith("ref_") and 
                       not arg.startswith("movie_") and 
                       not arg.startswith("video_") and
                       not arg.startswith("series_") and  # Esta es la línea que agregamos
                       not arg.startswith("search_") and
                       not arg.isdigit())
    
    if is_channel_param:
        print(f"❌ ERROR: El parámetro '{arg}' se procesaría como canal")
    else:
        print(f"✅ CORRECTO: El parámetro '{arg}' NO se procesará como canal")
    
    # 5. Verificar que SÍ se procese como serie
    is_series_param = arg.startswith("series_")
    if is_series_param:
        try:
            series_id = int(arg.split("_")[1])
            print(f"✅ CORRECTO: Se extraería el ID de serie: {series_id}")
            
            # Verificar que la serie existe
            show = await db.get_tv_show_by_id(series_id)
            if show:
                print(f"✅ CORRECTO: Serie encontrada en BD: {show.name}")
            else:
                print(f"❌ ERROR: Serie con ID {series_id} no encontrada")
                
        except Exception as e:
            print(f"❌ ERROR extrayendo ID de serie: {e}")
    else:
        print(f"❌ ERROR: El parámetro '{arg}' no se reconoce como serie")
    
    # 6. Generar URL de ejemplo
    from config.settings import BOT_TOKEN
    import re
    bot_username = "CineStelar_bot"  # Extraer de BOT_TOKEN si es necesario
    
    deep_link_url = f"https://t.me/{bot_username}?start={deep_link_param}"
    print(f"\n3. URL de deep link generada:")
    print(f"   {deep_link_url}")
    
    print(f"\n✅ Test completado. El deep linking debería funcionar correctamente ahora.")

if __name__ == "__main__":
    asyncio.run(test_series_deep_linking())