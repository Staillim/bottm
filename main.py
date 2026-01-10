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
    reindexar_command, handle_reindex_callback, reindexar_titulos_command
)
from handlers.repost import (
    repost_command, handle_repost_callback, handle_repost_channel_input
)
from handlers.text_handler import handle_text_message
from handlers.callbacks import handle_callback
from handlers.series_admin import index_series_command, index_episode_reply, finish_indexing_command
from handlers.admin_menu import admin_menu_command, admin_callback_handler, process_new_episode
from handlers.indexing_callbacks import handle_title_input, handle_indexing_callback
from handlers.broadcast import broadcast_menu_command, handle_broadcast_callback, handle_custom_message_input
from handlers.tickets import (
    mis_tickets_command, invitar_command, mis_referidos_command,
    handle_tickets_callback
)
from handlers.admin_users import (
    admin_users_command, handle_admin_user_callback, handle_admin_user_input
)
from handlers.group_search import handle_group_message, group_search_command
from handlers.stats_channels import (
    stats_canales_command, add_canal_command, list_canales_command,
    handle_stats_callback
)

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
/mistickets - Ver tus tickets disponibles
/invitar - Obtener tu link de invitación
/misreferidos - Ver tus referidos
/help - Mostrar esta ayuda

*Comandos de Administracion:*
/admin - Panel de administración
/usuarios - Gestionar usuarios
/broadcast - Enviar mensajes masivos
/indexar - Indexar nuevas peliculas automaticamente
/indexar_manual <msg_id> - Indexar pelicula especifica
/reindexar <msg_id> - Re-indexar pelicula existente
/reindexar_titulos - Actualizar todos los títulos con captions originales
/repost - Re-publicar videos antiguos en nuevo canal
/indexar_serie <serie> - Indexar nueva serie
/terminar_indexacion - Finalizar indexacion de serie
/stats - Ver estadisticas del bot

*Sistema de Tickets:*
🎟️ Usa tickets para ver contenido sin anuncios
👥 Invita amigos y gana 5 tickets por cada uno que se verifique

*Como usar:*
1. Unete al canal de verificacion
2. Verifica tu membresia
3. Usa el menu interactivo para elegir peliculas o series
4. Busca por nombre y selecciona lo que quieres ver
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
    application.add_handler(CommandHandler("broadcast", broadcast_menu_command))
    application.add_handler(CommandHandler("indexar", indexar_command))
    application.add_handler(CommandHandler("indexar_manual", indexar_manual_command))
    application.add_handler(CommandHandler("reindexar", reindexar_command))
    application.add_handler(CommandHandler("reindexar_titulos", reindexar_titulos_command))
    application.add_handler(CommandHandler("repost", repost_command))
    application.add_handler(CommandHandler("indexar_serie", index_series_command))
    application.add_handler(CommandHandler("terminar_indexacion", finish_indexing_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Comandos de estadísticas de canales
    application.add_handler(CommandHandler("stats_canales", stats_canales_command))
    application.add_handler(CommandHandler("add_canal", add_canal_command))
    application.add_handler(CommandHandler("list_canales", list_canales_command))
    
    # Comandos de tickets y referidos
    application.add_handler(CommandHandler("mistickets", mis_tickets_command))
    application.add_handler(CommandHandler("invitar", invitar_command))
    application.add_handler(CommandHandler("misreferidos", mis_referidos_command))
    application.add_handler(CommandHandler("usuarios", admin_users_command))
    
    # Comando de búsqueda en grupos
    application.add_handler(CommandHandler("search_group", group_search_command))
    
    # Handlers de callbacks (nuevo sistema unificado tiene prioridad)
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(handle_broadcast_callback, pattern="^broadcast_"))
    application.add_handler(CallbackQueryHandler(handle_indexing_callback, pattern="^idx_"))
    application.add_handler(CallbackQueryHandler(handle_reindex_callback, pattern="^ridx_"))
    application.add_handler(CallbackQueryHandler(handle_repost_callback, pattern="^repost_"))
    application.add_handler(CallbackQueryHandler(handle_tickets_callback, pattern="^tickets_"))
    application.add_handler(CallbackQueryHandler(handle_admin_user_callback, pattern="^admu_"))
    application.add_handler(CallbackQueryHandler(handle_stats_callback, pattern="^stats_"))
    application.add_handler(CallbackQueryHandler(handle_callback, pattern="^(menu_|movie_|series_|season_|episode_|use_ticket_)"))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
    application.add_handler(CallbackQueryHandler(video_callback, pattern="^video_"))
    
    # Handler de mensajes de texto (búsqueda contextual)
    async def text_handler_with_auto_index(update, context):
        # Primero verificar si es mensaje de grupo para búsqueda inteligente
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            await handle_group_message(update, context)
            return
        
        # Intentar manejar input de canal para repost
        await handle_repost_channel_input(update, context)
        
        # Intentar manejar input de gestión de usuarios admin
        if await handle_admin_user_input(update, context):
            return
        
        # Intentar manejar mensaje personalizado de broadcast
        if await handle_custom_message_input(update, context):
            return
        
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
    
    # Handler para multimedia
    async def handle_multimedia_message(update, context):
        # Intentar manejar mensaje personalizado de broadcast primero
        if await handle_custom_message_input(update, context):
            return
        
        # Si no fue manejado por broadcast, proceso normal
        user_id = update.effective_user.id
        media_type = "unknown"
        if update.message.photo:
            media_type = "photo"
        elif update.message.video:
            media_type = "video"
        elif update.message.audio:
            media_type = "audio"
        elif update.message.document:
            media_type = "document"
        
        logger.info(f"User {user_id} sent {media_type}")
    
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document.ALL,
        handle_multimedia_message
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
