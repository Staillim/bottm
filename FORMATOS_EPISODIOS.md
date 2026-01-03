# Formatos de Episodios Soportados

Este documento describe los formatos de episodios que el sistema de indexación puede reconocer automáticamente.

## Formatos Soportados

### 1. Formato Corto (1x1, 2x14)
El formato más común usado en archivos y subtítulos.

**Ejemplos:**
- `Loki 1x1 - El inicio`
- `Dexter 2x14 Final de temporada`
- `Breaking Bad 5X10`
- `LUCIFER 1x13 FINAL`

**Patrón:** `(\d+)[xX](\d+)`

### 2. Formato Español (Temporada X - Capítulo Y)
Formato descriptivo en español.

**Ejemplos:**
- `Loki Temporada 2 - Capítulo 14 - El final`
- `Dexter Temporada 1 - Capítulo 20`
- `Breaking Bad Temporada 3 - Capítulo 5 - La decisión`

**Patrón:** `[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)`

**Variaciones soportadas:**
- Con diferentes tipos de guiones: `-`, `–`, `—`
- Con o sin acentos: `Capítulo` o `Capitulo`
- Mayúsculas/minúsculas: `temporada` o `TEMPORADA`

### 3. Formato con Emoji y Guión Largo
Formato decorativo con emojis y guión largo.

**Ejemplos:**
- `🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD`
- `🔻Lucifer — 02x05 — Audio Latino 🇲🇽 HD`
- `🔻Lucifer — 02x15 — Audio Latino 🇲🇽 HD`

**Patrón:** `(\d+)[xX](\d+)\s*[—–-]`

Este formato es detectado por el patrón corto, pero con soporte para guiones largos.

### 4. Formato S##E## (S01E01)
Formato estándar usado en archivos de video.

**Ejemplos:**
- `Breaking Bad - S01E01 - 1080p.mp4`
- `Breaking Bad - S03E02 - 1080p.mp4`
- `Game of Thrones - S08E06 - The Iron Throne.mp4`
- `The Office - s05e10 - The Duel.mkv`

**Patrón:** `[Ss](\d+)[Ee](\d+)`

**Variaciones soportadas:**
- Mayúsculas: `S01E01`
- Minúsculas: `s01e01`
- Combinaciones: `S01e01`, `s01E01`

## Prioridad de Detección

El sistema verifica los patrones en este orden:

1. **Formato Español** - Se verifica primero por ser el más específico
2. **Formato S##E##** - Segundo en prioridad
3. **Formato Corto** - Se verifica al final (incluye formato con emoji)

Esto evita conflictos cuando un mensaje contiene múltiples patrones.

## Extracción de Información

Para cada formato, el sistema extrae:

- **Número de Temporada**: El primer número del patrón
- **Número de Episodio**: El segundo número del patrón
- **Título del Episodio**: El texto que sigue al patrón (si existe)

### Ejemplos de Extracción:

| Caption | Temporada | Episodio | Título Extraído |
|---------|-----------|----------|-----------------|
| `Loki 1x1 - El inicio` | 1 | 1 | `El inicio` |
| `🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD` | 2 | 1 | `Audio Latino 🇲🇽 HD` |
| `Breaking Bad - S03E02 - 1080p.mp4` | 3 | 2 | `1080p.mp4` |
| `Temporada 2 - Capítulo 14 - El final` | 2 | 14 | `El final` |

## Detección de Cambio de Serie

El sistema incluye un mecanismo inteligente para detenerse cuando detecta que los episodios ya no pertenecen a la serie actual:

1. **Verificación del Nombre**: Cada caption debe contener el nombre de la serie (case insensitive)
2. **Contador de Vacíos**: Si 5 mensajes consecutivos no contienen episodios válidos, el escaneo se detiene
3. **Protección contra Series Mixtas**: Al verificar el nombre de la serie en cada caption, se evita indexar episodios de otras series

### Ejemplo de Detención:

```
Mensaje 100: "🔻Lucifer — 02x01 — Audio Latino"     ✅ Indexado
Mensaje 101: "🔻Lucifer — 02x02 — Audio Latino"     ✅ Indexado
Mensaje 102: "🔻Lucifer — 02x03 — Audio Latino"     ✅ Indexado
Mensaje 103: "Breaking Bad - S01E01 - 1080p.mp4"    ❌ No contiene "Lucifer", saltado (1/5)
Mensaje 104: "Breaking Bad - S01E02 - 1080p.mp4"    ❌ No contiene "Lucifer", saltado (2/5)
Mensaje 105: "Breaking Bad - S01E03 - 1080p.mp4"    ❌ No contiene "Lucifer", saltado (3/5)
Mensaje 106: "Breaking Bad - S01E04 - 1080p.mp4"    ❌ No contiene "Lucifer", saltado (4/5)
Mensaje 107: "Breaking Bad - S01E05 - 1080p.mp4"    ❌ No contiene "Lucifer", saltado (5/5)
🛑 Escaneo detenido después de 5 mensajes sin episodios válidos
```

## Comandos Relacionados

### Indexación Automática

```
/indexar_serie Lucifer (2021)
```

Busca automáticamente todos los episodios de la serie en el canal de almacenamiento.

### Indexación Manual

Si la indexación automática no encuentra episodios, puedes indexar manualmente respondiendo a los mensajes del canal con el formato del episodio:

```
1x1
2x14
Temporada 2 - Capítulo 5
S01E01
```

## Archivo de Prueba

Puedes probar los patrones ejecutando:

```bash
python test_episode_patterns.py
```

Este script incluye 22 casos de prueba que validan todos los formatos soportados.

## Notas Técnicas

- Los patrones usan expresiones regulares (regex) para flexibilidad
- El sistema es case-insensitive para el nombre de la serie
- Soporta diferentes tipos de guiones Unicode: `-`, `–`, `—`
- Los emojis en los captions no afectan la detección
- El sistema guarda el último mensaje procesado para continuar la indexación en sesiones futuras
