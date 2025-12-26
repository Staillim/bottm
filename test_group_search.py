"""
Script de prueba para el sistema de búsqueda inteligente en grupos
Prueba la detección de mensajes y cálculo de confidence score
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from handlers.group_search import (
    is_potential_search_query,
    clean_search_query,
    calculate_confidence,
    IGNORE_WORDS
)

# Clase mock para simular resultados de DB
class MockMovie:
    def __init__(self, title, year=None, vote_average=None):
        self.title = title
        self.year = year
        self.vote_average = vote_average

# Casos de prueba
TEST_CASES = [
    # (mensaje, debe_detectar, descripción)
    ("Alguien tiene Spider-Man?", True, "Pregunta directa"),
    ("Busco Avengers Endgame", True, "Búsqueda explícita"),
    ("Hay The Last of Us?", True, "Pregunta con 'hay'"),
    ("Donde veo Breaking Bad", True, "Pregunta con 'donde'"),
    ("Spider-Man No Way Home", True, "Título directo"),
    ("Avatar 2022", True, "Título con año"),
    ("temporada 2 de The Walking Dead", True, "Mención de temporada"),
    ("La película de Thor", True, "Mención de película"),
    
    # Casos que NO deben detectarse
    ("Hola como están todos?", False, "Saludo casual"),
    ("Jajaja que chistoso", False, "Risa/conversación"),
    ("Si, gracias por todo", False, "Agradecimiento"),
    ("Ok, nos vemos luego", False, "Despedida"),
    ("x", False, "Mensaje muy corto"),
    ("/start", False, "Comando"),
    ("Hoy es un día muy lindo para salir a pasear con los amigos", False, "Conversación larga"),
]

def test_detection():
    """Prueba la detección de búsquedas potenciales"""
    print("=" * 70)
    print("PRUEBA DE DETECCIÓN DE BÚSQUEDAS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for message, should_detect, description in TEST_CASES:
        result = is_potential_search_query(message)
        status = "✅ PASS" if result == should_detect else "❌ FAIL"
        
        if result == should_detect:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} - {description}")
        print(f"   Mensaje: '{message}'")
        print(f"   Esperado: {should_detect}, Obtenido: {result}")
    
    print("\n" + "=" * 70)
    print(f"Resultados: {passed} pasadas, {failed} fallidas")
    print("=" * 70)
    return failed == 0

def test_query_cleaning():
    """Prueba la limpieza de queries"""
    print("\n" + "=" * 70)
    print("PRUEBA DE LIMPIEZA DE QUERIES")
    print("=" * 70)
    
    test_cases = [
        ("Alguien tiene Spider-Man?", "Spider-Man"),
        ("Busco Avengers Endgame", "Avengers Endgame"),
        ("Hay The Last of Us?", "The Last of Us"),
        ("Donde veo Breaking Bad", "Breaking Bad"),
        ("La película de Thor", "Thor"),
        ("¿Como se llama la pelicula de Batman?", "Batman"),
    ]
    
    for original, expected in test_cases:
        cleaned = clean_search_query(original)
        status = "✅" if expected.lower() in cleaned.lower() else "⚠️"
        print(f"\n{status} '{original}'")
        print(f"   → '{cleaned}'")
        print(f"   Esperado contiene: '{expected}'")

def test_confidence_scoring():
    """Prueba el cálculo de confidence score"""
    print("\n" + "=" * 70)
    print("PRUEBA DE CONFIDENCE SCORING")
    print("=" * 70)
    
    test_cases = [
        # (mensaje, query_limpio, tiene_resultados, descripción)
        ("Alguien tiene Spider-Man?", "Spider-Man", True, "Búsqueda explícita con resultados"),
        ("Spider-Man", "Spider-Man", True, "Título corto con resultados"),
        ("Hola como están", "Hola como están", False, "Conversación sin resultados"),
        ("Busco una película de acción que sea muy emocionante y tenga buenos efectos especiales", 
         "película acción emocionante efectos especiales", False, "Búsqueda muy larga"),
    ]
    
    for message, query, has_results, description in test_cases:
        movies = [MockMovie("Spider-Man: No Way Home", "2021", 8.3)] if has_results else []
        series = []
        
        score = calculate_confidence(message, query, movies, series)
        should_respond = "Sí" if score >= 0.7 else "No"
        
        print(f"\n{description}")
        print(f"   Mensaje: '{message}'")
        print(f"   Query: '{query}'")
        print(f"   Score: {score:.2f}")
        print(f"   Responder: {should_respond}")

def test_ignore_words():
    """Muestra las palabras que se ignoran"""
    print("\n" + "=" * 70)
    print("PALABRAS IGNORADAS")
    print("=" * 70)
    print(f"Total de palabras: {len(IGNORE_WORDS)}")
    print(f"Palabras: {', '.join(sorted(IGNORE_WORDS)[:20])}...")

def main():
    """Ejecuta todas las pruebas"""
    print("\n🧪 TESTING: Sistema de Búsqueda Inteligente en Grupos\n")
    
    test_detection()
    test_query_cleaning()
    test_confidence_scoring()
    test_ignore_words()
    
    print("\n" + "=" * 70)
    print("✅ Pruebas completadas")
    print("=" * 70)
    print("\n💡 Recomendaciones:")
    print("   - Ajusta MIN_CONFIDENCE_SCORE si hay muchos falsos positivos/negativos")
    print("   - Agrega palabras a IGNORE_WORDS según el idioma de tu comunidad")
    print("   - Modifica SEARCH_PATTERNS para detectar patrones específicos")
    print("\n")

if __name__ == "__main__":
    main()
