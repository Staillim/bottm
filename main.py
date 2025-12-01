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
from handlers.admin import indexar_command, stats_command
from handlers.text_handler import handle_text_message
from handlers.callbacks import handle_callback
from handlers.series_admin import index_series_command, index_episode_reply, finish_indexing_command, process_auto_index
from handlers.admin_menu import admin_menu_command, admin_callback_handler, process_new_episode

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
/start - Iniciar y ver menú principal
/buscar <término> - Buscar videos (modo antiguo)
/search <término> - Search videos (English)
/help - Mostrar esta ayuda

*Comandos de Administración:*
/indexar <película> - Indexar nueva película
/indexar_serie <serie> - Indexar nueva serie
/terminar_indexacion - Finalizar indexación de serie
/stats - Ver estadísticas del bot

*Cómo usar:*
1. Únete al canal de verificación
2. Verifica tu membresía
3. Usa el menú interactivo para elegir películas o series
4. Busca por nombre y selecciona lo que quieres ver

*Ejemplos de búsqueda:*
• Thor
• Loki (2021)
• Breaking Bad
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def post_init(application):
    """Inicializar base de datos"""
    db = DatabaseManager()
    await db.init_db()
    application.bot_data['db'] = db
    logger.info("Base de datos inicializada")

def main():
    """Iniciar el bot"""
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Handlers de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler(["buscar", "search"], search_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_menu_command))
    application.add_handler(CommandHandler("indexar", indexar_command))
    application.add_handler(CommandHandler("indexar_serie", index_series_command))
    application.add_handler(CommandHandler("terminar_indexacion", finish_indexing_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Handlers de callbacks (nuevo sistema unificado tiene prioridad)
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(handle_callback, pattern="^(menu_|movie_|series_|season_|episode_)"))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
    application.add_handler(CallbackQueryHandler(video_callback, pattern="^video_"))
    
    # Handler de mensajes de texto (búsqueda contextual)
    # Primero procesar auto-indexación si está activa
    async def text_handler_with_auto_index(update, context):
        # Intentar procesar nuevo episodio primero
        handled = await process_new_episode(update, context)
        if handled:
            return
        
        # Intentar procesar auto-indexación
        handled = await process_auto_index(update, context)
        if not handled:
            # Si no es auto-index, procesar como mensaje normal
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
    
    # Handler para mensajes reenviados (auto-indexación)
    application.add_handler(MessageHandler(
        filters.FORWARDED,
        text_handler_with_auto_index
    ))
    
    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
