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
/start - Iniciar y verificar membresía
/buscar <término> - Buscar videos
/search <término> - Search videos (English)
/help - Mostrar esta ayuda

*Cómo usar:*
1. Únete al canal de verificación
2. Verifica tu membresía
3. Usa /buscar seguido del término que buscas
4. Selecciona el video de los resultados

*Ejemplos:*
/buscar bad mc
/search action movies
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
    application.add_handler(CommandHandler("indexar", indexar_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Handlers de callbacks
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_membership$"))
    application.add_handler(CallbackQueryHandler(video_callback, pattern="^video_"))
    
    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
