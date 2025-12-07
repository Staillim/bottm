import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from config.settings import BOT_TOKEN
from database.db_manager import DatabaseManager
from handlers.start import start_command, verify_callback
from handlers.search import search_command, video_callback
from handlers.admin import (
    indexar_command, stats_command, indexar_manual_command, 
    reindexar_command, handle_reindex_callback
)
from handlers.repost import (
    repost_command, handle_repost_callback, handle_repost_channel_input
)
from handlers.text_handler import handle_text_message
from handlers.callbacks import handle_callback
from handlers.series_admin import index_series_command, index_episode_reply, finish_indexing_command
from handlers.admin_menu import admin_menu_command, admin_callback_handler, process_new_episode
from handlers.indexing_callbacks import handle_title_input

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def help_command(update, context):
    help_text = """
📚 *Ayuda del Bot*

*Comandos disponibles:*
/start - Iniciar y ver menu principal
/buscar <termino> - Buscar videos (modo antiguo)
/search <termino> - Search videos (English)
/help - Mostrar esta ayuda

*Comandos de Administracion:*
/indexar - Indexar nuevas peliculas automaticamente
/indexar_manual <msg_id> - Indexar pelicula especifica
/reindexar <msg_id> - Re-indexar pelicula existente
/repost - Re-publicar videos antiguos en nuevo canal
/indexar_serie <serie> - Indexar nueva serie
/terminar_indexacion - Finalizar indexacion de serie
/stats - Ver estadisticas del bot

*Como usar:*
1. Unete al canal de verificacion
2. Verifica tu membresia
3. Usa el menu interactivo para elegir peliculas o series
4. Busca por nombre y selecciona lo que quieres ver

*Ejemplos de busqueda:*
- Thor
- Loki (2021)
- Breaking Bad
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def post_init(application):
    """Ya no se usa - inicialización movida a main()"""
    pass
    
    logger.info("Base de datos inicializada")

def main():
    """Iniciar el bot"""
    # Inicializar base de datos
    db = DatabaseManager()
    asyncio.run(db.init_db())
    
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Guardar en bot_data
    application.bot_data['db'] = db
    
    # Handlers de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler(["buscar", "search"], search_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_menu_command))
    application.add_handler(CommandHandler("indexar", indexar_command))
    application.add_handler(CommandHandler("indexar_manual", indexar_manual_command))
    application.add_handler(CommandHandler("reindexar", reindexar_command))
    application.add_handler(CommandHandler("repost", repost_command))
    application.add_handler(CommandHandler("indexar_serie", index_series_command))
    application.add_handler(CommandHandler("terminar_indexacion", finish_indexing_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Handlers de callbacks (nuevo sistema unificado tiene prioridad)
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(handle_reindex_callback, pattern="^ridx_"))
    application.add_handler(CallbackQueryHandler(handle_repost_callback, pattern="^repost_"))
    application.add_handler(CallbackQueryHandler(handle_callback, pattern="^(menu_|movie_|series_|season_|episode_)"))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
    application.add_handler(CallbackQueryHandler(video_callback, pattern="^video_"))
    
    # Handler de mensajes de texto (búsqueda contextual)
    async def text_handler_with_auto_index(update, context):
        # Intentar manejar input de canal para repost
        await handle_repost_channel_input(update, context)
        
        # Intentar manejar input de título para indexación
        if await handle_title_input(update, context):
            return  # Fue manejado por el sistema de indexación
        
        # Procesar nuevo episodio si está activa la espera
        handled = await process_new_episode(update, context)
        if not handled:
            # Procesar como mensaje normal
            await handle_text_message(update, context)
    
    # Handler para respuestas con formato #x# (puede contener texto adicional)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'\d+[xX]\d+'),
        index_episode_reply
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_handler_with_auto_index
    ))
    
    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
