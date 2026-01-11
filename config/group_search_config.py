"""
Configuración para búsqueda inteligente en grupos
Personaliza estos valores según las necesidades de tu bot
"""

# ======================
# CONFIGURACIÓN BÁSICA
# ======================

# Longitud mínima del mensaje para considerarlo como búsqueda
MIN_QUERY_LENGTH = 3

# Longitud máxima del mensaje (mensajes más largos probablemente son conversación)
MAX_QUERY_LENGTH = 100

# Score mínimo de confianza para responder automáticamente (0.0 - 1.0)
# Valores recomendados:
#   0.5 - Muy permisivo (responde frecuentemente)
#   0.7 - Balance óptimo (recomendado)
#   0.8 - Más estricto (mejor precisión)
#   0.9 - Muy conservador (solo alta confianza)
MIN_CONFIDENCE_SCORE = 0.8

# Máximo de resultados a mostrar automáticamente
MAX_AUTO_RESULTS = 2

# ======================
# FILTROS AVANZADOS
# ======================

# Máximo de palabras en el mensaje para considerar como búsqueda potencial
MAX_WORDS_FOR_SEARCH = 15

# Porcentaje máximo de palabras comunes para considerar como búsqueda
# Si más del X% son palabras comunes, se considera conversación
MAX_COMMON_WORDS_RATIO = 0.7

# Mínimo de palabras capitalizadas para detectar formato de título
MIN_CAPITALIZED_WORDS = 2
MIN_CAPITALIZED_RATIO = 0.5

# ======================
# PALABRAS A IGNORAR
# ======================

# Palabras comunes que NO indican búsqueda de películas/series
IGNORE_WORDS = {
    # Saludos
    'hola', 'hi', 'hello', 'hey', 'buenos', 'días', 'buenas', 'tardes', 'noches',
    'adios', 'bye', 'chau', 'hasta', 'luego',
    
    # Cortesía
    'gracias', 'thanks', 'thank', 'you', 'porfavor', 'please', 'perdón', 'sorry',
    
    # Afirmaciones/Negaciones
    'si', 'no', 'yes', 'ok', 'okay', 'vale', 'bien', 'mal',
    
    # Risas
    'jaja', 'jeje', 'jiji', 'lol', 'xd', 'jajaja', 'hahaha', 'hehe',
    
    # Preguntas básicas
    'que', 'como', 'cuando', 'donde', 'quien', 'cual', 'porque', 'por', 'para',
    
    # Conectores comunes
    'con', 'sin', 'sobre', 'pero', 'mas', 'menos', 'muy', 'mucho', 'poco',
    'grande', 'pequeño', 'nuevo', 'viejo', 'este', 'ese', 'aquel',
    
    # Verbos comunes
    'ser', 'estar', 'hacer', 'decir', 'poder', 'deber', 'querer',
    
    # Otras
    'algo', 'nada', 'todo', 'alguno', 'ninguno', 'otro', 'mismo'
}

# ======================
# PATRONES DE BÚSQUEDA
# ======================

# Patrones regex que indican búsqueda de contenido
# Usa formato regex de Python
SEARCH_PATTERNS = [
    # Preguntas sobre disponibilidad
    r'alguien\s+(?:tiene|vio|conoce|sabe)',
    r'tienen\s+(?:la\s+)?(?:pelicula|serie|peli)',
    r'hay\s+(?:alguna?\s+)?(?:pelicula|serie|peli)',
    
    # Búsqueda explícita
    r'busco\s+',
    r'buscando\s+',
    r'estoy\s+buscando',
    
    # Ubicación de contenido
    r'donde\s+(?:esta|veo|encuentro|puedo\s+ver)',
    r'como\s+(?:se\s+llama|veo)',
    
    # Descriptores
    r'(?:la\s+)?pelicula\s+(?:de|del|sobre)',
    r'(?:la\s+)?serie\s+(?:de|del|sobre)',
    
    # Temporadas/Episodios
    r'temporada\s+\d+',
    r'season\s+\d+',
    r'capitulo\s+\d+',
    r'episodio\s+\d+',
    r'episode\s+\d+',
    r'\d+x\d+',  # Formato 2x05
    
    # Años (indica búsqueda específica)
    r'\b(19|20)\d{2}\b',
    
    # Recomendaciones
    r'recomiend(?:an|en|a)',
    r'suggestion',
]

# ======================
# PREFIJOS A REMOVER
# ======================

# Patrones que se eliminan del inicio del mensaje para limpiar la búsqueda
PREFIXES_TO_REMOVE = [
    r'^alguien\s+tiene\s+',
    r'^tienen\s+',
    r'^hay\s+',
    r'^busco\s+',
    r'^buscando\s+',
    r'^donde\s+(?:esta|veo|encuentro)\s+',
    r'^como\s+se\s+llama\s+(?:la\s+)?(?:pelicula|serie)\s+(?:de\s+)?',
    r'^(?:la\s+)?pelicula\s+(?:de\s+)?',
    r'^(?:la\s+)?serie\s+(?:de\s+)?',
    r'^(?:la\s+)?peli\s+(?:de\s+)?',
]

# ======================
# SCORES DE CONFIANZA
# ======================

# Configuración de cómo se calcula el score de confianza
CONFIDENCE_SCORES = {
    'has_results': 0.3,          # Bonus por tener resultados
    'short_query': 0.2,          # Bonus por query corto (1-4 palabras)
    'explicit_search': 0.3,      # Bonus por patrones explícitos de búsqueda
    'exact_match': 0.2,          # Bonus por coincidencia exacta
    'long_message_penalty': -0.3 # Penalización por mensaje largo
}

# Rango de palabras para considerar "query corto"
SHORT_QUERY_MIN_WORDS = 1
SHORT_QUERY_MAX_WORDS = 4

# ======================
# FORMATO DE RESPUESTA
# ======================

# Emojis para diferentes tipos de contenido
EMOJI_MOVIE = "📹"
EMOJI_SERIES = "📺"
EMOJI_SEARCH = "🔍"
EMOJI_RATING = "⭐"

# Texto del botón para búsqueda privada
PRIVATE_SEARCH_BUTTON_TEXT = "🔍 Buscar más en privado"

# Formato del mensaje de respuesta
RESPONSE_HEADER = "🎬 Encontré esto para: *{query}*\n\n"
MOVIES_SECTION_HEADER = "📽️ *Películas:*\n"
SERIES_SECTION_HEADER = "\n📺 *Series:*\n"

# ======================
# LOGGING Y DEBUG
# ======================

# Habilitar logging detallado
ENABLE_DEBUG_LOGGING = False

# Log de mensajes rechazados (útil para ajustar filtros)
LOG_REJECTED_MESSAGES = False

# ======================
# RATE LIMITING
# ======================

# Tiempo mínimo entre respuestas del bot en el mismo grupo (segundos)
# Evita spam si varios usuarios buscan al mismo tiempo
MIN_TIME_BETWEEN_RESPONSES = 3

# Máximo de respuestas por grupo por hora
MAX_RESPONSES_PER_HOUR = 50

# ======================
# PERSONALIZACIÓN POR IDIOMA
# ======================

# Idioma principal del bot
PRIMARY_LANGUAGE = 'es'  # 'es' para español, 'en' para inglés

# Mensajes por idioma
MESSAGES = {
    'es': {
        'no_results': '😔 No encontré resultados para: *{query}*',
        'command_usage': '🔍 Uso: `/search_group <nombre de película o serie>`',
        'group_only': 'Este comando solo funciona en grupos.',
    },
    'en': {
        'no_results': '😔 No results found for: *{query}*',
        'command_usage': '🔍 Usage: `/search_group <movie or series name>`',
        'group_only': 'This command only works in groups.',
    }
}
