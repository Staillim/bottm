"""
Servidor Flask para el bot de CineStelar
"""
from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import asyncio
from database.db_manager import DatabaseManager
from telegram import Bot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID
import os

app = Flask(__name__)
CORS(app)

# Inicializar base de datos global
db = None
# Inicializar bot global
bot = None

async def init_database():
    """Inicializar la base de datos de forma asíncrona"""
    global db
    if db is None:
        print("🔄 Inicializando base de datos...")
        db = DatabaseManager()
        await db.init_db()
        print("✅ Base de datos inicializada correctamente")

async def init_bot():
    """Inicializar el bot de Telegram"""
    global bot
    if bot is None:
        bot = Bot(token=BOT_TOKEN)
        print("✅ Bot de Telegram inicializado")

@app.route('/')
def home():
    """Página de inicio"""
    return jsonify({'status': 'ok', 'service': 'CineStelar API Server'})

@app.route('/ad_viewer.html')
def serve_webapp():
    """Sirve la Mini App de anuncios"""
    return send_file('webapp/ad_viewer.html')

@app.route('/api/ad-completed', methods=['POST'])
def ad_completed():
    """Endpoint que se llama cuando el usuario completa el anuncio"""
    global db

    try:
        data = request.json
        token = data.get('token')
        user_id = data.get('user_id')

        print(f"📡 Recibida petición ad-completed: token={token[:10] if token else None}..., user_id={user_id}")

        # Verificar que el token y user_id estén presentes
        if not token:
            print("❌ Token no proporcionado")
            return jsonify({'success': False, 'error': 'Token no proporcionado'}), 400

        if not user_id:
            print("❌ User ID no proporcionado")
            return jsonify({'success': False, 'error': 'User ID no proporcionado'}), 400

        # Inicializar DB si no está inicializada (lazy initialization)
        if db is None:
            print("🔄 Inicializando DB...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                db = DatabaseManager()
                loop.run_until_complete(db.init_db())
                loop.close()
                print("✅ DB inicializada")
            except Exception as e:
                print(f"❌ Error inicializando DB: {e}")
                return jsonify({'success': False, 'error': 'Error de base de datos'}), 500

        # Inicializar bot si no está inicializado
        if bot is None:
            print("🔄 Inicializando bot...")
            try:
                bot = Bot(token=BOT_TOKEN)
                print("✅ Bot inicializado")
            except Exception as e:
                print(f"❌ Error inicializando bot: {e}")
                return jsonify({'success': False, 'error': 'Error de bot'}), 500

        # Ejecutar operaciones async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Validar token
            ad_token = loop.run_until_complete(db.get_ad_token(token))

            if not ad_token:
                print(f"❌ Token inválido: {token[:10]}...")
                return jsonify({'success': False, 'error': 'Token inválido'}), 404

            if ad_token.completed:
                print(f"⚠️ Token ya usado: {token[:10]}...")
                return jsonify({'success': False, 'error': 'Token ya usado'}), 400

            print(f"✅ Token válido para user_id={ad_token.user_id}, video_id={ad_token.video_id}")

            # Marcar token como completado
            success = loop.run_until_complete(db.complete_ad_token(token))

            if not success:
                print("❌ Error al completar token")
                return jsonify({'success': False, 'error': 'Error al completar token'}), 500

            # Obtener información del video
            video = loop.run_until_complete(db.get_video_by_id(ad_token.video_id))

            if not video:
                print(f"❌ Video no encontrado: {ad_token.video_id}")
                return jsonify({'success': False, 'error': 'Video no encontrado'}), 404

            print(f"🎬 Enviando video: {video.title}")

            # Verificar que el bot esté inicializado
            if bot is None:
                print("❌ Bot no inicializado")
                return jsonify({'success': False, 'error': 'Bot no disponible'}), 500

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
                            chat_id=ad_token.user_id,
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
                    chat_id=ad_token.user_id,
                    video=video.file_id,
                    caption=caption_text,
                    parse_mode='Markdown'
                )
            )
            print("🎥 Video enviado")

            # Enviar mensaje de confirmación
            loop.run_until_complete(
                bot.send_message(
                    chat_id=ad_token.user_id,
                    text="✅ ¡Disfruta tu película!\n\nUsa /buscar para encontrar más contenido."
                )
            )
            print("💬 Mensaje de confirmación enviado")

            return jsonify({'success': True, 'message': 'Video enviado correctamente'})

        except Exception as e:
            print(f"❌ Error procesando anuncio: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Error general en ad_completed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@app.route('/test')
def test():
    """Endpoint de prueba"""
    return jsonify({'status': 'ok', 'message': 'Test endpoint working v2', 'db_initialized': db is not None, 'bot_initialized': bot is not None})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Servidor Flask iniciado en puerto {port}")
    print(f"📱 Mini App disponible en: /ad_viewer.html")
    print(f"🤖 API lista para recibir peticiones de anuncios")

    app.run(host='0.0.0.0', port=port, debug=False)