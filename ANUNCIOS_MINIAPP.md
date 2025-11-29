# 📺 Sistema de Anuncios con Mini App - CineStelar Bot

## 🎯 ¿Cómo Funciona?

### Flujo del Usuario:
1. Usuario busca una película con `/buscar`
2. Selecciona la película que desea ver
3. Bot envía botón "📺 Ver Anuncio para Continuar"
4. Usuario toca el botón → Se abre Mini App
5. Mini App muestra anuncio recompensado (libtl.com)
6. Usuario ve el anuncio completo
7. Mini App notifica al bot que el anuncio fue visto
8. Bot envía automáticamente la película al usuario

## 🏗️ Arquitectura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Usuario   │─────▶│  Bot Telegram│─────▶│  Mini App   │
└─────────────┘      └──────────────┘      └─────────────┘
                             │                     │
                             │                     ▼
                             │              ┌─────────────┐
                             │              │   libtl.com │
                             │              │  (Anuncios) │
                             │              └─────────────┘
                             │                     │
                             ▼                     │
                      ┌──────────────┐            │
                      │  Base Datos  │◀───────────┘
                      │   (Tokens)   │
                      └──────────────┘
                             │
                             ▼
                      Video enviado ✅
```

## 📁 Archivos Nuevos

### 1. `webapp/ad_viewer.html` - Mini App de Anuncios
- Interfaz web que muestra el anuncio
- Integra SDK de libtl.com
- Muestra poster y título de la película
- Notifica al servidor cuando el anuncio termina

### 2. `webapp_server.py` - Servidor Flask
- Sirve la Mini App HTML
- Endpoint `/api/ad-completed` recibe notificaciones
- Valida tokens de anuncios
- Envía video automáticamente después del anuncio

### 3. `database/models.py` - Modelo AdToken
```python
class AdToken:
    token: str          # Token único
    user_id: int        # ID del usuario
    video_id: int       # ID del video
    completed: bool     # ¿Anuncio visto?
    created_at: datetime
    completed_at: datetime
```

## 🔧 Configuración

### 1. Variables de Entorno (.env)
```env
BOT_USERNAME=CineStelar_bot
WEBAPP_URL=https://tu-dominio.com/ad_viewer.html
FLASK_PORT=5000
```

### 2. Instalar Dependencias
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Iniciar Servicios
```powershell
# Opción A: Script automático (recomendado)
.\start_bot.ps1

# Opción B: Manual (2 terminales)
# Terminal 1 - Servidor Web:
python webapp_server.py

# Terminal 2 - Bot:
python main.py
```

## 🌐 Hosting (IMPORTANTE)

Para que la Mini App funcione, necesitas **hosting público** porque Telegram requiere HTTPS:

### Opción 1: ngrok (Pruebas rápidas)
```powershell
# Instalar ngrok
winget install ngrok

# Ejecutar túnel
ngrok http 5000

# Copiar URL HTTPS que te da (ej: https://abc123.ngrok.io)
# Actualizar .env:
WEBAPP_URL=https://abc123.ngrok.io/ad_viewer.html
```

### Opción 2: Render (Gratis, permanente)
1. Ve a https://render.com
2. Crea nuevo "Web Service"
3. Conecta tu repositorio Git
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python webapp_server.py`
6. Copia tu URL: `https://tu-app.onrender.com`
7. Actualiza `.env`:
```env
WEBAPP_URL=https://tu-app.onrender.com/ad_viewer.html
```

### Opción 3: Vercel (Para archivos estáticos)
```powershell
npm i -g vercel
cd webapp
vercel --prod
```

### Opción 4: Railway.app
Similar a Render, con plan gratuito.

## ⚙️ Configurar Bot en BotFather

Después de tener tu dominio público:

1. Abre @BotFather en Telegram
2. Envía `/setdomain`
3. Selecciona tu bot (@CineStelar_bot)
4. Envía tu dominio: `tu-dominio.com`

Esto permite que tu Mini App funcione correctamente.

## 🧪 Probar Localmente (Sin hosting)

Para pruebas **SIN anuncios reales**, puedes comentar la llamada al anuncio:

En `webapp/ad_viewer.html` línea ~85:
```javascript
async function showAd() {
    // Comentar para pruebas:
    // await show_10253964();
    
    // Descomentar para simular:
    setTimeout(() => onAdComplete(), 3000); // Simula 3 segundos
}
```

## 📊 Base de Datos

El sistema guarda tokens en `bot_database.db`:

```sql
CREATE TABLE ad_tokens (
    id INTEGER PRIMARY KEY,
    token VARCHAR(100) UNIQUE,
    user_id BIGINT,
    video_id INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    completed_at DATETIME
);
```

## 🔒 Seguridad

- Tokens únicos (32 bytes aleatorios)
- Tokens de un solo uso (no reutilizables)
- Validación de usuario y video
- Timeout automático (puedes agregarlo)

## 🐛 Troubleshooting

### Error: "Mini App no se abre"
**Solución:** Configura dominio en @BotFather con `/setdomain`

### Error: "Token inválido"
**Solución:** Verifica que WEBAPP_URL esté configurado correctamente

### Error: "Video no se envía"
**Solución:** Revisa logs de Flask en terminal del servidor

### Error: "Anuncio no carga"
**Solución:** Verifica que el script de libtl.com esté accesible (zona 10253964)

## 📝 Modificar Anuncios

Para cambiar el formato de anuncio en `webapp/ad_viewer.html`:

```javascript
// Intersticial Recompensado (actual - RECOMENDADO)
await show_10253964();

// Popup Recompensado
await show_10253964('pop');

// Intersticial In-App
show_10253964({
  type: 'inApp',
  inAppSettings: {
    frequency: 2,
    capping: 0.1,
    interval: 30
  }
})
```

## 📈 Monitoreo

Ver estadísticas de tokens:
```sql
-- Tokens completados hoy
SELECT COUNT(*) FROM ad_tokens 
WHERE completed = 1 
AND DATE(completed_at) = DATE('now');

-- Tokens pendientes
SELECT COUNT(*) FROM ad_tokens 
WHERE completed = 0;
```

## 🚀 Próximos Pasos

1. **Subir a hosting público** (Render/Railway recomendado)
2. **Configurar dominio en BotFather**
3. **Resetear base de datos** (para regenerar con AdToken):
```powershell
Remove-Item bot_database.db
python main.py  # Crea BD nueva con AdToken
```
4. **Probar flujo completo**
5. **Monitorear logs**

## 💡 Ventajas de este Sistema

✅ Anuncios reales monetizables (libtl.com paga)
✅ Usuario NO puede saltarse el anuncio
✅ Experiencia fluida (Mini App integrada en Telegram)
✅ Tokens seguros de un solo uso
✅ Envío automático después del anuncio
✅ Base de datos para analytics

## 🆘 Soporte

Si tienes problemas:
1. Revisa logs del servidor Flask
2. Revisa logs del bot
3. Verifica que ambos servicios estén corriendo
4. Confirma que WEBAPP_URL es accesible públicamente

---

**Desarrollado para CineStelar Bot** 🎬
