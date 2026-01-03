# Actualización del Sistema de Indexación de Series

## 🎯 Cambios Realizados

Se ha mejorado el sistema de indexación de series para reconocer **4 formatos** de numeración de episodios.

## 📝 Formatos Soportados

### 1. Formato Corto (existente)
- **Ejemplos:** `1x1`, `2x14`, `5X10`, `LUCIFER 1x13 FINAL`
- **Patrón:** `(\d+)[xX](\d+)`
- Compatible con mayúsculas y minúsculas en la 'x'

### 2. Formato Español (existente)
- **Ejemplos:** 
  - `Temporada 2 - Capítulo 14`
  - `Temporada 1 - Capítulo 20`
  - `temporada 3 - capítulo 5`
- **Patrón:** `[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)`
- Características:
  - Case insensitive (mayúsculas/minúsculas)
  - Acepta diferentes tipos de guiones: `-`, `–`, `—`
  - Funciona con "Capítulo" o "Capitulo" (con o sin acento)

### 3. Formato con Emoji y Guión Largo (NUEVO) ✨
- **Ejemplos:**
  - `🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD`
  - `🔻Lucifer — 02x05 — Audio Latino 🇲🇽 HD`
  - `🔻Lucifer — 02x15 — Audio Latino 🇲🇽 HD`
- **Patrón:** `(\d+)[xX](\d+)` (detectado por el formato corto)
- Características:
  - Soporta emojis al inicio y en medio del texto
  - Reconoce guiones largos (`—`)
  - Extrae información adicional (idioma, calidad)

### 4. Formato S##E## (NUEVO) ✨
- **Ejemplos:**
  - `Breaking Bad - S01E01 - 1080p.mp4`
  - `Breaking Bad - S03E02 - 1080p.mp4`
  - `Game of Thrones - S08E06 - The Iron Throne.mp4`
  - `The Office - s05e10 - The Duel.mkv`
- **Patrón:** `[Ss](\d+)[Ee](\d+)`
- Características:
  - Formato estándar usado en archivos de video
  - Soporta mayúsculas y minúsculas: `S01E01`, `s01e01`
  - Reconoce ceros iniciales en temporada y episodio

## 🔧 Funciones Actualizadas

### 1. `scan_channel_for_episodes()`
**Ubicación:** `handlers/series_admin.py`

**Mejoras:**
- Detecta automáticamente todos los 4 formatos al escanear el canal
- Incluye protección contra cambio de serie
- Extrae correctamente el título del episodio en todos los casos

**Orden de detección:**
1. Primero busca formato español (más específico)
2. Luego busca formato S##E##
3. Finalmente busca formato corto (incluye emoji-dash)
4. Si no encuentra ninguno, continúa con el siguiente mensaje

**Protección contra Series Mixtas:**
- Verifica que cada caption contenga el nombre de la serie
- Cuenta mensajes consecutivos sin episodios válidos (máximo 5)
- Se detiene automáticamente al detectar otra serie

### 2. `index_episode_reply()`
**Ubicación:** `handlers/series_admin.py`

**Mejoras:**
- Acepta todos los 4 formatos al indexar manualmente
- Parsea correctamente los números de temporada y episodio
- Mantiene compatibilidad con el formato existente

### 3. Mensajes de ayuda actualizados

**Comando `/indexar_serie`:**
```
⚠️ No se encontraron episodios automáticamente en el canal.

Puedes indexar manualmente respondiendo mensajes con cualquiera de estos formatos:

Formato corto:
1x1 (Temporada 1, Episodio 1)
2x5 (Temporada 2, Episodio 5)

Formato español:
Temporada 1 - Capítulo 20
Temporada 2 - Capítulo 14

Formato con emoji:
🔻Lucifer — 02x01 — Audio Latino

Formato S##E##:
Breaking Bad - S01E01 - 1080p.mp4
## ✅ Ejemplos de Uso

### Captions Válidos

#### Formato Corto:
```
Loki 1x1 - El inicio
Dexter 2x14 Final de temporada
Breaking Bad 5X10
LUCIFER 1x13 FINAL
```

#### Formato con Emoji y Guión Largo:
```
🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD
🔻Lucifer — 02x05 — Audio Latino 🇲🇽 HD
🔻Lucifer — 02x15 — Audio Latino 🇲🇽 HD
```

#### Formato S##E##:
```
Breaking Bad - S01E01 - 1080p.mp4
Breaking Bad - S03E02 - 1080p.mp4
Game of Thrones - S08E06 - The Iron Throne.mp4
The Office - s05e10 - The Duel.mkv
```

#### Formato Español:
```
Loki Temporada 2 - Capítulo 14 - El final
Dexter Temporada 1 - Capítulo 20
Breaking Bad Temporada 3 - Capítulo 5 - La decisión
Game of Thrones temporada 8 - capítulo 6
```

### Variaciones Aceptadas

- **Mayúsculas/minúsculas:** ✅ `TEMPORADA 4 - CAPÍTULO 13`, `S01E01`, `s01e01`
- **Diferentes guiones:** ✅ `Temporada 5 – Capítulo 10`, `Lucifer — 02x01`
- **Sin acento:** ✅ `Temporada 3 - Capitulo 7`
- **Espacios variables:** ✅ `Temporada  2  -  Capítulo  8`
- **Con emojis:** ✅ `🔻Lucifer — 02x01 — Audio Latino 🇲🇽 HD`

## 🧪 Testing

### Test de Patrones

Se ha actualizado el archivo `test_episode_patterns.py` para validar todos los patrones:

```bash
python test_episode_patterns.py
```

Este script prueba **22 casos de prueba**:
- ✅ Formato corto con 'x' minúscula y 'X' mayúscula
- ✅ Formato español estándar
- ✅ Formato con emoji y guión largo (NUEVO)
- ✅ Formato S##E## con mayúsculas y minúsculas (NUEVO)
- ✅ Variaciones de mayúsculas/minúsculas
- ✅ Diferentes tipos de guiones
- ✅ Con y sin acentos
- ✅ Casos inválidos (que no deben detectarse)

**Resultado:** ✅ 22/22 tests pasados

### Test de Detención al Cambiar de Serie

Se ha creado el archivo `test_series_switch.py` para verificar que el sistema se detiene correctamente:

```bash
python test_series_switch.py
```

Este script simula:
- ✅ Indexación de 3 episodios de Lucifer
- ✅ Detección de 5 episodios de Breaking Bad
- ✅ Sistema se detiene automáticamente (no indexa Breaking Bad)

**Resultado:** ✅ Sistema se detiene correctamente

## 🔄 Compatibilidad

- ✅ **100% compatible** con el sistema existente
- ✅ No rompe la indexación actual
- ✅ Agrega soporte para 2 nuevos formatos sin afectar los anteriores
- ✅ Los episodios ya indexados no se ven afectados

## 📊 Prioridad de Detección

Cuando un caption contiene múltiples formatos, el sistema:
1. Detecta primero el **formato español** (más específico)
2. Si no lo encuentra, busca el **formato S##E##**
3. Si no lo encuentra, busca el **formato corto** (incluye emoji-dash)
4. Si no encuentra ninguno, continúa al siguiente mensaje

Esto asegura que siempre se use el formato más explícito disponible.

## 🛡️ Protección contra Series Mixtas

El sistema incluye un mecanismo robusto para detenerse cuando detecta otra serie:

**Ejemplo práctico:**
```
Mensaje 100: "🔻Lucifer — 02x01 — Audio Latino"     ✅ INDEXADO
Mensaje 101: "🔻Lucifer — 02x05 — Audio Latino"     ✅ INDEXADO
Mensaje 102: "🔻Lucifer — 02x15 — Audio Latino"     ✅ INDEXADO
Mensaje 103: "Breaking Bad - S01E01 - 1080p.mp4"    ❌ No contiene "Lucifer" (1/5)
Mensaje 104: "Breaking Bad - S01E02 - 1080p.mp4"    ❌ No contiene "Lucifer" (2/5)
Mensaje 105: "Breaking Bad - S01E03 - 1080p.mp4"    ❌ No contiene "Lucifer" (3/5)
Mensaje 106: "Breaking Bad - S01E04 - 1080p.mp4"    ❌ No contiene "Lucifer" (4/5)
Mensaje 107: "Breaking Bad - S01E05 - 1080p.mp4"    ❌ No contiene "Lucifer" (5/5)
🛑 DETENCIÓN: Sistema se detuvo correctamente
```

**Características:**
- Verifica el nombre de la serie en cada caption (case insensitive)
- Cuenta mensajes consecutivos sin episodios válidos (máximo 5)
- Se detiene automáticamente al detectar otra serie
- NO indexa episodios de otras series

## 🚀 Despliegue

Los cambios están listos para usar. Solo necesitas:

1. ✅ Reiniciar el bot
2. ✅ Usar `/indexar_serie` como siempre
3. ✅ El sistema detectará automáticamente todos los 4 formatos

No se requieren cambios en la base de datos ni migraciones.

## 📚 Documentación Adicional

Se han creado nuevos archivos de documentación:

- **`FORMATOS_EPISODIOS.md`**: Guía completa de todos los formatos soportados
- **`test_series_switch.py`**: Test de detención al cambiar de serie
- **`ACTUALIZACION_FORMATOS_EPISODIOS.md`**: Este archivo (resumen de cambios)

---

**Fecha de actualización**: 3 de enero de 2026  
**Estado**: ✅ Probado y Funcional  
**Tests**: ✅ 22/22 pasados
