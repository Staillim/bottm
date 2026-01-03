"""
Script de prueba para validar los patrones de detección de episodios
"""
import re

# Patrones para detectar episodios
pattern_short = re.compile(r'(\d+)[xX](\d+)')
pattern_spanish = re.compile(r'[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)', re.IGNORECASE)
pattern_se_format = re.compile(r'[Ss](\d+)[Ee](\d+)')

# Casos de prueba
test_cases = [
    # Formato corto
    "Loki 1x1 - El inicio",
    "Dexter 2x14 Final de temporada",
    "Breaking Bad 5X10",
    "LUCIFER 1x13 FINAL",
    
    # Formato español
    "Loki Temporada 2 - Capítulo 14 - El final",
    "Dexter Temporada 1 - Capítulo 20",
    "Breaking Bad Temporada 3 - Capítulo 5 - La decisión",
    
    # Formato con emoji y guión largo
    "🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD",
    "🔻Lucifer — 02x05 — Audio Latino 🇲🇽 HD",
    "🔻Lucifer — 02x15 — Audio Latino 🇲🇽 HD",
    
    # Formato S##E##
    "Breaking Bad - S01E01 - 1080p.mp4",
    "Breaking Bad - S03E02 - 1080p.mp4",
    "Game of Thrones - S08E06 - The Iron Throne.mp4",
    "The Office - s05e10 - The Duel.mkv",
    
    # Variaciones en mayúsculas/minúsculas
    "Game of Thrones temporada 8 - capítulo 6",
    "The Wire TEMPORADA 4 - CAPÍTULO 13",
    
    # Con diferentes guiones
    "The Office Temporada 5 – Capítulo 10",
    "Friends Temporada 10 — Capítulo 18",
    
    # Con acentos
    "Narcos Temporada 2 - Capítulo 8",
    "La Casa de Papel Temporada 3 - Capitulo 7",
    
    # Casos que NO deben coincidir
    "Película sin episodio",
    "Serie sin formato",
]

print("=" * 60)
print("PRUEBAS DE PATRONES DE DETECCIÓN DE EPISODIOS")
print("=" * 60)

for i, caption in enumerate(test_cases, 1):
    print(f"\n📝 Caso {i}: {caption}")
    print("-" * 60)
    
    # Intentar con formato español primero
    match_spanish = pattern_spanish.search(caption)
    if match_spanish:
        season = int(match_spanish.group(1))
        episode = int(match_spanish.group(2))
        print(f"✅ DETECTADO (Formato Español)")
        print(f"   Temporada: {season}")
        print(f"   Episodio: {episode}")
        
        # Extraer título
        title_match = re.search(r'[Cc]ap[ií]tulo\s*\d+\s*[-–—]?\s*(.+)', caption)
        if title_match:
            title = title_match.group(1).strip()
            print(f"   Título: {title}")
        continue
    
    # Intentar con formato S##E##
    match_se = pattern_se_format.search(caption)
    if match_se:
        season = int(match_se.group(1))
        episode = int(match_se.group(2))
        print(f"✅ DETECTADO (Formato S##E##)")
        print(f"   Temporada: {season}")
        print(f"   Episodio: {episode}")
        
        # Extraer título
        title_match = re.search(r'[Ss]\d+[Ee]\d+\s*[-–—]?\s*(.+)', caption)
        if title_match:
            title = title_match.group(1).strip()
            print(f"   Título: {title}")
        continue
    
    # Intentar con formato corto
    match_short = pattern_short.search(caption)
    if match_short:
        season = int(match_short.group(1))
        episode = int(match_short.group(2))
        print(f"✅ DETECTADO (Formato Corto)")
        print(f"   Temporada: {season}")
        print(f"   Episodio: {episode}")
        
        # Extraer título
        title_match = re.search(r'\d+[xX]\d+\s*[-–—]?\s*(.+)', caption)
        if title_match:
            title = title_match.group(1).strip()
            print(f"   Título: {title}")
        continue
    
    # No se detectó
    print("❌ NO DETECTADO (Formato no válido)")

print("\n" + "=" * 60)
print("PRUEBAS COMPLETADAS")
print("=" * 60)
