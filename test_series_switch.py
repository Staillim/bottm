"""
Test para verificar que el sistema se detiene cuando detecta otra serie
"""
import re

def check_series_name_in_caption(caption: str, series_name: str) -> bool:
    """
    Verifica si el nombre de la serie está en el caption
    """
    return series_name.lower() in caption.lower()

# Patrones
pattern_short = re.compile(r'(\d+)[xX](\d+)')
pattern_spanish = re.compile(r'[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)', re.IGNORECASE)
pattern_se_format = re.compile(r'[Ss](\d+)[Ee](\d+)')

def detect_episode(caption: str, series_name: str):
    """
    Detecta un episodio en el caption si pertenece a la serie especificada
    """
    # Verificar si el caption contiene el nombre de la serie
    if not check_series_name_in_caption(caption, series_name):
        return None, None, None, "No contiene el nombre de la serie"
    
    # Intentar detectar episodio
    # 1. Formato español
    match_spanish = pattern_spanish.search(caption)
    if match_spanish:
        season = int(match_spanish.group(1))
        episode = int(match_spanish.group(2))
        return season, episode, "Español", None
    
    # 2. Formato S##E##
    match_se = pattern_se_format.search(caption)
    if match_se:
        season = int(match_se.group(1))
        episode = int(match_se.group(2))
        return season, episode, "S##E##", None
    
    # 3. Formato corto
    match_short = pattern_short.search(caption)
    if match_short:
        season = int(match_short.group(1))
        episode = int(match_short.group(2))
        return season, episode, "Corto", None
    
    return None, None, None, "No se detectó formato de episodio"

# Simular mensajes del canal
test_messages = [
    ("🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD", 100),
    ("🔻Lucifer — 02x05 — Audio Latino 🇲🇽 HD", 101),
    ("🔻Lucifer — 02x15 — Audio Latino 🇲🇽 HD", 102),
    ("Breaking Bad - S01E01 - 1080p.mp4", 103),  # Cambia de serie
    ("Breaking Bad - S01E02 - 1080p.mp4", 104),
    ("Breaking Bad - S01E03 - 1080p.mp4", 105),
    ("Breaking Bad - S01E04 - 1080p.mp4", 106),
    ("Breaking Bad - S01E05 - 1080p.mp4", 107),
]

print("=" * 80)
print("TEST: DETECCIÓN Y DETENCIÓN AL CAMBIAR DE SERIE")
print("=" * 80)
print(f"\nSerie objetivo: Lucifer")
print(f"Máximo de mensajes vacíos consecutivos: 5")
print("")

series_name = "Lucifer"
MAX_EMPTY = 5
empty_count = 0
indexed_count = 0
current_message_id = 100

print("Procesando mensajes:")
print("-" * 80)

for caption, msg_id in test_messages:
    season, episode, format_type, error = detect_episode(caption, series_name)
    
    if season is not None:
        # Episodio detectado
        indexed_count += 1
        empty_count = 0  # Resetear contador
        print(f"✅ Mensaje {msg_id}: INDEXADO")
        print(f"   Caption: {caption}")
        print(f"   Temporada {season}, Episodio {episode} (Formato: {format_type})")
        print(f"   Contador vacíos: {empty_count}")
        print("")
    else:
        # No se pudo indexar
        empty_count += 1
        print(f"❌ Mensaje {msg_id}: SALTADO ({empty_count}/{MAX_EMPTY})")
        print(f"   Caption: {caption}")
        print(f"   Razón: {error}")
        print("")
        
        if empty_count >= MAX_EMPTY:
            print("=" * 80)
            print("🛑 ESCANEO DETENIDO")
            print("=" * 80)
            print(f"Razón: Se alcanzó el límite de {MAX_EMPTY} mensajes vacíos consecutivos")
            print(f"Total episodios indexados: {indexed_count}")
            print(f"Último mensaje procesado: {msg_id}")
            print("")
            break

# Verificar que se detuvo correctamente
print("=" * 80)
print("RESULTADO DEL TEST")
print("=" * 80)

if empty_count >= MAX_EMPTY:
    print("✅ ÉXITO: El sistema se detuvo correctamente al detectar otra serie")
    print(f"   - Episodios de Lucifer indexados: {indexed_count}")
    print(f"   - Mensajes de Breaking Bad saltados: {empty_count}")
    print(f"   - El sistema NO indexó episodios de Breaking Bad")
else:
    print("❌ ERROR: El sistema no se detuvo como se esperaba")

print("=" * 80)
