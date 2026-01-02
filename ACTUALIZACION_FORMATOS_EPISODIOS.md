# Actualización del Sistema de Indexación de Series

## 🎯 Cambios Realizados

Se ha mejorado el sistema de indexación de series para reconocer **múltiples formatos** de numeración de episodios.

## 📝 Formatos Soportados

### 1. Formato Corto (existente mejorado)
- **Ejemplos:** `1x1`, `2x14`, `5X10`
- **Patrón:** `(\d+)[xX](\d+)`
- Compatible con mayúsculas y minúsculas en la 'x'

### 2. Formato Español (NUEVO)
- **Ejemplos:** 
  - `Temporada 2 - Capítulo 14`
  - `Temporada 1 - Capítulo 20`
  - `temporada 3 - capítulo 5`
- **Patrón:** `[Tt]emporada\s*(\d+)\s*[-–—]\s*[Cc]ap[ií]tulo\s*(\d+)`
- Características:
  - Case insensitive (mayúsculas/minúsculas)
  - Acepta diferentes tipos de guiones: `-`, `–`, `—`
  - Funciona con "Capítulo" o "Capitulo" (con o sin acento)

## 🔧 Funciones Actualizadas

### 1. `scan_channel_for_episodes()`
**Ubicación:** `handlers/series_admin.py`

**Mejoras:**
- Detecta automáticamente ambos formatos al escanear el canal
- Prioriza el formato español si ambos están presentes
- Extrae correctamente el título del episodio en ambos casos

**Orden de detección:**
1. Primero busca formato español
2. Si no encuentra, busca formato corto
3. Si no encuentra ninguno, continúa con el siguiente mensaje

### 2. `index_episode_reply()`
**Ubicación:** `handlers/series_admin.py`

**Mejoras:**
- Acepta ambos formatos al indexar manualmente
- Parsea correctamente los números de temporada y episodio
- Mantiene compatibilidad con el formato existente

### 3. Mensajes de ayuda actualizados

**Comando `/indexar_serie`:**
```
El sistema detecta automáticamente episodios en estos formatos:
- 1x1, 2x14 (formato corto)
- Temporada 1 - Capítulo 20 (formato español)
```

**Indexación manual:**
```
Puedes indexar manualmente respondiendo mensajes con cualquiera de estos formatos:

Formato corto:
1x1 (Temporada 1, Episodio 1)
2x5 (Temporada 2, Episodio 5)

Formato español:
Temporada 1 - Capítulo 20
Temporada 2 - Capítulo 14
```

## ✅ Ejemplos de Uso

### Captions Válidos

#### Formato Corto:
```
Loki 1x1 - El inicio
Dexter 2x14 Final de temporada
Breaking Bad 5X10
```

#### Formato Español:
```
Loki Temporada 2 - Capítulo 14 - El final
Dexter Temporada 1 - Capítulo 20
Breaking Bad Temporada 3 - Capítulo 5 - La decisión
Game of Thrones temporada 8 - capítulo 6
```

### Variaciones Aceptadas

- **Mayúsculas/minúsculas:** ✅ `TEMPORADA 4 - CAPÍTULO 13`
- **Diferentes guiones:** ✅ `Temporada 5 – Capítulo 10` (guion largo)
- **Sin acento:** ✅ `Temporada 3 - Capitulo 7`
- **Espacios variables:** ✅ `Temporada  2  -  Capítulo  8`

## 🧪 Testing

Se ha creado el archivo `test_episode_patterns.py` para validar todos los patrones:

```bash
python test_episode_patterns.py
```

Este script prueba:
- ✅ Formato corto con 'x' minúscula
- ✅ Formato corto con 'X' mayúscula
- ✅ Formato español estándar
- ✅ Variaciones de mayúsculas/minúsculas
- ✅ Diferentes tipos de guiones
- ✅ Con y sin acentos
- ✅ Casos inválidos (que no deben detectarse)

## 🔄 Compatibilidad

- ✅ **100% compatible** con el sistema existente
- ✅ No rompe la indexación actual
- ✅ Agrega soporte para nuevo formato sin afectar el anterior
- ✅ Los episodios ya indexados no se ven afectados

## 📊 Prioridad de Detección

Cuando un caption contiene ambos formatos, el sistema:
1. Detecta primero el formato español
2. Si no lo encuentra, busca el formato corto
3. Si no encuentra ninguno, continúa al siguiente mensaje

Esto asegura que siempre se use el formato más explícito disponible.

## 🚀 Despliegue

Los cambios están listos para usar. Solo necesitas:

1. ✅ Reiniciar el bot
2. ✅ Usar `/indexar_serie` como siempre
3. ✅ El sistema detectará automáticamente ambos formatos

No se requieren cambios en la base de datos ni migraciones.
