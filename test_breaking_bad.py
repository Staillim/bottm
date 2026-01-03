"""
Test rápido para verificar detección de Breaking Bad en formato S##E##
"""
import re

# Patrones
pattern_short = re.compile(r'(\d+)[xX](\d+)')
pattern_spanish = re.compile(r'[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)', re.IGNORECASE)
pattern_se_format = re.compile(r'[Ss](\d+)[Ee](\d+)')

# Captions de Breaking Bad
captions = [
    "Breaking Bad - S01E01 - 1080p.mp4",
    "Breaking Bad - S01E02 - 1080p.mp4",
    "Breaking Bad - S01E03 - 1080p.mp4",
    "Breaking Bad - S02E02 - 1080p.mp4",
    "Breaking Bad - S02E08 - 1080p.mp4",
    "Breaking Bad - S03E08 - 1080p.mp4"
]

series_name = "Breaking Bad"

print("=" * 80)
print("TEST: DETECCIÓN DE BREAKING BAD EN FORMATO S##E##")
print("=" * 80)
print()

for i, caption in enumerate(captions, 1):
    print(f"Caption {i}: {caption}")
    
    # Verificar nombre de serie
    if series_name.lower() not in caption.lower():
        print(f"❌ ERROR: No contiene '{series_name}'")
        print()
        continue
    else:
        print(f"✅ Contiene '{series_name}'")
    
    # Intentar detectar con formato español
    match_spanish = pattern_spanish.search(caption)
    if match_spanish:
        season = int(match_spanish.group(1))
        episode = int(match_spanish.group(2))
        print(f"✅ DETECTADO con formato español: Temporada {season}, Episodio {episode}")
        print()
        continue
    
    # Intentar detectar con formato S##E##
    match_se = pattern_se_format.search(caption)
    if match_se:
        season = int(match_se.group(1))
        episode = int(match_se.group(2))
        print(f"✅ DETECTADO con formato S##E##: Temporada {season}, Episodio {episode}")
        print()
        continue
    
    # Intentar detectar con formato corto
    match_short = pattern_short.search(caption)
    if match_short:
        season = int(match_short.group(1))
        episode = int(match_short.group(2))
        print(f"✅ DETECTADO con formato corto: Temporada {season}, Episodio {episode}")
        print()
        continue
    
    print(f"❌ ERROR: No se detectó ningún formato")
    print()

print("=" * 80)
print("RESUMEN")
print("=" * 80)
print("Si todos los captions fueron detectados, el código está funcionando correctamente.")
print("Si no, hay un problema con los patrones.")
print("=" * 80)
