# 📢 Publicación Multi-Canal

## 🎯 ¿Qué es?

El bot puede publicar automáticamente las películas indexadas en **múltiples canales** de Telegram simultáneamente.

---

## ⚙️ Configuración

### **1. Variables de Entorno**

Agrega o modifica en tu archivo `.env`:

```env
# Canal principal (obligatorio)
VERIFICATION_CHANNEL_ID=-1003216346183

# Canales adicionales (opcional, separados por coma)
PUBLICATION_CHANNELS=-1003216346183,-1002345678901,-1002987654321
```

**Notas:**
- `VERIFICATION_CHANNEL_ID` es el canal donde se guarda el `channel_message_id` en la BD
- `PUBLICATION_CHANNELS` puede incluir el canal de verificación + otros canales
- Si `PUBLICATION_CHANNELS` está vacío, solo publica en `VERIFICATION_CHANNEL_ID`
- El bot debe ser **administrador** en todos los canales con permisos de publicar

---

## 🔧 En Render

1. Ve a tu servicio en Render Dashboard
2. **Environment** → **Add Environment Variable**
3. Agrega:
   - **Key:** `PUBLICATION_CHANNELS`
   - **Value:** `-1003216346183,-1002345678901,-1002987654321`
4. **Save Changes** → El servicio se redesplegará automáticamente

---

## 📋 Cómo Obtener el ID de un Canal

### **Método 1: Con @userinfobot**
1. Agrega el bot al canal (temporalmente)
2. Envía cualquier mensaje
3. El bot responderá con el ID del canal
4. Remueve el bot

### **Método 2: Forwarding**
1. Forward un mensaje del canal a @userinfobot
2. Te mostrará el ID

### **Método 3: Con tu bot**
1. Agrega tu bot al canal como admin
2. Envía un mensaje de prueba
3. Verifica los logs del bot (te mostrará el chat_id)

---

## ✅ Funcionamiento

Cuando indexas una película (`/indexar`, `/indexar_manual`, `/reindexar`):

1. 📥 Bot descarga el poster de TMDB
2. 📢 Publica en **todos los canales** de `PUBLICATION_CHANNELS`
3. 💾 Guarda solo el `message_id` del canal principal (`VERIFICATION_CHANNEL_ID`) en BD
4. ✅ Si falla en algún canal, continúa con los demás

---

## ⚠️ Limitaciones Actuales

- Solo se guarda el `channel_message_id` del canal principal en BD
- Al re-indexar, solo se elimina el mensaje del canal principal
- Los mensajes en canales secundarios permanecen (requiere eliminación manual)

---

## 🚀 Ejemplo Completo

### **.env local:**
```env
VERIFICATION_CHANNEL_ID=-1003216346183
PUBLICATION_CHANNELS=-1003216346183,-1002111111111,-1002222222222
```

### **Resultado:**
```
/indexar
↓
📥 Descargando poster...
📢 Publicando en 3 canal(es)...
✅ Publicado en canal -1003216346183 (message_id: 456)
✅ Publicado en canal -1002111111111 (message_id: 789)
✅ Publicado en canal -1002222222222 (message_id: 123)
💾 Guardado en BD con channel_message_id: 456
```

---

## 🔐 Permisos Requeridos

El bot necesita ser **administrador** en cada canal con:
- ✅ Publicar mensajes
- ✅ Enviar medios (fotos)

---

## 📝 Notas

- El canal de **almacenamiento** (`STORAGE_CHANNEL_ID`) **NUNCA** recibe posts de películas
- Solo se publican películas indexadas con éxito en TMDB
- Los posts incluyen:
  - 🎬 Título y año
  - ⭐ Rating de TMDB
  - 📝 Overview (descripción)
  - 🖼️ Poster
  - ▶️ Botón "Ver Ahora" (deep link al bot)

---

## 🆘 Solución de Problemas

### **Error: "Forbidden: bot is not a member of the channel"**
→ Agrega el bot al canal como administrador

### **Error: "Bad Request: CHAT_ADMIN_REQUIRED"**
→ El bot no tiene permisos suficientes en el canal

### **No publica en todos los canales**
→ Verifica los logs de Render para ver qué canal está fallando

### **Solo quiero publicar en un canal adicional, no en verificación**
→ Configura solo ese canal en `PUBLICATION_CHANNELS`, el sistema automáticamente incluirá `VERIFICATION_CHANNEL_ID`

---

## 📊 Logs de Ejemplo

```
📢 Publicando en 3 canal(es)...
✅ Publicado en canal -1003216346183 (message_id: 456)
✅ Publicado en canal -1002111111111 (message_id: 789)
❌ Error publicando en canal -1002999999999: Forbidden: bot is not a member of the channel
```
