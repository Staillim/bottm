"""
Utilidades para limpiar títulos de películas y extraer información
"""
import re

def extract_year(text):
    """Extrae el año de un título (formato: título (2023) o título 2023)"""
    # Buscar año entre paréntesis: (2023) o (2020-2023)
    match = re.search(r'\((\d{4})\)', text)
    if match:
        return int(match.group(1))
    
    # Buscar año suelto: 2023
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    if match:
        return int(match.group(1))
    
    return None

def clean_title(text):
    """
    Limpia un título de película eliminando calidad, codec, idioma, etc.
    
    Ejemplo:
    "Avengers Endgame (2019) [1080p] [Latino] BluRay" → "Avengers Endgame"
    """
    if not text:
        return ""
    
    # Primero extraer el año si existe (lo guardaremos aparte)
    year = extract_year(text)
    
    # Lista de patrones a eliminar (case insensitive)
    patterns_to_remove = [
        r'\[.*?\]',  # Cualquier cosa entre corchetes: [1080p], [Latino]
        r'\(.*?p\)',  # Calidad entre paréntesis: (1080p), (720p)
        r'\b\d{3,4}p\b',  # Calidad: 1080p, 720p, 2160p
        r'\b4K\b',  # 4K
        r'\bUHD\b',  # UHD
        r'\bHD\b',  # HD
        r'\bFHD\b',  # Full HD
        r'\bBluRay\b',  # BluRay
        r'\bBRRip\b',  # BRRip
        r'\bWEBRip\b',  # WEBRip
        r'\bWEB-DL\b',  # WEB-DL
        r'\bHDRip\b',  # HDRip
        r'\bDVDRip\b',  # DVDRip
        r'\bx264\b',  # Codec
        r'\bx265\b',  # Codec
        r'\bHEVC\b',  # Codec
        r'\bh264\b',  # Codec
        r'\bh265\b',  # Codec
        r'\b10bit\b',  # Bit depth
        r'\bAAC\b',  # Audio codec
        r'\bAC3\b',  # Audio codec
        r'\bDTS\b',  # Audio codec
        r'\bLatino\b',  # Idioma
        r'\bEspañol\b',  # Idioma
        r'\bSpanish\b',  # Idioma
        r'\bEnglish\b',  # Idioma
        r'\bSubtitulado\b',  # Subtítulos
        r'\bSubs\b',  # Subtítulos
        r'\bDual\b',  # Dual audio
        r'\bExtended\b',  # Versión extendida
        r'\bUnrated\b',  # Versión sin censura
        r'\bDirector\'?s? Cut\b',  # Director's Cut
        r'\bREMAST(ER|ERED)\b',  # Remasterizado
        r'\bIMAX\b',  # IMAX
        r'\b-\s*\w+$',  # Grupo al final: - YIFY, - RARBG
        r'\s+-\s+',  # Guiones con espacios
    ]
    
    cleaned = text
    
    # Remover año entre paréntesis para limpieza (lo agregaremos después si es necesario)
    cleaned = re.sub(r'\(\d{4}\)', '', cleaned)
    
    # Aplicar todos los patrones
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Limpiar caracteres especiales y múltiples espacios
    cleaned = re.sub(r'[_\.]', ' ', cleaned)  # Reemplazar _ y . por espacios
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Múltiples espacios → uno solo
    cleaned = cleaned.strip()
    
    # Remover caracteres especiales al inicio/fin
    cleaned = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', cleaned)
    
    return cleaned, year

def suggest_search_terms(title):
    """
    Genera múltiples variaciones de búsqueda para mejorar resultados
    
    Returns: lista de términos de búsqueda en orden de prioridad
    """
    cleaned, year = clean_title(title)
    
    suggestions = []
    
    # 1. Título limpio con año (más específico)
    if year:
        suggestions.append(f"{cleaned} {year}")
    
    # 2. Título limpio sin año
    suggestions.append(cleaned)
    
    # 3. Si tiene subtítulo (después de :), probar sin él
    if ':' in cleaned:
        main_title = cleaned.split(':')[0].strip()
        if year:
            suggestions.append(f"{main_title} {year}")
        suggestions.append(main_title)
    
    # 4. Si es muy largo (> 50 chars), probar versión corta
    if len(cleaned) > 50:
        short = cleaned[:50].rsplit(' ', 1)[0]  # Cortar en última palabra
        suggestions.append(short)
    
    return suggestions

def format_title_with_year(title, year=None):
    """Formatea un título con año al estilo TMDB: Title (Year)"""
    if year:
        return f"{title} ({year})"
    return title

# Funciones auxiliares para debugging
def analyze_title(text):
    """Analiza un título y muestra qué se detectó"""
    cleaned, year = clean_title(text)
    suggestions = suggest_search_terms(text)
    
    return {
        "original": text,
        "cleaned": cleaned,
        "year": year,
        "formatted": format_title_with_year(cleaned, year),
        "search_suggestions": suggestions
    }
