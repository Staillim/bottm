# 🤖 Búsqueda Inteligente en Grupos

## 📋 Descripción

Esta funcionalidad permite que el bot detecte automáticamente cuando alguien menciona el nombre de una película o serie en un grupo y responda con los resultados disponibles.

## 🚀 Características

### ✨ Detección Automática
- El bot analiza mensajes en grupos para detectar posibles búsquedas de películas/series
- Filtra conversaciones casuales para evitar respuestas innecesarias
- Solo responde cuando hay alta confianza de que es una búsqueda real

### 🎯 Sistema Inteligente
El bot detecta búsquedas cuando:
- El mensaje contiene patrones como "alguien tiene", "busco", "hay", "donde veo"
- El texto tiene formato de título (palabras capitalizadas)
- Se menciona un año (ej: "Avengers 2019")
- Se menciona temporada/capítulo (ej: "temporada 2")
- El mensaje es corto y específico (2-6 palabras)

### 🛡️ Filtros Anti-Spam
El bot NO responde cuando:
- El mensaje es muy corto (< 3 caracteres) o muy largo (> 100 caracteres)
- El mensaje contiene principalmente palabras conversacionales comunes
- Es un comando (empieza con `/`)
- No hay resultados en la base de datos
- El score de confianza es bajo (< 70%)

## 📖 Uso

### Modo Automático
Simplemente escribe en el grupo el nombre de la película o serie:

```
Usuario: Alguien tiene Avengers Endgame?
Bot: 🎬 Encontré esto para: Avengers Endgame
     📽️ Películas:
     1. Avengers: Endgame (2019) ⭐8.3
     [Botón: 📹 Avengers: Endgame]
```

### Modo Manual (Comando)
También puedes usar el comando `/search_group` para búsquedas explícitas:

```
/search_group Spider-Man
```

## ⚙️ Configuración

### Parámetros Ajustables
En [`handlers/group_search.py`](handlers/group_search.py):

```python
MIN_QUERY_LENGTH = 3           # Mínimo de caracteres para búsqueda
MIN_CONFIDENCE_SCORE = 0.7     # Score mínimo para responder (70%)
MAX_AUTO_RESULTS = 3           # Máximo de resultados a mostrar
```

### Permisos del Bot en Grupos

El bot necesita los siguientes permisos en el grupo:
- ✅ **Leer mensajes** - Para detectar búsquedas
- ✅ **Enviar mensajes** - Para responder con resultados
- ✅ **Enviar enlaces inline** - Para botones interactivos

### Agregar el Bot a un Grupo

1. **Invitar el bot:**
   - Abre el grupo en Telegram
   - Click en el nombre del grupo → "Agregar miembros"
   - Busca `@tu_bot_username`
   - Agrégalo al grupo

2. **Configurar permisos:**
   - Ve a "Configuración del grupo"
   - "Administradores" → Agrega el bot como admin (opcional)
   - O asegúrate que "Todos los miembros" pueden enviar mensajes

3. **Habilitar modo Privacy OFF** (importante):
   - Habla con [@BotFather](https://t.me/BotFather)
   - Envía `/setprivacy`
   - Selecciona tu bot
   - Selecciona **Disable** (para que el bot pueda leer mensajes)

## 🔧 Configuración en BotFather

Para que el bot funcione en grupos, debes desactivar el modo privacidad:

```
1. Abre @BotFather
2. Envía: /setprivacy
3. Selecciona tu bot
4. Selecciona: Disable
5. Confirma: Disabled - the bot will receive all messages
```

**⚠️ Importante:** Sin desactivar el modo privacidad, el bot solo recibirá mensajes que:
- Empiecen con `/`
- Sean respuestas a mensajes del bot
- Mencionen al bot con `@`

## 📊 Ejemplos de Uso

### Ejemplo 1: Búsqueda Directa
```
👤 Usuario: Spider-Man No Way Home
🤖 Bot: 🎬 Encontré esto para: Spider-Man No Way Home
         📽️ Películas:
         1. Spider-Man: No Way Home (2021) ⭐8.4
         [Botón para ver]
```

### Ejemplo 2: Pregunta Natural
```
👤 Usuario: Alguien tiene la película de Avatar 2?
🤖 Bot: 🎬 Encontré esto para: Avatar 2
         📽️ Películas:
         1. Avatar: The Way of Water (2022) ⭐7.7
         [Botón para ver]
```

### Ejemplo 3: Serie
```
👤 Usuario: Hay The Last of Us?
🤖 Bot: 🎬 Encontré esto para: The Last of Us
         📺 Series:
         1. The Last of Us (2023)
         [Botón para ver]
```

### Ejemplo 4: Sin Respuesta (Conversación Casual)
```
👤 Usuario: Hola, cómo están todos?
🤖 Bot: [No responde - detecta que es conversación]
```

## 🎛️ Sistema de Confianza (Confidence Score)

El bot calcula un score de 0.0 a 1.0 para decidir si responder:

| Factor | Puntos |
|--------|--------|
| Hay resultados en BD | +0.3 |
| Query corto y específico (1-4 palabras) | +0.2 |
| Contiene palabras de búsqueda ("busco", "hay", etc) | +0.3 |
| Coincidencia exacta con título | +0.2 |
| Mensaje muy largo (>15 palabras) | -0.3 |

**Umbral:** Solo responde si score ≥ 0.7

## 🔍 Patrones de Detección

El sistema reconoce estos patrones:

```python
✅ "alguien tiene/vio/conoce..."
✅ "busco..."
✅ "tienen..."
✅ "hay..."
✅ "donde esta/veo/encuentro..."
✅ "como se llama..."
✅ "pelicula de..."
✅ "serie de..."
✅ Menciones de años (2019, 2023, etc)
✅ "temporada X" / "capitulo X"
✅ Títulos con formato capitalizado
```

## 📝 Registro de Búsquedas

Todas las búsquedas en grupos se registran en la base de datos con metadata:

```python
await db.log_search(
    user_id, 
    query, 
    results_count,
    metadata={
        'source': 'group',
        'chat_id': chat_id
    }
)
```

Esto permite analizar:
- Qué grupos usan más el bot
- Qué buscan los usuarios en grupos
- Efectividad de la detección automática

## 🚦 Flujo de Funcionamiento

```
Mensaje en grupo
    ↓
¿Es comando? → Sí → Ignorar
    ↓ No
¿Muy corto/largo? → Sí → Ignorar
    ↓ No
¿Parece búsqueda? → No → Ignorar
    ↓ Sí
Buscar en BD
    ↓
¿Hay resultados? → No → Ignorar
    ↓ Sí
Calcular confidence
    ↓
¿Score ≥ 0.7? → No → Ignorar
    ↓ Sí
Responder con resultados
```

## 🎨 Personalización

### Modificar Palabras Ignoradas

Edita el set `IGNORE_WORDS` en [`handlers/group_search.py`](handlers/group_search.py):

```python
IGNORE_WORDS = {
    'hola', 'hi', 'hello', 
    # Agrega más palabras...
}
```

### Ajustar Patrones de Búsqueda

Modifica la lista `search_indicators` en la función `is_potential_search_query()`:

```python
search_indicators = [
    r'mi_patron_personalizado',
    # Agrega más patrones regex...
]
```

### Cambiar Mensaje de Respuesta

Modifica la función `send_group_results()` para personalizar el formato:

```python
text = f"🎬 Tu mensaje personalizado: *{query}*\n\n"
```

## 🐛 Troubleshooting

### El bot no responde en grupos

1. ✅ Verifica que el bot esté en el grupo
2. ✅ Verifica que Privacy Mode esté **Disabled** en BotFather
3. ✅ Confirma que el bot tiene permisos para leer/enviar mensajes
4. ✅ Revisa los logs para ver si detecta los mensajes

### El bot responde demasiado

- Aumenta `MIN_CONFIDENCE_SCORE` a 0.8 o 0.9
- Agrega más palabras a `IGNORE_WORDS`
- Reduce `MAX_AUTO_RESULTS`

### El bot no responde suficiente

- Reduce `MIN_CONFIDENCE_SCORE` a 0.5 o 0.6
- Ajusta los patrones en `search_indicators`
- Verifica que hay contenido en la base de datos

## 📈 Próximas Mejoras

Posibles mejoras futuras:

- [ ] Machine Learning para mejor detección
- [ ] Caché de búsquedas frecuentes
- [ ] Configuración por grupo (activar/desactivar)
- [ ] Estadísticas de uso por grupo
- [ ] Respuestas personalizadas por grupo
- [ ] Rate limiting por usuario/grupo
- [ ] Detección de idioma
- [ ] Búsqueda fuzzy mejorada

## 💡 Tips

1. **Menos es más**: Mejor responder poco pero acertado que mucho y molesto
2. **Monitorea el uso**: Revisa los logs para ajustar los parámetros
3. **Escucha feedback**: Los usuarios te dirán si es muy activo o poco
4. **Empieza conservador**: Es mejor comenzar con score alto (0.8) y bajarlo según necesidad

## 📚 Archivos Modificados

- ✅ [`handlers/group_search.py`](handlers/group_search.py) - Handler principal (NUEVO)
- ✅ [`main.py`](main.py) - Integración del handler
- ✅ [`database/db_manager.py`](database/db_manager.py) - Soporte para metadata en búsquedas

## 🤝 Soporte

Si tienes problemas o sugerencias:
1. Revisa los logs del bot
2. Verifica la configuración de BotFather
3. Ajusta los parámetros según tu caso de uso
