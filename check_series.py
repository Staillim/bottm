import asyncio
from database.db_manager import DatabaseManager
from sqlalchemy import select, text
from database.models import TvShow, Video

async def check_content():
    db = DatabaseManager()
    await db.init_db()
    
    # Consulta directa a la tabla tv_shows
    async with db.async_session() as session:
        # Contar series
        result = await session.execute(select(TvShow))
        all_series = result.scalars().all()
        print(f'📺 Series en tabla tv_shows: {len(all_series)}')
        
        if all_series:
            print('\nSeries encontradas:')
            for s in all_series[:10]:
                print(f'  - ID: {s.id}, Nombre: {s.name}')
    
    # Probar la función search_tv_shows
    print('\n🔍 Probando búsqueda de series...')
    
    # Buscar "Loki"
    result_loki = await db.search_tv_shows('Loki', limit=5)
    print(f'\nBúsqueda "Loki": {len(result_loki) if result_loki else 0} resultados')
    if result_loki:
        for s in result_loki:
            print(f'  - {s.name}')
    
    # Buscar "Dexter"
    result_dexter = await db.search_tv_shows('Dexter', limit=5)
    print(f'\nBúsqueda "Dexter": {len(result_dexter) if result_dexter else 0} resultados')
    if result_dexter:
        for s in result_dexter:
            print(f'  - {s.name}')
    
    # Buscar "Euphoria"
    result_euphoria = await db.search_tv_shows('Euphoria', limit=5)
    print(f'\nBúsqueda "Euphoria": {len(result_euphoria) if result_euphoria else 0} resultados')
    if result_euphoria:
        for s in result_euphoria:
            print(f'  - {s.name}')

asyncio.run(check_content())
