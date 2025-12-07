"""
Servidor unificado que ejecuta Flask (API) y Bot de Telegram simultáneamente.
Diseñado para correr en Render.com
"""
from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import asyncio
import threading
from database.db_manager import DatabaseManager
from telegram import Bot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID, FLASK_PORT
from sqlalchemy import text
import os
import sys

app = Flask(__name__)
CORS(app)
# Inicializar base de datos
db = None

async def run_migration():
    """Ejecuta la migración de base de datos si es necesaria"""
    try:
        async with db.engine.begin() as conn:
            # Verificar si las columnas ya existen
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ad_tokens' 
                AND column_name IN ('expires_at', 'ip_address')
            """))
            
            existing_columns = [row[0] for row in result]
            
            # Agregar expires_at si no existe
            if 'expires_at' not in existing_columns:
                print("🔧 Agregando columna expires_at...")
                await conn.execute(text("""
                    ALTER TABLE ad_tokens 
                    ADD COLUMN expires_at TIMESTAMP WITHOUT TIME ZONE
                """))
                print("✅ Columna expires_at agregada")
            
            # Agregar ip_address si no existe
            if 'ip_address' not in existing_columns:
                print("🔧 Agregando columna ip_address...")
                await conn.execute(text("""
                    ALTER TABLE ad_tokens 
                    ADD COLUMN ip_address VARCHAR(50)
                """))
                print("✅ Columna ip_address agregada")
        
        if 'expires_at' not in existing_columns or 'ip_address' not in existing_columns:
            print("✅ Migración completada")
    except Exception as e:
        print(f"⚠️ Error en migración (puede ser normal si ya existe): {e}")

async def init_db():
    """Inicializar base de datos de forma asíncrona"""
    global db
    if db is None:
        db = DatabaseManager()
        await db.init_db()
        print("✅ Base de datos inicializada")
        
        # Ejecutar migración automática
        await run_migration()

@app.route('/ad_viewer.html')
def serve_webapp():
    """Sirve la Mini App de anuncios (versión simplificada)"""
    return send_file('webapp/ad_viewer_simple.html')

def process_video_delivery(user_id, content_id, content_type='movie'):
    """Procesa el envío del video/episodio en segundo plano"""
    print(f"🔄 Iniciando proceso de envío en background para user_id={user_id}, content_type={content_type}")
    
    # Crear nuevo loop para este hilo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Crear instancia de DB local
    local_db = DatabaseManager()

    try:
        # Inicializar DB
        loop.run_until_complete(local_db.init_db())

        if content_type == 'episode':
            # Es un episodio de serie
            episode = loop.run_until_complete(local_db.get_episode_by_id(content_id))
            if not episode:
                print(f"❌ Episodio no encontrado en background: {content_id}")
                return
            
            show = loop.run_until_complete(local_db.get_tv_show_by_id(episode.tv_show_id))
            if not show:
                print(f"❌ Serie no encontrada en background: {episode.tv_show_id}")
                return
            
            print(f"📺 Enviando episodio: {show.name} S{episode.season_number}x{episode.episode_number:02d} a user_id={user_id}")
            
            # Enviar episodio
            bot = Bot(token=BOT_TOKEN)
            
            # Preparar caption
            caption = f"📺 <b>{show.name}</b>\n"
            caption += f"🎬 Temporada {episode.season_number}, Episodio {episode.episode_number}\n"
            if episode.title:
                caption += f"📝 {episode.title}\n"
            if episode.air_date:
                caption += f"📅 {episode.air_date}\n"
            if episode.overview:
                caption += f"\n{episode.overview}\n"
            
            try:
                loop.run_until_complete(
                    bot.send_video(
                        chat_id=user_id,
                        video=episode.file_id,
                        caption=caption,
                        parse_mode='HTML',
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=60
                    )
                )
                print("✅ Episodio enviado exitosamente")
            except Exception as e:
                print(f"❌ Error enviando episodio: {e}")
                try:
                    loop.run_until_complete(
                        bot.send_message(
                            chat_id=user_id,
                            text="❌ Hubo un error al enviar el episodio. Por favor intenta de nuevo más tarde."
                        )
                    )
                except:
                    pass
                return
            
            # Mensaje de confirmación
            loop.run_until_complete(
                bot.send_message(
                    chat_id=user_id,
                    text="✅ ¡Disfruta el episodio!\n\nUsa /start para continuar navegando."
                )
            )
            
        else:
            # Es una película (código existente)
            video = loop.run_until_complete(local_db.get_video_by_id(content_id))

            if not video:
                print(f"❌ Video no encontrado en background: {content_id}")
                return

            print(f"🎬 Enviando video: {video.title} a user_id={user_id}")

            # Enviar el video al usuario
            bot = Bot(token=BOT_TOKEN)

        # Si tiene poster, enviarlo primero
        if video.poster_url:
            try:
                import io
                import requests as req

                response = req.get(video.poster_url, timeout=10)
                response.raise_for_status()
                photo = io.BytesIO(response.content)
                photo.name = "poster.jpg"

                caption = f"🎬 <b>{video.title}</b>\n"
                if video.year:
                    caption += f"📅 {video.year}\n"
                if video.vote_average:
                    caption += f"⭐ {video.vote_average/10:.1f}/10\n"
                if video.runtime:
                    caption += f"⏱️ {video.runtime} min\n"
                if video.genres:
                    caption += f"🎭 {video.genres}\n"
                if video.overview:
                    caption += f"\n📝 {video.overview}\n"

                loop.run_until_complete(
                    bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="HTML"
                    )
                )
                print("📸 Poster enviado")
            except Exception as e:
                print(f"⚠️ Error enviando poster: {e}")

        # Enviar video
        print(f"🎥 Intentando enviar video file_id: {video.file_id}")
        caption_text = f"📹 *{video.title}*"
        if video.description:
            caption_text += f"\n\n{video.description}"

        try:
            loop.run_until_complete(
                bot.send_video(
                    chat_id=user_id,
                    video=video.file_id,
                    caption=caption_text,
                    parse_mode='Markdown',
                    read_timeout=60,
                    write_timeout=60,
                    connect_timeout=60
                )
            )
            print("✅ Video enviado exitosamente")
        except Exception as e:
            print(f"❌ Error enviando video: {e}")
            # Intentar enviar mensaje de error al usuario
            try:
                loop.run_until_complete(
                    bot.send_message(
                        chat_id=user_id,
                        text="❌ Hubo un error al enviar el archivo de video. Por favor intenta de nuevo más tarde."
                    )
                )
            except:
                pass
            return # Salir si falla el video

        # Enviar mensaje de confirmación
        loop.run_until_complete(
            bot.send_message(
                chat_id=user_id,
                text="✅ ¡Disfruta tu película!\n\nUsa /buscar para encontrar más contenido."
            )
        )
        print("💬 Mensaje de confirmación enviado")

    except Exception as e:
        print(f"❌ Error en background process: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cerrar conexión a DB y Loop
        try:
            loop.run_until_complete(local_db.engine.dispose())
        except:
            pass
        loop.close()

@app.route('/api/ad-completed', methods=['POST'])
def ad_completed():
    """Endpoint que se llama cuando el usuario completa el anuncio (sin tokens, directo)"""
    try:
        data = request.json
        user_id = data.get('user_id')
        content_id = data.get('video_id')  # Puede ser video_id o episode_id
        content_type = data.get('content_type', 'movie')  # 'movie' o 'episode'

        print(f"📡 Recibida petición ad-completed: user_id={user_id}, content_id={content_id}, content_type={content_type}")

        if not user_id or not content_id:
            print("❌ user_id o content_id no proporcionado")
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        # Convertir a int si vienen como string
        try:
            user_id = int(user_id)
            content_id = int(content_id)
            print(f"✅ Convertidos a int: user_id={user_id}, content_id={content_id}")
        except ValueError as e:
            print(f"❌ Error convirtiendo IDs: {e}")
            return jsonify({'success': False, 'error': 'IDs inválidos'}), 400

        # Iniciar proceso en background
        print(f"🚀 Lanzando thread para procesar {content_type}...")
        threading.Thread(target=process_video_delivery, args=(user_id, content_id, content_type), daemon=True).start()
        
        # Responder inmediatamente
        print(f"✅ Respondiendo OK al cliente")
        return jsonify({'success': True, 'message': f'Procesando envío de {content_type}'})

    except Exception as e:
        print(f"❌ Error general en ad_completed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@app.route('/health')
def health():
    """Endpoint de salud para verificar que el servidor está corriendo"""
    return jsonify({'status': 'ok', 'service': 'CineStelar WebApp Server'})

def run_telegram_bot():
    """Ejecuta el bot de Telegram en un thread con su propio event loop"""
    try:
        print("🤖 Iniciando Bot de Telegram...")
        
        # Crear un nuevo event loop para este thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Importar componentes necesarios
        from telegram.ext import Application
        from config.settings import BOT_TOKEN
        from database.db_manager import DatabaseManager
        from telegram import Update
        
        # Importar handlers
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
        from handlers.indexing_callbacks import handle_title_input, handle_indexing_callback
        from handlers.broadcast import broadcast_menu_command, handle_broadcast_callback, handle_custom_message_input
        from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
        
        # Inicializar base de datos
        db = DatabaseManager()
        loop.run_until_complete(db.init_db())
        
        # Crear aplicación
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Guardar en bot_data
        application.bot_data['db'] = db
        
        # Registrar handlers de comandos
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler(["buscar", "search"], search_command))
        
        # Help command inline
        async def help_command(update, context):
            help_text = """
📚 *Ayuda del Bot*

*Comandos disponibles:*
/start - Iniciar y ver menu principal
/buscar <termino> - Buscar videos
/help - Mostrar esta ayuda
            """
            await update.message.reply_text(help_text, parse_mode='Markdown')
        
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("admin", admin_menu_command))
        application.add_handler(CommandHandler("indexar", indexar_command))
        application.add_handler(CommandHandler("indexar_manual", indexar_manual_command))
        application.add_handler(CommandHandler("reindexar", reindexar_command))
        application.add_handler(CommandHandler("repost", repost_command))
        application.add_handler(CommandHandler("indexar_serie", index_series_command))
        application.add_handler(CommandHandler("terminar_indexacion", finish_indexing_command))
        application.add_handler(CommandHandler("stats", stats_command))
        
        # Handlers de callbacks
        application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
        application.add_handler(CallbackQueryHandler(handle_broadcast_callback, pattern="^broadcast_"))
        application.add_handler(CallbackQueryHandler(handle_indexing_callback, pattern="^idx_"))
        application.add_handler(CallbackQueryHandler(handle_reindex_callback, pattern="^ridx_"))
        application.add_handler(CallbackQueryHandler(handle_repost_callback, pattern="^repost_"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^(menu_|movie_|series_|season_|episode_)"))
        application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
        application.add_handler(CallbackQueryHandler(video_callback, pattern="^video_"))
        
        # Handler de mensajes de texto
        async def text_handler_with_auto_index(update, context):
            await handle_repost_channel_input(update, context)
            if await handle_custom_message_input(update, context):
                return
            if await handle_title_input(update, context):
                return
            handled = await process_new_episode(update, context)
            if not handled:
                await handle_text_message(update, context)
        
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r'\d+[xX]\d+'),
            index_episode_reply
        ))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler_with_auto_index
        ))
        
        print("✅ Bot configurado, iniciando polling...")
        
        # Ejecutar bot en este event loop (sin signal handlers)
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.start())
        loop.run_until_complete(application.updater.start_polling(allowed_updates=Update.ALL_TYPES))
        
        print("✅ Bot ejecutándose correctamente")
        
        # Mantener el loop corriendo
        loop.run_forever()
        
    except Exception as e:
        print(f"❌ Error ejecutando bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Inicializar base de datos
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    # Iniciar bot en hilo separado
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # Iniciar servidor Flask
    port = int(os.environ.get('PORT', FLASK_PORT))
    print(f"🌐 Servidor Flask iniciado en puerto {port}")
    print(f"📱 Mini App disponible en: /ad_viewer.html")
    print(f"🤖 Bot de Telegram ejecutándose en segundo plano")

    app.run(host='0.0.0.0', port=port, debug=False)
