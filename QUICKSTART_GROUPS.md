# 🚀 Guía Rápida: Habilitar Búsqueda en Grupos

## ✅ Checklist de Configuración

### 1️⃣ Configurar el Bot en BotFather

```
1. Abre @BotFather en Telegram
2. Envía: /setprivacy
3. Selecciona tu bot de la lista
4. Selecciona: Disable
5. ✅ Verás: "Privacy mode disabled"
```

**¿Por qué?** El bot necesita leer todos los mensajes para detectar búsquedas.

---

### 2️⃣ Agregar el Bot al Grupo

```
1. Abre tu grupo en Telegram
2. Toca el nombre del grupo (arriba)
3. Toca "Agregar miembros"
4. Busca: @tu_bot_username
5. Toca "Agregar"
```

---

### 3️⃣ Dar Permisos al Bot

El bot necesita poder:
- ✅ Leer mensajes
- ✅ Enviar mensajes
- ✅ Enviar botones inline

**Opción A: Hacer admin al bot** (recomendado)
```
1. Ve a "Configuración del grupo"
2. Toca "Administradores"
3. Toca "Agregar administrador"
4. Selecciona tu bot
5. Asegúrate que tenga estos permisos:
   ✅ Enviar mensajes
   ✅ Enviar enlaces
```

**Opción B: Configurar permisos de grupo**
```
1. Ve a "Configuración del grupo"
2. Toca "Permisos"
3. Asegúrate que "Todos los miembros" pueden:
   ✅ Enviar mensajes
```

---

### 4️⃣ Probar el Bot

**Test 1: Búsqueda automática**
```
Escribe en el grupo: "Alguien tiene Spider-Man?"
```
✅ El bot debe responder con resultados

**Test 2: Búsqueda manual**
```
Escribe en el grupo: /search_group Avatar
```
✅ El bot debe responder con resultados

**Test 3: Conversación normal**
```
Escribe en el grupo: "Hola, cómo están?"
```
✅ El bot NO debe responder (ignora conversación)

---

## 🎛️ Ajustar Sensibilidad

Si el bot responde demasiado o muy poco, edita [`config/group_search_config.py`](config/group_search_config.py):

### Bot responde demasiado (muchos falsos positivos)
```python
# Aumentar el threshold
MIN_CONFIDENCE_SCORE = 0.8  # o 0.9 para ser muy estricto
```

### Bot no responde suficiente
```python
# Bajar el threshold
MIN_CONFIDENCE_SCORE = 0.6  # o 0.5 para ser más permisivo
```

---

## 🔍 Ejemplos de Uso

### ✅ Mensajes que el bot DETECTA:

```
"Alguien tiene Avengers?"
"Busco Spider-Man"
"Hay Breaking Bad?"
"Donde veo The Last of Us"
"Avatar 2022"
"Spider-Man No Way Home"
"temporada 2 de The Walking Dead"
"La película de Thor"
```

### ❌ Mensajes que el bot IGNORA:

```
"Hola, cómo están?"
"Jajaja que gracioso"
"Gracias por la info"
"Ok, nos vemos"
"¿Alguien está despierto?"  (conversación general)
```

---

## 🐛 Solución de Problemas

### ❌ El bot no responde en absoluto

**Causa 1: Privacy mode activado**
- Solución: Ve a BotFather y desactívalo (paso 1)

**Causa 2: Bot no tiene permisos**
- Solución: Hazlo admin o revisa permisos del grupo (paso 3)

**Causa 3: Bot no está en el grupo**
- Solución: Agrégalo al grupo (paso 2)

**Verificar:**
```bash
# En el servidor, revisa los logs
python main.py
# Deberías ver logs cuando alguien escribe en el grupo
```

---

### ⚠️ El bot responde a TODO

**Causa: Confidence score muy bajo**

Solución:
```python
# En config/group_search_config.py
MIN_CONFIDENCE_SCORE = 0.8  # Subir a 0.8 o 0.9
```

---

### 🤔 El bot responde a veces sí, a veces no

Esto es **NORMAL**. El bot usa inteligencia para:
- Detectar si es una búsqueda real
- Verificar si hay resultados en la base de datos
- Calcular score de confianza antes de responder

Si quieres más control, usa el comando manual:
```
/search_group <nombre de película>
```

---

## 📊 Monitorear el Bot

### Ver estadísticas
```
/stats  (solo admins)
```

### Ver logs en tiempo real
```bash
# En el servidor
tail -f bot.log
```

### Probar detección sin producción
```bash
python test_group_search.py
```

---

## ⚡ Tips Pro

### 1. Responder solo en horario específico

Edita `handlers/group_search.py`:
```python
from datetime import datetime

async def handle_group_message(update, context):
    # Solo responder entre 9 AM y 11 PM
    hour = datetime.now().hour
    if hour < 9 or hour > 23:
        return
    
    # ... resto del código
```

### 2. Desactivar en grupos específicos

```python
# Lista de grupos donde NO responder
BLACKLISTED_GROUPS = [-1001234567890, -1009876543210]

async def handle_group_message(update, context):
    if update.message.chat.id in BLACKLISTED_GROUPS:
        return
    
    # ... resto del código
```

### 3. Activar solo con palabra clave

```python
ACTIVATION_KEYWORDS = ['bot', 'búsqueda', 'película']

async def handle_group_message(update, context):
    message_lower = update.message.text.lower()
    if not any(keyword in message_lower for keyword in ACTIVATION_KEYWORDS):
        return
    
    # ... resto del código
```

### 4. Rate limiting por usuario

```python
from datetime import datetime, timedelta

last_searches = {}  # {user_id: datetime}
COOLDOWN_SECONDS = 60  # 1 minuto entre búsquedas por usuario

async def handle_group_message(update, context):
    user_id = update.effective_user.id
    now = datetime.now()
    
    if user_id in last_searches:
        time_diff = (now - last_searches[user_id]).total_seconds()
        if time_diff < COOLDOWN_SECONDS:
            return  # Usuario en cooldown
    
    last_searches[user_id] = now
    # ... resto del código
```

---

## 📝 Recordatorio Final

### Antes de activar en grupos grandes:

1. ✅ Prueba en un grupo de prueba pequeño
2. ✅ Ajusta `MIN_CONFIDENCE_SCORE` según necesites
3. ✅ Monitorea los primeros días
4. ✅ Escucha feedback de usuarios
5. ✅ Ajusta configuración según el uso real

### El bot está diseñado para:

- ✅ **Ayudar** a encontrar contenido rápidamente
- ✅ **No molestar** con respuestas innecesarias
- ✅ **Ser inteligente** al detectar búsquedas reales

---

## 🎯 Meta

El objetivo es que el bot sea **útil pero discreto**. Prefiere que responda poco pero acertado, que mucho y molesto.

---

## 💬 ¿Necesitas ayuda?

1. Lee la documentación completa: [README_GROUP_SEARCH.md](README_GROUP_SEARCH.md)
2. Revisa los logs del bot
3. Prueba con `test_group_search.py`
4. Ajusta la configuración según tus necesidades

---

**¡Listo! Tu bot ya está funcionando en grupos 🎉**
