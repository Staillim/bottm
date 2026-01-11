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
    
    # Ignorar si es un comando (cualquier cosa que empiece con /)
    if message_text.startswith('/'):
        logger.debug(f"⏭️ Ignorando comando: {message_text}")
        return
    
    # Ignorar mensajes muy cortos o muy largos
    if len(message_text) < MIN_QUERY_LENGTH or len(message_text) > 100:
        logger.debug(f"⏭️ Mensaje ignorado por longitud: {len(message_text)} caracteres")
        return
    
    # Priorizar mensajes que empiecen con @ (búsqueda directa)
    starts_with_at = message_text.startswith('@')
    
    # Filtrar mensajes que son conversación casual (excepto si empiezan con @)
    if not starts_with_at and not is_potential_search_query(message_text):
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
    Prioriza mensajes con @ y nombres que parecen títulos
    """
    text_lower = text.lower()
    
    # Si empieza con @, es muy probable que sea una búsqueda
    if text.startswith('@'):
        return True
    
    # Ignorar mensajes muy conversacionales
    words = text_lower.split()
    
    # Si tiene más de 70% de palabras comunes, probablemente es conversación
    if len(words) > 0:
        common_count = sum(1 for word in words if word in IGNORE_WORDS)
        if common_count / len(words) > 0.7:
            return False
    
    # Si contiene solo palabras comunes, ignorar (excepto si es muy corto, podría ser título)
    if len(words) > 1 and all(word in IGNORE_WORDS for word in words):
        return False
    
    # Patrones que indican búsqueda de contenido (removido '^@' ya que se maneja arriba)
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
    
    # Si el mensaje tiene entre 1-6 palabras y formato de título
    if 1 <= len(words) <= 6:
        # Contar palabras capitalizadas usando el texto original, no text_lower
        original_words = text.split()
        capitalized_words = sum(1 for word in original_words if word and word[0].isupper())
        
        # Para 1 palabra: debe empezar con mayúscula, tener al menos 4 caracteres
        # y NO estar en palabras comunes
        if len(words) == 1:
            word = words[0]  # palabra en minúsculas para comparar
            if (capitalized_words >= 1 and len(word) >= 4 and 
                word not in IGNORE_WORDS and 
                not word.isdigit()):  # No es solo un número
                return True
        
        # Para múltiples palabras: al menos 2 deben estar capitalizadas
        elif len(words) > 1 and capitalized_words >= 2:
            return True
    
    return False

def clean_search_query(text: str) -> str:
    """
    Limpia el texto para usar como query de búsqueda
    """
    # Eliminar signos de interrogación, exclamación, etc
    text = re.sub(r'[¿?!¡]', '', text)
    
    # Eliminar @ al inicio (para búsquedas tipo @película)
    text = re.sub(r'^@\s*', '', text)
    
    # Eliminar palabras de relleno comunes al inicio
    prefixes_to_remove = [
        r'^alguien\s+tiene\s+',
        r'^tienen\s+',
        r'^hay\s+',
        r'^busco\s+',
        r'^donde\s+(?:esta|está|veo|encuentro)\s+',
        r'^como\s+se\s+llama\s+(?:la\s+)?(?:pelicula|película|serie)\s+(?:de\s+)?',
        r'^(?:la\s+)?pelicula\s+(?:de\s+)?',
        r'^(?:la\s+)?película\s+(?:de\s+)?',
        r'^(?:la\s+)?serie\s+(?:de\s+)?',
    ]
    
    for prefix in prefixes_to_remove:
        text = re.sub(prefix, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def normalize_text(text: str) -> str:
    """
    Normaliza texto para comparación, removiendo acentos y caracteres especiales
    """
    # Mapeo de caracteres con acentos a sin acentos
    accent_map = {
        'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ā': 'a', 'ă': 'a', 'ą': 'a',
        'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e', 'ē': 'e', 'ĕ': 'e', 'ę': 'e',
        'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ī': 'i', 'ĭ': 'i', 'į': 'i',
        'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ō': 'o', 'ŏ': 'o', 'ő': 'o',
        'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u', 'ŭ': 'u', 'ů': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    
    text = text.lower()
    for accented, unaccented in accent_map.items():
        text = text.replace(accented, unaccented)
    
    return text

def calculate_confidence(original_text: str, query: str, movies: list, series: list) -> float:
    """
    Calcula un score de confianza para determinar si responder
    """
    score = 0.0
    
    # Base score si hay resultados
    if movies or series:
        score += 0.2
    
    # Bonus alto si empieza con @ (búsqueda directa muy probable)
    if original_text.startswith('@'):
        score += 0.6
    
    # Bonus si el query es corto y específico (probablemente un título)
    words = query.split()
    if 1 <= len(words) <= 4:
        score += 0.1
        # Bonus extra si es una sola palabra y tiene buena longitud (probable título)
        if len(words) == 1 and len(query) >= 4:
            score += 0.1
    
    # Bonus si tiene patrones de búsqueda explícitos
    search_patterns = ['alguien tiene', 'busco', 'donde', 'hay']
    if any(pattern in original_text.lower() for pattern in search_patterns):
        score += 0.2
    
    # Bonus ALTO si el título coincide EXACTAMENTE o muy bien con algún resultado
    query_normalized = normalize_text(query)
    
    best_match_score = 0
    
    if movies:
        for movie in movies[:3]:
            title_normalized = normalize_text(movie.title)
            # Coincidencia exacta
            if query_normalized == title_normalized:
                best_match_score = max(best_match_score, 0.5)
            # Query está contenido en título
            elif query_normalized in title_normalized:
                # Calcular qué tan grande es la coincidencia
                match_ratio = len(query_normalized) / len(title_normalized)
                if match_ratio > 0.7:  # Query cubre más del 70% del título
                    best_match_score = max(best_match_score, 0.4)
                elif match_ratio > 0.5:  # Query cubre más del 50% del título
                    best_match_score = max(best_match_score, 0.3)
                else:
                    best_match_score = max(best_match_score, 0.1)
    
    if series:
        for show in series[:3]:
            name_normalized = normalize_text(show.name)
            # Coincidencia exacta
            if query_normalized == name_normalized:
                best_match_score = max(best_match_score, 0.5)
            # Query está contenido en nombre
            elif query_normalized in name_normalized:
                match_ratio = len(query_normalized) / len(name_normalized)
                if match_ratio > 0.7:
                    best_match_score = max(best_match_score, 0.4)
                elif match_ratio > 0.5:
                    best_match_score = max(best_match_score, 0.3)
                else:
                    best_match_score = max(best_match_score, 0.1)
    
    score += best_match_score
    
    # Penalizar si los resultados no son realmente relevantes
    if best_match_score < 0.2:  # Si no hay buena coincidencia
        score -= 0.2
    
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
    
    bot_username = context.bot.username
    
    # Agregar películas
    if movies:
        text += "📽️ *Películas:*\n"
        for idx, movie in enumerate(movies[:MAX_AUTO_RESULTS], 1):
            year = f"({movie.year})" if movie.year else ""
            rating = f" ⭐{movie.vote_average/10:.1f}" if movie.vote_average else ""
            
            safe_title = movie.title.replace("*", "").replace("_", "")
            text += f"  {idx}. {safe_title} {year}{rating}\n"
            
            # URL que abre el bot en privado con el ID de la película
            keyboard.append([
                InlineKeyboardButton(
                    f"📹 {safe_title[:40]}..." if len(safe_title) > 40 else f"📹 {safe_title}",
                    url=f"https://t.me/{bot_username}?start=movie_{movie.id}"
                )
            ])
    
    # Agregar series
    if series:
        text += "\n📺 *Series:*\n"
        for idx, show in enumerate(series[:MAX_AUTO_RESULTS], 1):
            year = f"({show.year})" if show.year else ""
            
            safe_title = show.name.replace("*", "").replace("_", "")
            text += f"  {idx}. {safe_title} {year}\n"
            
            # URL que abre el bot en privado con el ID de la serie
            keyboard.append([
                InlineKeyboardButton(
                    f"📺 {safe_title[:40]}..." if len(safe_title) > 40 else f"📺 {safe_title}",
                    url=f"https://t.me/{bot_username}?start=series_{show.id}"
                )
            ])
    
    # Agregar botón de búsqueda privada
    keyboard.append([
        InlineKeyboardButton(
            "🔍 Buscar más en privado",
            url=f"https://t.me/{bot_username}?start=search_{query}"
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

"""
# COMANDO DESHABILITADO - El bot solo responde automáticamente en grupos
# NO responde a comandos con /

async def group_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"
    Comando opcional para búsqueda manual en grupos: /search_group <query>
    DESHABILITADO - Solo funciona respuesta automática ahora
    \"\"\"
    logger.info(f"🔍 Comando /search_group ejecutado en chat {update.message.chat.id}")
    
    await update.message.reply_text(
        "🚫 Los comandos están deshabilitados en grupos.\n"
        "Simplemente escribe @nombrepelicula o el nombre de la película/serie.",
        parse_mode='Markdown'
    )
"""
