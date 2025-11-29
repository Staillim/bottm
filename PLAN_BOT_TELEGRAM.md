# 🤖 Bot de Videos de Telegram - Plan Completo

## 📋 Descripción del Proyecto

Bot de Telegram que permite a los usuarios buscar y recibir videos desde un canal/grupo de almacenamiento, con verificación obligatoria de membresía en un canal.

---

## 🎯 Funcionalidades Principales

### 1. **Sistema de Verificación**
- Al iniciar el bot (`/start`), verificar si el usuario es miembro del canal requerido
- Si no es miembro, mostrar botón para unirse al canal
- Bloquear acceso a funciones hasta completar la verificación
- Re-verificar periódicamente o antes de cada búsqueda

### 2. **Sistema de Búsqueda**
- Comandos: `/buscar <término>` o `/search <término>`
- Búsqueda por palabras clave en títulos/descripciones de videos
- Mostrar resultados en lista numerada con botones inline
- Máximo 10 resultados por búsqueda

### 3. **Sistema de Entrega**
- Al seleccionar un video, el bot lo reenvía al usuario
- Incluir información: título, duración, tamaño
- Opción de "Buscar otro video"

### 4. **Características Adicionales Recomendadas**
- `/help` - Muestra instrucciones de uso
- `/stats` - Estadísticas personales (videos vistos)
- Sistema de categorías o tags
- Búsqueda por ID directo
- Historial de búsquedas del usuario
- Sistema de favoritos
- Paginación de resultados (siguiente/anterior)
- Modo inline query (búsqueda desde cualquier chat)

---

## 🏗️ Arquitectura del Sistema

```
Usuario → Bot → Verificación Canal
              ↓
         Base de Datos ← Canal/Grupo Almacén
              ↓         (Videos + Metadata)
         Búsqueda
              ↓
      Resultados → Selección → Reenvío
```

### Componentes:

1. **Bot Principal** (Python + python-telegram-bot)
2. **Base de Datos** (SQLite o PostgreSQL)
   - Tabla: usuarios (user_id, verificado, último_acceso)
   - Tabla: videos (file_id, título, descripción, tags, mensaje_id)
   - Tabla: búsquedas (user_id, término, timestamp)
   - Tabla: favoritos (user_id, video_id)

3. **Canal de Verificación** (público o privado)
4. **Grupo/Canal de Almacén** (donde están los videos)

---

## 🛠️ Tecnologías Requeridas

### Stack Recomendado:
- **Lenguaje**: Python 3.9+
- **Librería Bot**: `python-telegram-bot` v20+
- **Base de Datos**: 
  - Opción 1: SQLite (simple, local)
  - Opción 2: PostgreSQL (producción)
- **ORM**: SQLAlchemy (opcional pero recomendado)
- **Hosting**: 
  - Opción 1: VPS (DigitalOcean, AWS EC2)
  - Opción 2: PythonAnywhere (gratis limitado)
  - Opción 3: Railway.app
  - Opción 4: Heroku

### Dependencias Python:
```
python-telegram-bot>=20.0
python-dotenv
sqlalchemy
aiosqlite (si usas SQLite)
```

---

## 📝 Pasos para Crear el Bot desde Cero

### Fase 1: Configuración Inicial

#### 1.1 Crear el Bot en Telegram
1. Abre Telegram y busca `@BotFather`
2. Envía el comando `/newbot`
3. Elige un nombre para tu bot (ej: "Video Finder Bot")
4. Elige un username (debe terminar en 'bot', ej: `videofinderXYZ_bot`)
5. **Guarda el TOKEN** que te da BotFather (algo como: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 1.2 Configurar el Bot en BotFather
```
/setdescription - Descripción del bot
/setabouttext - Texto "Acerca de"
/setuserpic - Foto de perfil
/setcommands - Configurar comandos:
  start - Iniciar el bot
  buscar - Buscar videos
  search - Search videos
  help - Ayuda y comandos
  stats - Tus estadísticas
```

#### 1.3 Crear Canal de Verificación
1. Crea un canal en Telegram
2. Hazlo público o privado (anota el @username o link)
3. **Agrega tu bot al canal como administrador:**
   - Ve a tu canal → Administradores → Agregar administrador
   - Busca `@CineStelar_bot` y agrégalo
   - Dale permisos de "Post messages" mínimo
4. **Publica un mensaje** cualquiera en el canal (ej: "test")
5. **Obtén el CHANNEL_ID** abriendo este link en tu navegador:
   ```
   https://api.telegram.org/bot8352053218:AAGNe-yZ-_nXTEFFuSulfUJ5MUGPOPzwIaY/getUpdates
   ```
6. Busca en la respuesta JSON: `"chat":{"id":-100XXXXXXXXXX`
7. Ese número negativo es tu **CHANNEL_ID** (cópialo completo con el `-`)

#### 1.4 Crear Grupo/Canal de Almacén
1. Crea un **nuevo grupo o canal** para almacenar videos (diferente al canal de verificación)
2. **Agrega `@CineStelar_bot` como administrador** con permisos de:
   - ✅ Leer mensajes / Ver historial
   - ✅ Enviar mensajes
   - ✅ Enviar multimedia (videos)
3. **Publica un video de prueba** en el canal con una descripción
4. **Obtén el STORAGE_ID** de la misma forma que el paso 1.3:
   - El bot ya debería estar como admin
   - Abre: `https://api.telegram.org/bot8352053218:AAGNe-yZ-_nXTEFFuSulfUJ5MUGPOPzwIaY/getUpdates`
   - Busca el nuevo `"chat":{"id":-100XXXXXXXXXX` del canal de almacén
   - Cópialo completo

---

### Fase 2: Preparar el Entorno de Desarrollo

#### 2.1 Instalar Python
```bash
# Verificar instalación
python --version  # Debe ser 3.9 o superior

# Si no está instalado, descarga desde python.org
```

#### 2.2 Crear Estructura del Proyecto
```bash
mkdir bot_telegram_videos
cd bot_telegram_videos

# Crear estructura de carpetas
mkdir config database handlers utils
```

Estructura final:
```
bot_telegram_videos/
│
├── .env                    # Variables de entorno
├── .gitignore             # Ignorar archivos sensibles
├── requirements.txt       # Dependencias
├── main.py               # Archivo principal
├── README.md             # Documentación
│
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuración global
│
├── database/
│   ├── __init__.py
│   ├── models.py         # Modelos de BD
│   └── db_manager.py     # Gestión de BD
│
├── handlers/
│   ├── __init__.py
│   ├── start.py          # Handler /start
│   ├── search.py         # Handler búsqueda
│   ├── callback.py       # Handlers de botones
│   └── admin.py          # Handlers admin
│
└── utils/
    ├── __init__.py
    ├── verification.py   # Verificación de canal
    ├── search_engine.py  # Motor de búsqueda
    └── helpers.py        # Funciones auxiliares
```

#### 2.3 Crear Entorno Virtual
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Si hay error de permisos:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2.4 Instalar Dependencias
Crear `requirements.txt`:
```
python-telegram-bot[job-queue]==20.7
python-dotenv==1.0.0
sqlalchemy==2.0.23
aiosqlite==0.19.0
```

Instalar:
```bash
pip install -r requirements.txt
```

---

### Fase 3: Configuración Básica

#### 3.1 Crear archivo `.env`
```env
# Bot Token de BotFather
BOT_TOKEN=8352053218:AAGNe-yZ-_nXTEFFuSulfUJ5MUGPOPzwIaY

# ID del canal de verificación (incluye el -)
VERIFICATION_CHANNEL_ID=-1003216346183
VERIFICATION_CHANNEL_USERNAME=@CineStellar_S

# ID del grupo/canal de almacén
STORAGE_CHANNEL_ID=-1003371387168

# Base de datos
DATABASE_URL=sqlite+aiosqlite:///bot_database.db

# Admin IDs (tu ID personal)
ADMIN_IDS=7830343272
```

#### 3.2 Crear `.gitignore`
```
venv/
.env
*.db
__pycache__/
*.pyc
.vscode/
.idea/
```

---

### Fase 4: Desarrollo del Bot

#### 4.1 Archivo `config/settings.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
VERIFICATION_CHANNEL_ID = int(os.getenv('VERIFICATION_CHANNEL_ID'))
VERIFICATION_CHANNEL_USERNAME = os.getenv('VERIFICATION_CHANNEL_USERNAME')
STORAGE_CHANNEL_ID = int(os.getenv('STORAGE_CHANNEL_ID'))
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
```

#### 4.2 Base de Datos `database/models.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    verified = Column(Boolean, default=False)
    joined_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, onupdate=func.now())

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(String(200), unique=True, nullable=False)
    message_id = Column(BigInteger)
    title = Column(String(500))
    description = Column(Text)
    tags = Column(String(500))  # separados por coma
    file_size = Column(BigInteger)
    duration = Column(Integer)
    added_at = Column(DateTime, server_default=func.now())

class Search(Base):
    __tablename__ = 'searches'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    query = Column(String(200))
    results_count = Column(Integer)
    searched_at = Column(DateTime, server_default=func.now())

class Favorite(Base):
    __tablename__ = 'favorites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    video_id = Column(Integer, nullable=False)
    added_at = Column(DateTime, server_default=func.now())
```

#### 4.3 Gestor de BD `database/db_manager.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_
from .models import Base, User, Video, Search, Favorite
from config.settings import DATABASE_URL

class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def add_user(self, user_id, username, first_name):
        async with self.async_session() as session:
            user = User(user_id=user_id, username=username, first_name=first_name)
            session.add(user)
            await session.commit()
    
    async def get_user(self, user_id):
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def update_user_verification(self, user_id, verified):
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.verified = verified
                await session.commit()
    
    async def add_video(self, file_id, message_id, title, description="", tags=""):
        async with self.async_session() as session:
            video = Video(
                file_id=file_id,
                message_id=message_id,
                title=title,
                description=description,
                tags=tags
            )
            session.add(video)
            await session.commit()
    
    async def search_videos(self, query, limit=10):
        async with self.async_session() as session:
            search_term = f"%{query}%"
            result = await session.execute(
                select(Video).where(
                    or_(
                        Video.title.ilike(search_term),
                        Video.description.ilike(search_term),
                        Video.tags.ilike(search_term)
                    )
                ).limit(limit)
            )
            return result.scalars().all()
    
    async def get_video_by_id(self, video_id):
        async with self.async_session() as session:
            result = await session.execute(
                select(Video).where(Video.id == video_id)
            )
            return result.scalar_one_or_none()
    
    async def log_search(self, user_id, query, results_count):
        async with self.async_session() as session:
            search = Search(user_id=user_id, query=query, results_count=results_count)
            session.add(search)
            await session.commit()
```

#### 4.4 Utilidad de Verificación `utils/verification.py`
```python
from telegram import ChatMember
from telegram.ext import ContextTypes
from config.settings import VERIFICATION_CHANNEL_ID

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Verifica si el usuario es miembro del canal"""
    try:
        member = await context.bot.get_chat_member(
            chat_id=VERIFICATION_CHANNEL_ID,
            user_id=user_id
        )
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        ]
    except Exception as e:
        print(f"Error verificando membresía: {e}")
        return False
```

#### 4.5 Handler Start `handlers/start.py`
```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.verification import is_user_member
from config.settings import VERIFICATION_CHANNEL_USERNAME

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    # Registrar o actualizar usuario
    db_user = await db.get_user(user.id)
    if not db_user:
        await db.add_user(user.id, user.username, user.first_name)
    
    # Verificar membresía
    is_member = await is_user_member(user.id, context)
    
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("✅ Unirse al Canal", url=f"https://t.me/{VERIFICATION_CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("🔄 Verificar Membresía", callback_data="verify_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 ¡Hola {user.first_name}!\n\n"
            f"Para usar este bot, debes unirte a nuestro canal oficial:\n"
            f"{VERIFICATION_CHANNEL_USERNAME}\n\n"
            f"Una vez que te hayas unido, presiona el botón de verificación.",
            reply_markup=reply_markup
        )
    else:
        await db.update_user_verification(user.id, True)
        await update.message.reply_text(
            f"✅ ¡Bienvenido {user.first_name}!\n\n"
            f"Ya estás verificado. Puedes comenzar a buscar videos.\n\n"
            f"📝 Comandos disponibles:\n"
            f"/buscar <término> - Buscar videos\n"
            f"/search <término> - Search videos\n"
            f"/help - Ver ayuda completa"
        )

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    db = context.bot_data['db']
    
    is_member = await is_user_member(user.id, context)
    
    if is_member:
        await db.update_user_verification(user.id, True)
        await query.edit_message_text(
            f"✅ ¡Verificación exitosa!\n\n"
            f"Ahora puedes usar el bot para buscar videos.\n\n"
            f"Usa /buscar <término> para comenzar."
        )
    else:
        await query.edit_message_text(
            f"❌ Aún no eres miembro del canal.\n\n"
            f"Por favor únete primero y luego presiona verificar nuevamente.",
            reply_markup=query.message.reply_markup
        )
```

#### 4.6 Handler de Búsqueda `handlers/search.py`
```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.verification import is_user_member

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    # Verificar membresía
    if not await is_user_member(user.id, context):
        await update.message.reply_text(
            "❌ Debes estar verificado para usar este comando.\n"
            "Usa /start para verificarte."
        )
        return
    
    # Obtener término de búsqueda
    if not context.args:
        await update.message.reply_text(
            "❓ Uso: /buscar <término de búsqueda>\n"
            "Ejemplo: /buscar tutorial python"
        )
        return
    
    query = " ".join(context.args)
    
    # Buscar en la base de datos
    videos = await db.search_videos(query)
    
    if not videos:
        await update.message.reply_text(
            f"😔 No se encontraron resultados para: '{query}'\n\n"
            f"Intenta con otros términos de búsqueda."
        )
        return
    
    # Registrar búsqueda
    await db.log_search(user.id, query, len(videos))
    
    # Crear botones con resultados
    keyboard = []
    text = f"🔍 Resultados para: *{query}*\n\n"
    
    for idx, video in enumerate(videos, 1):
        text += f"{idx}. {video.title}\n"
        keyboard.append([
            InlineKeyboardButton(
                f"📹 {idx}. {video.title[:50]}...",
                callback_data=f"video_{video.id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Obtener ID del video
    video_id = int(query.data.split('_')[1])
    db = context.bot_data['db']
    
    video = await db.get_video_by_id(video_id)
    
    if not video:
        await query.edit_message_text("❌ Video no encontrado.")
        return
    
    # Enviar video al usuario
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=f"📹 *{video.title}*\n\n{video.description}",
        parse_mode='Markdown'
    )
    
    # Reenviar video desde el canal de almacenamiento
    from config.settings import STORAGE_CHANNEL_ID
    await context.bot.forward_message(
        chat_id=query.from_user.id,
        from_chat_id=STORAGE_CHANNEL_ID,
        message_id=video.message_id
    )
    
    await query.edit_message_text(
        f"✅ Video enviado: {video.title}\n\n"
        f"Usa /buscar para encontrar más videos."
    )
```

#### 4.7 Archivo Principal `main.py`
```python
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from config.settings import BOT_TOKEN
from database.db_manager import DatabaseManager
from handlers.start import start_command, verify_callback
from handlers.search import search_command, video_callback

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def help_command(update, context):
    help_text = """
📚 *Ayuda del Bot*

*Comandos disponibles:*
/start - Iniciar y verificar membresía
/buscar <término> - Buscar videos
/search <término> - Search videos (English)
/help - Mostrar esta ayuda

*Cómo usar:*
1. Únete al canal de verificación
2. Verifica tu membresía
3. Usa /buscar seguido del término que buscas
4. Selecciona el video de los resultados

*Ejemplos:*
/buscar tutorial python
/search how to code
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def post_init(application):
    """Inicializar base de datos"""
    db = DatabaseManager()
    await db.init_db()
    application.bot_data['db'] = db
    logger.info("Base de datos inicializada")

def main():
    """Iniciar el bot"""
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Handlers de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler(["buscar", "search"], search_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handlers de callbacks
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_membership$"))
    application.add_handler(CallbackQueryHandler(video_callback, pattern="^video_"))
    
    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```

---

### Fase 5: Indexar Videos

#### Script para Indexar Videos `index_videos.py`
```python
import asyncio
from telegram import Bot
from database.db_manager import DatabaseManager
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

async def index_channel_videos():
    bot = Bot(token=BOT_TOKEN)
    db = DatabaseManager()
    await db.init_db()
    
    print("Iniciando indexación de videos...")
    
    # Obtener mensajes del canal (últimos 100)
    offset = 0
    indexed = 0
    
    # Nota: Telegram limita a obtener mensajes de uno en uno
    # Para indexación masiva, necesitarás iterar
    for msg_id in range(1, 1000):  # Ajusta el rango según necesites
        try:
            message = await bot.forward_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=msg_id
            )
            
            if message.video:
                title = message.caption or f"Video {msg_id}"
                await db.add_video(
                    file_id=message.video.file_id,
                    message_id=msg_id,
                    title=title,
                    description="",
                    tags=""
                )
                indexed += 1
                print(f"✅ Indexado: {title}")
        except Exception as e:
            continue
    
    print(f"\n✅ Indexación completa: {indexed} videos")

if __name__ == "__main__":
    asyncio.run(index_channel_videos())
```

---

### Fase 6: Ejecutar y Probar

#### 6.1 Ejecutar el Bot Localmente
```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar bot
python main.py
```

#### 6.2 Probar Funcionalidades
1. Abre Telegram y busca tu bot
2. Envía `/start`
3. Verifica la membresía del canal
4. Prueba comandos de búsqueda
5. Selecciona videos y verifica que se envíen

---

## 🚀 Despliegue en Producción

### Opción 1: VPS (Recomendado para producción)

```bash
# En el servidor
git clone <tu-repositorio>
cd bot_telegram_videos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env

# Ejecutar con screen o tmux
screen -S telegram_bot
python main.py
# Ctrl+A, D para detach
```

### Opción 2: Systemd Service (Linux)
Crear `/etc/systemd/system/telegram-bot.service`:
```ini
[Unit]
Description=Telegram Video Bot
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/ruta/al/bot
Environment="PATH=/ruta/al/bot/venv/bin"
ExecStart=/ruta/al/bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### Opción 3: Docker

`Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file:
      - .env
    volumes:
      - ./bot_database.db:/app/bot_database.db
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## 📊 Mejoras Adicionales

### 1. **Panel de Administración**
- Comando `/admin` para administradores
- Ver estadísticas globales
- Agregar/eliminar videos
- Broadcast de mensajes

### 2. **Sistema de Caché**
- Redis para cachear búsquedas frecuentes
- Reducir carga en la BD

### 3. **Búsqueda Avanzada**
- Filtros por duración, calidad, fecha
- Búsqueda por múltiples palabras (AND/OR)
- Búsqueda fuzzy (tolerancia a errores)

### 4. **Analytics**
- Videos más populares
- Términos de búsqueda trending
- Usuarios más activos

### 5. **Monetización (opcional)**
- Sistema de suscripción premium
- Acceso a contenido exclusivo
- Pagos con Telegram Stars

---

## 🔒 Seguridad y Consideraciones

### Importantes:
1. **Nunca subas el `.env` a GitHub**
2. **Usa HTTPS para webhooks en producción**
3. **Implementa rate limiting** para evitar spam
4. **Backups automáticos de la BD**
5. **Logs de errores y monitoreo**
6. **Cumple con términos de servicio de Telegram**
7. **Respeta derechos de autor del contenido**

### Rate Limiting (Opcional)
```python
from telegram.ext import MessageHandler, filters
from datetime import datetime, timedelta

user_last_request = {}

async def rate_limit_middleware(update, context):
    user_id = update.effective_user.id
    now = datetime.now()
    
    if user_id in user_last_request:
        if now - user_last_request[user_id] < timedelta(seconds=3):
            await update.message.reply_text("⏳ Por favor espera unos segundos.")
            return
    
    user_last_request[user_id] = now
    # Continuar con el handler normal
```

---

## 📚 Recursos Adicionales

### Documentación:
- [python-telegram-bot docs](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [SQLAlchemy docs](https://docs.sqlalchemy.org/)

### Comunidades:
- [python-telegram-bot GitHub](https://github.com/python-telegram-bot/python-telegram-bot)
- [Telegram Bot Developers](https://t.me/BotDevelopers)

---

## ✅ Checklist de Lanzamiento

- [ ] Bot creado en BotFather
- [ ] Canal de verificación configurado
- [ ] Grupo/canal de almacén configurado
- [ ] Bot agregado como admin al canal de almacén
- [ ] Código implementado y probado localmente
- [ ] Base de datos inicializada
- [ ] Videos indexados
- [ ] Archivo .env configurado correctamente
- [ ] .gitignore creado
- [ ] Bot desplegado en servidor
- [ ] Pruebas completas realizadas
- [ ] Monitoreo configurado
- [ ] Backup automático configurado

---

## 🐛 Solución de Problemas Comunes

### Error: "Unauthorized"
- Verifica que el TOKEN esté correcto en `.env`
- Asegúrate de que el bot no esté bloqueado

### Error: "Chat not found"
- Verifica que los IDs de canal sean correctos
- Asegúrate de que el bot esté en el grupo/canal

### No encuentra videos
- Ejecuta `index_videos.py` para indexar
- Verifica que los videos tengan captions/títulos

### Bot no responde
- Revisa los logs para errores
- Verifica conexión a internet del servidor
- Comprueba que el proceso esté corriendo

---

**¡Tu bot está listo para desplegarse! 🚀**

Para cualquier pregunta adicional, revisa la documentación oficial o las comunidades de Telegram Bots.
