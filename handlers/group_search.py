"""
Handler para búsqueda inteligente en grupos de Telegram
Detecta automáticamente cuando alguien menciona nombres de películas/series
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re
from datetime import datetime
import logging

# Importar configuración (con fallback a valores por defecto)
try:
    from config.group_search_config import *
except ImportError:
    # Valores por defecto si no existe el archivo de configuración
    MIN_QUERY_LENGTH = 3
    MIN_CONFIDENCE_SCORE = 0.7
    MAX_AUTO_RESULTS = 3
    IGNORE_WORDS = {
        'hola', 'hi', 'hello', 'gracias', 'thanks', 'ok', 'okay', 'si', 'no', 
        'yes', 'jaja', 'jeje', 'lol', 'xd', 'jajaja', 'hahaha', 'que', 'como',
        'cuando', 'donde', 'quien', 'cual', 'porque', 'por', 'para', 'con',
        'sin', 'sobre', 'pero', 'mas', 'menos', 'muy', 'mucho', 'poco',
        'bien', 'mal', 'bueno', 'malo', 'grande', 'pequeño', 'nuevo', 'viejo'
    }

logger = logging.getLogger(__name__)

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes en grupos para detectar búsquedas de películas/series
    """
    # Verificar que es un mensaje de grupo
    if update.message.chat.type not in ['group', 'supergroup']:
        return
    
    # Verificar que tiene texto
    if not update.message.text:
        return
    
    message_text = update.message.text.strip()
    
    logger.info(f"📨 Mensaje de grupo recibido: '{message_text[:50]}...' de {update.effective_user.id}")
    
    # Ignorar si es un comando
    if message_text.startswith('/'):
        logger.debug(f"⏭️ Ignorando comando: {message_text}")
        return
    
    # Ignorar mensajes muy cortos o muy largos
    if len(message_text) < MIN_QUERY_LENGTH or len(message_text) > 100:
        logger.debug(f"⏭️ Mensaje ignorado por longitud: {len(message_text)} caracteres")
        return
    
    # Filtrar mensajes que son conversación casual
    if not is_potential_search_query(message_text):
        logger.debug(f"⏭️ No parece búsqueda: '{message_text[:30]}...'")
        return
    
    logger.info(f"✅ Detectado como búsqueda potencial: '{message_text[:50]}...'")
    
    # Buscar en la base de datos
    db = context.bot_data['db']
    
    # Limpiar query para búsqueda
    clean_query = clean_search_query(message_text)
    
    logger.info(f"🔍 Query limpio: '{clean_query}'")
    
    if not clean_query:
        logger.debug("⏭️ Query vacío después de limpiar")
        return
    
    # Buscar películas
    movies = await db.search_videos(clean_query, limit=5)
    
    # Buscar series
    series = await db.search_tv_shows(clean_query, limit=5)
    
    # Combinar resultados
    total_results = (len(movies) if movies else 0) + (len(series) if series else 0)
    
    logger.info(f"📊 Resultados encontrados: {len(movies) if movies else 0} películas, {len(series) if series else 0} series")
    
    if total_results == 0:
        logger.info("⏭️ No hay resultados, no se responde")
        return  # No responder si no hay resultados
    
    # Calcular score de confianza
    confidence = calculate_confidence(message_text, clean_query, movies, series)
    
    logger.info(f"📈 Confidence score: {confidence:.2f} (min requerido: {MIN_CONFIDENCE_SCORE})")
    
    # Solo responder si el score es alto
    if confidence < MIN_CONFIDENCE_SCORE:
        logger.info(f"⏭️ Score insuficiente ({confidence:.2f} < {MIN_CONFIDENCE_SCORE}), no se responde")
        return
    
    logger.info(f"✅ Enviando respuesta al grupo con {total_results} resultados")
    
    # Preparar respuesta
    await send_group_results(update, context, movies, series, clean_query)

def is_potential_search_query(text: str) -> bool:
    """
    Determina si el texto parece ser una búsqueda de película/serie
    """
    text_lower = text.lower()
    
    # Ignorar mensajes muy conversacionales
    words = text_lower.split()
    
    # Si tiene más de 70% de palabras comunes, probablemente es conversación
    if len(words) > 0:
        common_count = sum(1 for word in words if word in IGNORE_WORDS)
        if common_count / len(words) > 0.7:
            return False
    
    # Si contiene solo palabras comunes, ignorar
    if len(words) > 0 and all(word in IGNORE_WORDS for word in words):
        return False
    
    # Patrones que indican búsqueda de contenido
    search_indicators = [
        r'alguien\s+(?:tiene|vio|conoce)',  # "alguien tiene/vio..."
        r'busco\s+',  # "busco..."
        r'tienen\s+',  # "tienen..."
        r'hay\s+',  # "hay..."
        r'donde\s+(?:esta|veo|encuentro)',  # "donde esta/veo..."
        r'como\s+se\s+llama',  # "como se llama..."
        r'pelicula\s+de',  # "pelicula de..."
        r'serie\s+de',  # "serie de..."
        r'\b(?:19|20)\d{2}\b',  # Año (indica búsqueda)
        r'temporada\s+\d+',  # "temporada X"
        r'capitulo\s+\d+',  # "capitulo X"
    ]
    
    for pattern in search_indicators:
        if re.search(pattern, text_lower):
            return True
    
    # Si el mensaje tiene entre 2-6 palabras y empieza con mayúscula, 
    # podría ser un título
    if 2 <= len(words) <= 6 and text[0].isupper():
        return True
    
    # Si tiene formato de título (palabras capitalizadas)
    capitalized_words = sum(1 for word in words if word and word[0].isupper())
    if capitalized_words >= 2 and capitalized_words / len(words) > 0.5:
        return True
    
    return False

def clean_search_query(text: str) -> str:
    """
    Limpia el texto para usar como query de búsqueda
    """
    # Eliminar signos de interrogación, exclamación, etc
    text = re.sub(r'[¿?!¡]', '', text)
    
    # Eliminar palabras de relleno comunes al inicio
    prefixes_to_remove = [
        r'^alguien\s+tiene\s+',
        r'^tienen\s+',
        r'^hay\s+',
        r'^busco\s+',
        r'^donde\s+(?:esta|veo|encuentro)\s+',
        r'^como\s+se\s+llama\s+(?:la\s+)?(?:pelicula|serie)\s+(?:de\s+)?',
        r'^(?:la\s+)?pelicula\s+(?:de\s+)?',
        r'^(?:la\s+)?serie\s+(?:de\s+)?',
    ]
    
    for prefix in prefixes_to_remove:
        text = re.sub(prefix, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def calculate_confidence(original_text: str, query: str, movies: list, series: list) -> float:
    """
    Calcula un score de confianza para determinar si responder
    """
    score = 0.0
    
    # Base score si hay resultados
    if movies or series:
        score += 0.3
    
    # Bonus si el query es corto y específico (probablemente un título)
    words = query.split()
    if 1 <= len(words) <= 4:
        score += 0.2
    
    # Bonus si tiene patrones de búsqueda explícitos
    search_patterns = ['alguien tiene', 'busco', 'donde', 'hay']
    if any(pattern in original_text.lower() for pattern in search_patterns):
        score += 0.3
    
    # Bonus si el título coincide exactamente con algún resultado
    query_lower = query.lower()
    
    if movies:
        for movie in movies[:3]:
            if query_lower in movie.title.lower():
                score += 0.2
                break
    
    if series:
        for show in series[:3]:
            if query_lower in show.name.lower():
                score += 0.2
                break
    
    # Penalizar mensajes muy largos (probablemente conversación)
    if len(original_text.split()) > 15:
        score -= 0.3
    
    return min(score, 1.0)  # Cap at 1.0

async def send_group_results(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             movies: list, series: list, query: str):
    """
    Envía los resultados en el grupo
    """
    keyboard = []
    text = f"🎬 Encontré esto para: *{query}*\n\n"
    
    # Agregar películas
    if movies:
        text += "📽️ *Películas:*\n"
        for idx, movie in enumerate(movies[:MAX_AUTO_RESULTS], 1):
            year = f"({movie.year})" if movie.year else ""
            rating = f" ⭐{movie.vote_average/10:.1f}" if movie.vote_average else ""
            
            safe_title = movie.title.replace("*", "").replace("_", "")
            text += f"  {idx}. {safe_title} {year}{rating}\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📹 {safe_title[:40]}..." if len(safe_title) > 40 else f"📹 {safe_title}",
                    callback_data=f"video_{movie.id}"
                )
            ])
    
    # Agregar series
    if series:
        text += "\n📺 *Series:*\n"
        for idx, show in enumerate(series[:MAX_AUTO_RESULTS], 1):
            year = f"({show.year})" if show.year else ""
            
            safe_title = show.name.replace("*", "").replace("_", "")
            text += f"  {idx}. {safe_title} {year}\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📺 {safe_title[:40]}..." if len(safe_title) > 40 else f"📺 {safe_title}",
                    callback_data=f"series_{show.id}"
                )
            ])
    
    # Agregar botón de búsqueda privada
    keyboard.append([
        InlineKeyboardButton(
            "🔍 Buscar más en privado",
            url=f"https://t.me/{context.bot.username}?start=search_{query}"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Responder al mensaje original
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Registrar la búsqueda en grupo
    db = context.bot_data['db']
    try:
        await db.log_search(
            update.effective_user.id, 
            query, 
            len(movies) + len(series),
            metadata={'source': 'group', 'chat_id': update.message.chat.id}
        )
    except Exception as e:
        logger.error(f"Error logging group search: {e}")

async def group_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando opcional para búsqueda manual en grupos: /search_group <query>
    """
    logger.info(f"🔍 Comando /search_group ejecutado en chat {update.message.chat.id}")
    
    if update.message.chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "Este comando solo funciona en grupos."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍 Uso: `/search_group <nombre de película o serie>`",
            parse_mode='Markdown'
        )
        return
    
    query = " ".join(context.args)
    logger.info(f"🔍 Búsqueda manual en grupo: '{query}'")
    db = context.bot_data['db']
    
    # Buscar
    movies = await db.search_videos(query, limit=5)
    series = await db.search_tv_shows(query, limit=5)
    
    if not movies and not series:
        await update.message.reply_text(
            f"😔 No encontré resultados para: *{query}*",
            parse_mode='Markdown'
        )
        return
    
    await send_group_results(update, context, movies, series, query)
