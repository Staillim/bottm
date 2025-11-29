# 🎬 Sistema de Anuncios Implementado - Guía Rápida

## ✅ Lo que se ha creado:

### 1. **Mini App de Anuncios** (`webapp/ad_viewer.html`)
- Interfaz web elegante con tema morado/rosa
- Muestra poster y título de la película
- Integra anuncios de libtl.com (zona 10253964)
- Animaciones y efectos visuales profesionales
- Cierra automáticamente después del anuncio

### 2. **Servidor Flask** (`webapp_server.py`)
- Sirve la Mini App
- API `/api/ad-completed` para validar anuncios
- Envía automáticamente el video después del anuncio
- Sistema de tokens seguros

### 3. **Base de Datos Extendida**
Nueva tabla `ad_tokens` para rastrear anuncios vistos:
```
- token (único, seguro)
- user_id
- video_id
- completed (boolean)
- created_at
- completed_at
```

### 4. **Handler Modificado** (`handlers/search.py`)
Ahora cuando el usuario selecciona una película:
1. Crea token único
2. Genera URL de Mini App con poster y título
3. Envía botón "📺 Ver Anuncio para Continuar"
4. Espera notificación de anuncio completado
5. Envía video automáticamente

## 🚀 Próximos Pasos OBLIGATORIOS:

### Paso 1: Conseguir Hosting Público

**¿Por qué?** Telegram Mini Apps requieren HTTPS. Tu `localhost` NO funciona.

#### Opciones Recomendadas:

**A) ngrok (MÁS RÁPIDO - Para pruebas)**
```powershell
# 1. Instalar ngrok
winget install ngrok

# 2. Crear cuenta en https://ngrok.com y obtener token
ngrok config add-authtoken TU_TOKEN_AQUI

# 3. En una terminal, iniciar túnel
ngrok http 5000

# 4. Copiar URL HTTPS que te da (ej: https://abc123.ngrok-free.app)
# 5. Actualizar .env
WEBAPP_URL=https://abc123.ngrok-free.app/ad_viewer.html
```

**B) Render.com (GRATIS - Permanente)**
```
1. Ir a https://render.com
2. Crear cuenta gratuita
3. New → Web Service
4. Connect Repository (sube tu código a GitHub primero)
5. Build Command: pip install -r requirements.txt
6. Start Command: python webapp_server.py
7. Esperar deploy (5-10 min)
8. Copiar URL: https://tu-app.onrender.com
9. Actualizar .env:
   WEBAPP_URL=https://tu-app.onrender.com/ad_viewer.html
```

**C) Railway.app (GRATIS - Fácil)**
Similar a Render, pero más rápido para deploy.

### Paso 2: Configurar Dominio en BotFather

Una vez tengas tu dominio público:

```
1. Abrir @BotFather en Telegram
2. Enviar: /setdomain
3. Seleccionar: @CineStelar_bot
4. Enviar tu dominio: tu-dominio.com (SIN https://)
```

### Paso 3: Iniciar Ambos Servicios

```powershell
# Opción A: Automático
.\start_bot.ps1

# Opción B: Manual (2 terminales)
# Terminal 1:
python webapp_server.py

# Terminal 2:
python main.py
```

## 📝 Testing Local (Sin hosting real)

Para probar el FLUJO sin anuncios reales:

1. Editar `webapp/ad_viewer.html` línea 85:
```javascript
async function showAd() {
    // Comentar para pruebas:
    // await show_10253964();
    
    // Descomentar para simular:
    setTimeout(() => onAdComplete(), 2000); // Simula anuncio de 2 segundos
}
```

2. Iniciar servidor local:
```powershell
python webapp_server.py
```

3. Probar Mini App en navegador:
```
http://localhost:5000/ad_viewer.html?token=test&title=Thor&poster=https://via.placeholder.com/300x450
```

## 🔧 Verificar Instalación

```powershell
# Verificar Flask
.\venv\Scripts\Activate.ps1
pip list | findstr flask

# Debe mostrar:
# flask         3.0.0
# flask-cors    4.0.0
```

## 📊 Archivos Creados/Modificados:

```
bot/
├── webapp/
│   └── ad_viewer.html          ← NUEVO: Mini App
├── webapp_server.py            ← NUEVO: Servidor Flask
├── start_bot.ps1               ← NUEVO: Script de inicio
├── ANUNCIOS_MINIAPP.md         ← NUEVO: Documentación
├── database/
│   ├── models.py               ← MODIFICADO: Agregado AdToken
│   └── db_manager.py           ← MODIFICADO: Métodos para tokens
├── handlers/
│   └── search.py               ← MODIFICADO: Envía Mini App
├── config/
│   └── settings.py             ← MODIFICADO: WEBAPP_URL, BOT_USERNAME
├── .env                        ← MODIFICADO: Variables nuevas
└── requirements.txt            ← MODIFICADO: Flask agregado
```

## ⚠️ IMPORTANTE ANTES DE USAR:

1. ❌ **NO funcionará sin hosting público**
2. ✅ Necesitas configurar ngrok o Render PRIMERO
3. ✅ Actualizar WEBAPP_URL en `.env`
4. ✅ Configurar dominio en @BotFather
5. ✅ Resetear base de datos (ya hecho)

## 🎯 Flujo Completo una vez configurado:

```
Usuario → /buscar thor
       ↓
Bot muestra resultados
       ↓
Usuario toca "Thor (2022)"
       ↓
Bot genera token único
       ↓
Bot envía botón "Ver Anuncio para Continuar"
       ↓
Usuario toca botón → Se abre Mini App
       ↓
Mini App muestra poster + anuncio de libtl.com
       ↓
Usuario ve anuncio completo
       ↓
Mini App notifica a servidor Flask: /api/ad-completed
       ↓
Servidor valida token
       ↓
Servidor envía poster + video al usuario
       ↓
✅ Usuario recibe película automáticamente
```

## 🆘 Si tienes problemas:

**Error: "Mini App no se abre"**
→ Verifica que `/setdomain` esté configurado en @BotFather

**Error: "Token inválido"**
→ Verifica que WEBAPP_URL en `.env` sea correcto

**Error: "Video no se envía"**
→ Revisa terminal de Flask para ver logs

**Error: "Anuncio no carga"**
→ Verifica conexión a libtl.com en navegador

## 📞 Siguiente Acción REQUERIDA:

**DEBES configurar hosting público (ngrok/Render) para que funcione.**

¿Quieres que te ayude a configurar ngrok paso a paso?
