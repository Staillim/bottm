# Configuración de Notificaciones a Grupos

## 📱 Funcionamiento

Ahora el bot puede enviar notificaciones automáticas a grupos cuando se indexan nuevas películas o series. Estas son notificaciones cortas que incluyen un botón para que los usuarios vean el contenido directamente en el bot.

## ⚙️ Configuración

### 1. Variable de Entorno

Agrega la siguiente variable a tu archivo `.env`:

```bash
# IDs de grupos donde enviar notificaciones (separados por coma)
NOTIFICATION_GROUPS=-1001234567890,-1001098765432
```

### 2. Obtener ID de Grupo

Para obtener el ID de un grupo:

1. **Agrega tu bot al grupo** como administrador
2. **Envía un mensaje en el grupo** mencionando el bot: `@tu_bot hola`
3. **Revisa los logs** del bot para ver el `chat_id` del mensaje
4. **Copia el ID** (será un número negativo como `-1001234567890`)

### 3. Formato de IDs

- Los IDs de grupos **siempre empiezan con `-`** (número negativo)
- Si tienes múltiples grupos, **sepáralos por comas**
- **No uses espacios** entre comas e IDs

```bash
# ✅ Correcto
NOTIFICATION_GROUPS=-1001234567890,-1001098765432

# ❌ Incorrecto  
NOTIFICATION_GROUPS= -100123456789, -100109876543
```

## 📝 Tipos de Notificaciones

### Películas
Cuando se indexa una película nueva:
```
🆕 Nueva película agregada: Avengers Endgame (2019)
[🔍 Ver en el bot]
```

### Series
Cuando se indexa una serie completa:
```
📺 Nueva serie agregada: Breaking Bad (2008) - 62 episodios
[🔍 Ver en el bot]
```

## 🔧 Funcionalidades

- **Mensajes cortos**: No saturan los grupos con información excesiva
- **Deep links**: Al hacer clic se abre directamente la película/serie en el bot
- **Automático**: Se envía automáticamente al completar la indexación
- **Múltiples grupos**: Puedes configurar varios grupos
- **Resistente a errores**: Si falla en un grupo, continúa con los otros

## 🔒 Permisos del Bot

El bot necesita los siguientes permisos en cada grupo:

- **Enviar mensajes** ✅
- **Enviar enlaces** ✅

No necesita:
- Leer mensajes ❌
- Ser administrador ❌
- Eliminar mensajes ❌

## 🧪 Pruebas

Para probar que funciona:

1. **Configura un grupo de prueba** en `NOTIFICATION_GROUPS`
2. **Indexa una película** usando el comando `/indexar`
3. **Verifica** que llegue la notificación al grupo
4. **Haz clic en el botón** para confirmar que funciona el deep link

## ❓ Solución de Problemas

### No llegan las notificaciones

1. **Verifica que el bot esté en el grupo** y tenga permisos para enviar mensajes
2. **Revisa el ID del grupo** - debe ser negativo y correcto
3. **Mira los logs** del bot para ver errores específicos
4. **Prueba con un solo grupo** primero antes de agregar múltiples

### ID de grupo incorrecto

```bash
# Ver los logs cuando alguien escribe en el grupo:
# chat_id será el ID correcto del grupo
```

### Bot bloqueado en el grupo

Si el bot fue bloqueado o removido del grupo:
- Lo verás en los logs como error de permisos
- Re-agrega el bot al grupo
- Dale los permisos necesarios

## 📊 Logs

Los logs mostrarán:

```
📱 Enviando notificaciones a 2 grupo(s)...
✅ Notificación enviada al grupo -1001234567890  
✅ Notificación enviada al grupo -1001098765432
```

O en caso de error:
```
❌ Error enviando notificación al grupo -1001234567890: Bot was blocked by the user
```