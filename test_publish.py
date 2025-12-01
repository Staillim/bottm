"""Script para forzar publicación de un video al canal de verificación"""
import asyncio
import io
import requests as req
import urllib.parse
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import (
    BOT_TOKEN, 
    VERIFICATION_CHANNEL_ID,
    WEBAPP_URL,
    API_SERVER_URL
)

async def test_publish():
    """Publica un post de prueba en el canal"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Inicializar bot
        async with bot:
            # Obtener info del bot
            me = await bot.get_me()
            bot_username = me.username
            
            # Datos de prueba (una película conocida)
            movie_data = {
                "title": "Inception",
                "year": "2010",
                "vote_average": 8.8,
                "overview": "Un ladrón que roba secretos corporativos a través del uso de la tecnología de compartir sueños recibe la tarea inversa de plantar una idea en la mente de un CEO.",
                "poster_url": "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
                "tmdb_id": 27205
            }
            
            storage_msg_id = 999  # ID de prueba
            
            print(f"🔍 Preparando publicación de prueba...")
            print(f"   - Bot: @{bot_username}")
            print(f"   - Canal: {VERIFICATION_CHANNEL_ID}")
            print(f"   - Película: {movie_data['title']}")
            print(f"   - Poster: {movie_data['poster_url']}")
            
            # Descargar poster
            print(f"\n📥 Descargando poster...")
            poster_url = movie_data.get("poster_url")
            response = req.get(poster_url, timeout=10)
            response.raise_for_status()
            photo = io.BytesIO(response.content)
            photo.name = "poster.jpg"
            print(f"   ✅ Poster descargado ({len(response.content)} bytes)")
            
            # Crear caption
            title = movie_data.get("title", "Sin título")
            year = movie_data.get("year", "N/A")
            rating = movie_data.get("vote_average", 0)
            overview = movie_data.get("overview", "")
            
            if len(overview) > 200:
                overview = overview[:197] + "..."
            
            caption = (
                f"🎬 <b>{title}</b> ({year})\n"
                f"⭐ {rating}/10\n\n"
                f"{overview}"
            )
            
            print(f"\n📝 Caption creado:")
            print(caption)
            
            # Crear botón - En canales públicos NO se puede usar web_app, solo URL
            # El usuario hará clic y se abrirá el bot con deep link
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("▶️ Ver Ahora", url=f"https://t.me/{bot_username}?start=video_{storage_msg_id}")
            ]])
            
            print(f"\n🔗 Bot URL:")
            print(f"   https://t.me/{bot_username}?start=video_{storage_msg_id}")
            
            # Publicar en canal
            print(f"\n📤 Publicando en canal {VERIFICATION_CHANNEL_ID}...")
            msg = await bot.send_photo(
                chat_id=VERIFICATION_CHANNEL_ID,
                photo=photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            print(f"\n✅ ¡PUBLICADO EXITOSAMENTE!")
            print(f"   Message ID: {msg.message_id}")
            print(f"   Link: https://t.me/CineStellar_S/{msg.message_id}")
            
            return msg
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("="*60)
    print("TEST: Publicación forzada en canal de verificación")
    print("="*60)
    asyncio.run(test_publish())
