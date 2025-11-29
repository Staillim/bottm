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
import os
import sys

app = Flask(__name__)
CORS(app)

# Inicializar base de datos
db = DatabaseManager()

@app.route('/ad_viewer.html')
def serve_webapp():
    """Sirve la Mini App de anuncios"""
    return send_file('webapp/ad_viewer.html')

@app.route('/api/ad-completed', methods=['POST'])
def ad_completed():
    """Endpoint que se llama cuando el usuario completa el anuncio"""
    data = request.json
    token = data.get('token')
    user_id = data.get('user_id')
    
    if not token:
        return jsonify({'success': False, 'error': 'Token no proporcionado'}), 400
    
    # Ejecutar código async en Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Validar token y marcar como completado
        ad_token = loop.run_until_complete(db.get_ad_token(token))
        
        if not ad_token:
            return jsonify({'success': False, 'error': 'Token inválido'}), 404
        
        if ad_token.completed:
            return jsonify({'success': False, 'error': 'Token ya usado'}), 400
        
        # Marcar token como completado
        success = loop.run_until_complete(db.complete_ad_token(token))
        
        if not success:
            return jsonify({'success': False, 'error': 'Error al completar token'}), 500
        
        # Obtener información del video
        video = loop.run_until_complete(db.get_video_by_id(ad_token.video_id))
        
        if not video:
            return jsonify({'success': False, 'error': 'Video no encontrado'}), 404
        
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
                        chat_id=ad_token.user_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="HTML"
                    )
                )
            except Exception as e:
                print(f"Error enviando poster: {e}")
        
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
        
        # Enviar mensaje de confirmación
        loop.run_until_complete(
            bot.send_message(
                chat_id=ad_token.user_id,
                text="✅ ¡Disfruta tu película!\n\nUsa /buscar para encontrar más contenido."
            )
        )
        
        return jsonify({'success': True, 'message': 'Video enviado correctamente'})
        
    except Exception as e:
        print(f"Error en ad_completed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        loop.close()

@app.route('/health')
def health():
    """Endpoint de salud para verificar que el servidor está corriendo"""
    return jsonify({'status': 'ok', 'service': 'CineStelar WebApp Server'})

def run_telegram_bot():
    """Ejecuta el bot de Telegram en un hilo separado"""
    import subprocess
    print("🤖 Iniciando Bot de Telegram...")
    subprocess.run([sys.executable, "main.py"])

if __name__ == '__main__':
    # Iniciar bot en hilo separado
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Iniciar servidor Flask
    port = int(os.environ.get('PORT', FLASK_PORT))
    print(f"🌐 Servidor Flask iniciado en puerto {port}")
    print(f"📱 Mini App disponible en: /ad_viewer.html")
    print(f"🤖 Bot de Telegram ejecutándose en segundo plano")
    
    app.run(host='0.0.0.0', port=port, debug=False)
