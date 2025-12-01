"""
Handler para mensajes de texto - Búsqueda contextual de películas/series
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from handlers.menu import show_movie_results, show_series_results

db = DatabaseManager()

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto según el estado de navegación del usuario"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Ignorar comandos
    if message_text.startswith('/'):
        return
    
    # Obtener estado del usuario
    user_state = await db.get_user_state(user_id)
    
    if not user_state:
        # Usuario no tiene estado activo, mostrar menú principal
        from handlers.menu import main_menu
        await main_menu(update, context)
        return
    
    current_menu = user_state.current_menu
    
    # Si está en modo búsqueda de películas
    if current_menu == "movies":
        await search_movies(update, context, message_text)
    
    # Si está en modo búsqueda de series
    elif current_menu == "series":
        await search_series(update, context, message_text)
    
    else:
        # Estado desconocido, volver al menú
        from handlers.menu import main_menu
        await main_menu(update, context)

async def search_movies(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Busca películas en la base de datos"""
    # Buscar en base de datos
    results = await db.search_videos(query, limit=10)
    
    # Mostrar resultados
    await show_movie_results(update, context, results, query)

async def search_series(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Busca series en la base de datos"""
    # Buscar en base de datos
    results = await db.search_tv_shows(query, limit=10)
    
    # Mostrar resultados
    await show_series_results(update, context, results, query)
