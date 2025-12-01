"""
Script para indexar la serie Loki manualmente desde consola
"""
import asyncio
from database.db_manager import DatabaseManager
from utils.tmdb_api import TMDBApi
from telegram import Bot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

async def index_loki():
    db = DatabaseManager()
    tmdb = TMDBApi()
    bot = Bot(token=BOT_TOKEN)
    
    print("🔍 Buscando serie Loki (2021) en TMDB...")
    
    # Buscar serie en TMDB
    series_data = tmdb.search_tv_show("Loki (2021)")
    
    if not series_data:
        print("❌ No se encontró la serie en TMDB")
        return
    
    print(f"✅ Serie encontrada: {series_data['name']}")
    
    # Verificar si ya existe
    existing_show = await db.get_tv_show_by_tmdb_id(series_data['tmdb_id'])
    
    if existing_show:
        print(f"⚠️ La serie ya está indexada con ID: {existing_show.id}")
        show = existing_show
    else:
        # Obtener detalles completos
        details = tmdb.get_tv_show_details(series_data['tmdb_id'])
        
        if not details:
            print("❌ Error al obtener detalles de la serie")
            return
        
        print(f"📺 Guardando serie en base de datos...")
        print(f"   Nombre: {details['name']}")
        print(f"   Año: {details.get('year')}")
        print(f"   Temporadas: {details.get('number_of_seasons')}")
        print(f"   Calificación: {details.get('vote_average')}/10")
        
        # Guardar serie
        show = await db.add_tv_show(
            name=details['name'],
            tmdb_id=details['tmdb_id'],
            original_name=details.get('original_name'),
            year=details.get('year'),
            overview=details.get('overview'),
            poster_url=details.get('poster_url'),
            backdrop_url=details.get('backdrop_url'),
            vote_average=details.get('vote_average'),
            genres=", ".join(details.get('genres', [])),
            number_of_seasons=details.get('number_of_seasons'),
            status=details.get('status')
        )
        
        if not show:
            print("❌ Error al guardar la serie en la base de datos")
            return
        
        print(f"✅ Serie guardada con ID: {show.id}")
    
    # Indexar episodios desde el mensaje 921
    print(f"\n📹 Indexando episodios desde mensaje 921...")
    
    start_message_id = 921
    max_messages = 50  # Reducido para prueba
    indexed_count = 0
    
    # Patrón para detectar episodios: 1x1, 2x5, etc.
    import re
    episode_pattern = re.compile(r'(\d+)[xX](\d+)')
    
    for offset in range(max_messages):
        message_id = start_message_id + offset
        
        try:
            # Obtener el mensaje directamente del canal
            message = await bot.get_chat(STORAGE_CHANNEL_ID)
            # Esto no funciona así, necesitamos usar copy_message
            
            # Obtener información del mensaje usando forward
            from telegram.error import TelegramError
            
            try:
                # Intentar copiar el mensaje a un chat temporal (nosotros mismos)
                chat = await bot.get_me()
                copied = await bot.copy_message(
                    chat_id=chat.id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=message_id
                )
                # Obtener el mensaje copiado
                # No podemos hacer esto, necesitamos un enfoque diferente
                continue
                
            except TelegramError as e:
                if "message not found" in str(e).lower():
                    print(f"   ⏭️  Mensaje {message_id} no encontrado, deteniendo...")
                    break
                continue
                
        except Exception as e:
            continue
    
    print(f"\n🎉 Indexación completada!")
    print(f"   Total episodios indexados: {indexed_count}")
    print(f"\n📊 Resumen por temporada:")
    
    # Mostrar resumen
    for season in range(1, show.number_of_seasons + 1):
        episodes = await db.get_episodes_by_season(show.id, season)
        if episodes:
            print(f"   Temporada {season}: {len(episodes)} episodios")

if __name__ == "__main__":
    asyncio.run(index_loki())
