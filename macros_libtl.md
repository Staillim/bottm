# Macros de libtl.com - CineStelar Bot

## ID de Telegram
—
ID de la aplicación, en formato Int.

Valor: tg.initDataUnsafe?.user?.id
Tipo: Int
Fuente: Obtenido desde Telegram Web App SDK en ad_viewer.html
Uso: Identifica al usuario que ve el anuncio, enviado en el body del POST a /api/ad-completed

## Identificación de zona
—
ID de zona principal, en Int.

Valor: 10253964
Tipo: Int
Fuente: Configurado en data-zone del SDK en ad_viewer.html línea 8
Código: <script src='//libtl.com/sdk.js' data-zone='10253964' data-sdk='show_10253964'></script>

## ID de subzona
—
ID de la subzona específica donde ocurrió el evento, en Int.

Valor: No configurado
Tipo: Int opcional
Descripción: ID de la subzona específica donde ocurrió el evento

## Tipo de evento
—
Cadena impresión o clic según el evento.

Valor: impresión o clic
Tipo: String
Descripción: Detectado automáticamente por libtl.com SDK según la interacción del usuario

## Tipo de evento de recompensa
—
Cadena sí si el evento es pagado, o no.

Valor: sí
Tipo: String
Descripción: Es un evento pagado porque usa Rewarded Interstitial
Función: show_10253964() - Promise que se resuelve cuando el anuncio se completa

## Precio estimado
—
Precio estimado del evento, en formato decimal - x.xxxxx.

Valor: Calculado por libtl.com
Tipo: Decimal x.xxxxx
Descripción: Precio estimado del evento, determinado por la red publicitaria

## YMID
—
ID único del evento, transmitido desde su aplicación.

Valor: token parámetro URL
Tipo: String 32 bytes URL-safe
Fuente: Generado con secrets.token_urlsafe(32) en db_manager.py
Ejemplo: Pasado como ?token=abc123... en la URL del Mini App
Base de datos: Campo token en tabla AdToken UNIQUE, NOT NULL
Validación: Verificado en /api/ad-completed antes de enviar video

## Solicitud var
—
Identificación adicional para la ubicación del disparador.

Valor: video_id almacenado en AdToken
Tipo: Int
Fuente: ID del video en la base de datos que se desbloqueará
Flujo:
1. Usuario selecciona video → video_callback() en search.py
2. Se crea AdToken con video_id → db.create_ad_token(user_id, video.id, msg_id)
3. Se genera URL con token → webapp_url = WEBAPP_URL?token=...
4. Usuario ve anuncio → show_10253964()
5. Se valida token → ad_token = await db.get_ad_token(token)
6. Se envía video → bot.send_video(video_id=ad_token.video_id)

El formato de las dos últimas macros depende de los datos enviados originalmente desde TMA.

---

## Configuración actual del sistema:

### Frontend (Netlify)
- **URL**: https://bottm.netlify.app/ad_viewer.html
- **SDK**: libtl.com
- **Zona ID**: 10253964
- **Tipo**: Rewarded Interstitial
- **Función**: `show_10253964()`

### Backend (Render)
- **API Endpoint**: `/api/ad-completed`
- **Método**: POST
- **Body**: `{ token: string, user_id: int }`
- **Respuesta**: `{ success: bool, message/error: string }`

### Flujo de datos:
```
1. Bot genera token único (32 bytes)
2. Token se guarda en BD: AdToken(token, user_id, video_id, completed=False)
3. URL se construye: webapp_url?token=X&title=Y&poster=Z&api_url=W
4. Usuario abre Mini App → ve anuncio → show_10253964() completa
5. Mini App llama: POST api_url/api/ad-completed {token, user_id}
6. Backend valida token → marca completed=True → envía video
7. Usuario recibe video en Telegram
```

### Parámetros URL del Mini App:
- `token`: ID único del AdToken
- `title`: Título de la película (URL-encoded)
- `poster`: URL del poster (URL-encoded)
- `api_url`: URL del servidor API (URL-encoded, de API_SERVER_URL env var)

### Variables de entorno requeridas:
- `WEBAPP_URL`: https://bottm.netlify.app/ad_viewer.html
- `API_SERVER_URL`: URL de Render (ej: https://bottm.onrender.com)
- `BOT_TOKEN`: Token del bot de Telegram
- `STORAGE_CHANNEL_ID`: ID del canal con videos
