# 🎬 Bot de Películas y Series para Telegram

Bot de Telegram para buscar y compartir películas y series con sistema de tickets, referidos y búsqueda inteligente.

## 🌟 Características Principales

### 🔍 Búsqueda de Contenido
- **Búsqueda por comando**: `/buscar <término>` o `/search <término>`
- **Búsqueda contextual**: Interfaz interactiva con menús
- **Búsqueda inteligente en grupos**: El bot detecta automáticamente menciones de películas/series en grupos

### 🎟️ Sistema de Tickets
- Tickets para ver contenido sin anuncios
- Sistema de referidos: Gana 5 tickets por cada amigo invitado
- Ver tickets disponibles con `/mistickets`
- Obtener link de invitación con `/invitar`

### 👥 Funcionalidad en Grupos
- **Detección automática**: El bot identifica cuando alguien menciona películas/series
- **Respuestas inteligentes**: Solo responde cuando tiene alta confianza
- **Sin spam**: Filtra conversaciones casuales
- Ver documentación completa en [README_GROUP_SEARCH.md](README_GROUP_SEARCH.md)

### 📊 Panel de Administración
- Indexación automática y manual de contenido
- Estadísticas de uso
- Gestión de usuarios
- Sistema de broadcast
- Reposteo de videos

### 📺 Contenido
- Películas con información de TMDb
- Series organizadas por temporadas y episodios
- Ratings y descripciones
- Búsqueda avanzada

## 🚀 Instalación

### Requisitos
- Python 3.8+
- PostgreSQL (o compatible con Supabase)
- Bot de Telegram (crear con [@BotFather](https://t.me/BotFather))

### Pasos

1. **Clonar el repositorio**
```bash
git clone <tu-repo>
cd bot
```

2. **Crear entorno virtual**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

Crea un archivo `.env` con:
```env
BOT_TOKEN=tu_token_de_botfather
DATABASE_URL=postgresql://user:pass@host:5432/dbname
VERIFICATION_CHANNEL_USERNAME=tu_canal
ADMIN_USER_IDS=123456789,987654321
WEBAPP_URL=https://tu-webapp.netlify.app
TMDB_API_KEY=tu_api_key_de_tmdb
```

5. **Iniciar el bot**
```bash
python main.py
```

## 📖 Uso

### Comandos de Usuario

```
/start - Iniciar y ver menú principal
/buscar <término> - Buscar videos
/mistickets - Ver tickets disponibles
/invitar - Obtener link de invitación
/misreferidos - Ver referidos
/help - Ver ayuda
```

### Comandos de Administración

```
/admin - Panel de administración
/usuarios - Gestionar usuarios
/broadcast - Mensajes masivos
/indexar - Indexar películas automáticamente
/indexar_manual <msg_id> - Indexar película específica
/reindexar <msg_id> - Re-indexar película
/repost - Re-publicar videos
/indexar_serie <serie> - Indexar serie
/stats - Ver estadísticas
```

### Usar en Grupos

Para habilitar búsqueda inteligente en grupos:

1. **Agregar el bot al grupo**
2. **Configurar permisos de lectura**
3. **Desactivar Privacy Mode en BotFather:**
   ```
   /setprivacy
   [Seleccionar tu bot]
   Disable
   ```

Ver guía completa: [README_GROUP_SEARCH.md](README_GROUP_SEARCH.md)

## 🏗️ Estructura del Proyecto

```
bot/
├── main.py                 # Punto de entrada
├── config/
│   ├── settings.py         # Configuración general
│   └── group_search_config.py  # Config búsqueda en grupos
├── database/
│   ├── db_manager.py       # Gestión de base de datos
│   └── models.py           # Modelos SQLAlchemy
├── handlers/
│   ├── start.py            # Comando /start
│   ├── search.py           # Búsqueda de videos
│   ├── group_search.py     # Búsqueda inteligente en grupos (NUEVO)
│   ├── menu.py             # Menús interactivos
│   ├── admin.py            # Panel admin
│   ├── broadcast.py        # Mensajes masivos
│   ├── tickets.py          # Sistema de tickets
│   └── ...
├── utils/
│   ├── tmdb_api.py         # Integración TMDb
│   └── verification.py     # Verificación de canal
├── webapp/
│   ├── index.html          # Mini App
│   └── ad_viewer.html      # Visualizador de anuncios
└── netlify/
    └── functions/          # Funciones serverless
```

## 🔧 Configuración Avanzada

### Búsqueda en Grupos

Ajusta los parámetros en `config/group_search_config.py`:

```python
MIN_CONFIDENCE_SCORE = 0.7    # Score mínimo para responder
MAX_AUTO_RESULTS = 3          # Máximo de resultados
MIN_QUERY_LENGTH = 3          # Mínimo de caracteres
```

### Base de Datos

El bot usa PostgreSQL con las siguientes tablas:
- `users` - Información de usuarios
- `videos` - Películas indexadas
- `tv_shows` - Series
- `episodes` - Episodios de series
- `searches` - Historial de búsquedas
- `user_tickets` - Tickets de usuarios
- `referrals` - Sistema de referidos
- Ver esquema completo en `database/models.py`

### Integración TMDb

El bot usa The Movie Database API para obtener información de películas:
- Ratings
- Descripciones
- Posters
- Años de lanzamiento

Obtén tu API key en: https://www.themoviedb.org/settings/api

## 🧪 Testing

Prueba la funcionalidad de búsqueda en grupos:

```bash
python test_group_search.py
```

Esto ejecutará tests de:
- Detección de búsquedas potenciales
- Limpieza de queries
- Cálculo de confidence score
- Filtrado de palabras

## 📚 Documentación Adicional

- [README_GROUP_SEARCH.md](README_GROUP_SEARCH.md) - Guía completa de búsqueda en grupos
- [README_POINTS_SYSTEM.md](README_POINTS_SYSTEM.md) - Sistema de puntos
- [README_ANUNCIOS.md](README_ANUNCIOS.md) - Sistema de anuncios
- [GUIA_COMPLETA_DEPLOY.md](GUIA_COMPLETA_DEPLOY.md) - Guía de deployment
- [PLAN_BOT_TELEGRAM.md](PLAN_BOT_TELEGRAM.md) - Plan de desarrollo

## 🔐 Seguridad

- Tokens únicos para visualización de contenido
- Verificación de membresía en canal
- Sistema de rate limiting
- Tokens con expiración automática
- Limpieza periódica de tokens expirados

## 🚀 Deployment

### Render.com

El bot está configurado para deployment en Render con `render.yaml`:

```yaml
services:
  - type: web
    name: bot-telegram
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
```

### Netlify (WebApp)

La Mini App se despliega en Netlify:

```bash
netlify deploy --prod
```

Ver [NETLIFY_SETUP.md](NETLIFY_SETUP.md) para más detalles.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es privado. Todos los derechos reservados.

## 💬 Soporte

Para problemas o sugerencias, abre un issue en el repositorio.

## 🎯 Roadmap

### Próximas Características
- [ ] Machine Learning para mejor detección en grupos
- [ ] Caché de búsquedas frecuentes
- [ ] Configuración por grupo (activar/desactivar bot)
- [ ] Estadísticas de uso por grupo
- [ ] Detección de idioma
- [ ] Búsqueda fuzzy mejorada
- [ ] Integración con más fuentes de contenido

### En Progreso
- [x] Búsqueda inteligente en grupos
- [x] Sistema de tickets y referidos
- [x] Mini App con Telegram WebApp
- [x] Sistema de anuncios

## 📊 Estado del Proyecto

🟢 Activo y en desarrollo

---

Desarrollado con ❤️ para la comunidad de Telegram
