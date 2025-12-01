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

def process_video_delivery(user_id, video_id):
    """Procesa el envío del video en segundo plano"""
    print(f"🔄 Iniciando proceso de envío en background para user_id={user_id}")
    
    # Crear nuevo loop para este hilo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Crear instancia de DB local
    local_db = DatabaseManager()

    try:
        # Inicializar DB
        loop.run_until_complete(local_db.init_db())

        # Obtener información del video
        video = loop.run_until_complete(local_db.get_video_by_id(video_id))

        if not video:
            print(f"❌ Video no encontrado en background: {video_id}")
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
        caption_text = f"📹 *{video.title}*"
        if video.description:
            caption_text += f"\n\n{video.description}"

        loop.run_until_complete(
            bot.send_video(
                chat_id=user_id,
                video=video.file_id,
                caption=caption_text,
                parse_mode='Markdown'
            )
        )
        print("🎥 Video enviado")

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
        video_id = data.get('video_id')

        print(f"📡 Recibida petición ad-completed: user_id={user_id} (type={type(user_id)}), video_id={video_id} (type={type(video_id)})")

        if not user_id or not video_id:
            print("❌ user_id o video_id no proporcionado")
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        # Convertir a int si vienen como string
        try:
            user_id = int(user_id)
            video_id = int(video_id)
            print(f"✅ Convertidos a int: user_id={user_id}, video_id={video_id}")
        except ValueError as e:
            print(f"❌ Error convirtiendo IDs: {e}")
            return jsonify({'success': False, 'error': 'IDs inválidos'}), 400

        # Iniciar proceso en background
        print(f"🚀 Lanzando thread para procesar video...")
        threading.Thread(target=process_video_delivery, args=(user_id, video_id), daemon=True).start()
        
        # Responder inmediatamente
        print(f"✅ Respondiendo OK al cliente")
        return jsonify({'success': True, 'message': 'Procesando envío de video'})

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
    """Ejecuta el bot de Telegram en un hilo separado"""
    try:
        print("🤖 Iniciando Bot de Telegram...")
        import subprocess
        result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error en bot: {result.stderr}")
        else:
            print("✅ Bot finalizado correctamente")
    except Exception as e:
        print(f"❌ Error ejecutando bot: {e}")

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
