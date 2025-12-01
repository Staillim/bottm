from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, func
from .models import Base, User, Video, Search, Favorite, AdToken
from config.settings import DATABASE_URL
import unicodedata
import secrets
import asyncio
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL no está configurada")
        
        # Configurar para PostgreSQL con pgbouncer
        connect_args = {}
        if DATABASE_URL.startswith("postgresql"):
            connect_args = {
                "statement_cache_size": 0,  # Deshabilitar cache de statements para pgbouncer
                "prepared_statement_cache_size": 0  # También deshabilitar prepared statements
            }
        
        self.engine = create_async_engine(
            DATABASE_URL, 
            echo=False,
            connect_args=connect_args,
            pool_pre_ping=True  # Verificar conexiones antes de usarlas
        )
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
    
    async def add_video(self, file_id, message_id, title, description="", tags="", 
                       tmdb_id=None, original_title=None, year=None, overview=None,
                       poster_url=None, backdrop_url=None, vote_average=None, 
                       runtime=None, genres=None, channel_message_id=None):
        try:
            async with self.async_session() as session:
                try:
                    # Verificar si el video ya existe
                    result = await session.execute(
                        select(Video).where(
                            (Video.file_id == file_id) | (Video.message_id == message_id)
                        )
                    )
                    existing_video = result.scalar_one_or_none()
                    if existing_video:
                        # Mostrar advertencia solo una vez por video duplicado
                        if not hasattr(self, '_duplicate_warnings'):
                            self._duplicate_warnings = set()
                        if file_id not in self._duplicate_warnings:
                            print(f"⚠️ Video duplicado: {file_id} o mensaje {message_id}")
                            self._duplicate_warnings.add(file_id)
                        return existing_video

                    # Truncar campos largos
                    title = title[:500] if title else None
                    description = description[:500] if description else None
                    tags = tags[:500] if tags else None
                    original_title = original_title[:500] if original_title else None
                    overview = overview[:500] if overview else None
                    poster_url = poster_url[:500] if poster_url else None
                    backdrop_url = backdrop_url[:500] if backdrop_url else None
                    genres = genres[:500] if genres else None

                    # Crear nuevo video
                    video = Video(
                        file_id=file_id,
                        message_id=message_id,
                        title=title,
                        description=description,
                        tags=tags,
                        tmdb_id=tmdb_id,
                        original_title=original_title,
                        year=year,
                        overview=overview,
                        poster_url=poster_url,
                        backdrop_url=backdrop_url,
                        vote_average=vote_average,
                        runtime=runtime,
                        genres=genres,
                        channel_message_id=channel_message_id
                    )
                    session.add(video)
                    await session.commit()
                    return video
                except Exception as e:
                    print(f"❌ Error al agregar video: {e}")
                    await session.rollback()
                    return None
        except asyncio.CancelledError:
            print(f"[CANCELLED] Operación cancelada al agregar video con file_id={file_id}")
            return None
        except Exception as e:
            print(f"[ERROR] Error de conexión al agregar video con file_id={file_id}: {e}")
            return None
    
    def normalize_text(self, text):
        """Normaliza texto: quita acentos, convierte a minúsculas"""
        if not text:
            return ""
        # Quitar acentos (á->a, é->e, etc.)
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text.lower()
    
    async def search_videos(self, query, limit=10):
        async with self.async_session() as session:
            if not query or query.strip() == "":
                # Sin query, retornar videos recientes
                result = await session.execute(
                    select(Video).order_by(Video.added_at.desc()).limit(limit)
                )
                return result.scalars().all()
            
            # Normalizar la búsqueda
            normalized_query = self.normalize_text(query)
            search_terms = normalized_query.split()  # Separar palabras para mejor búsqueda
            
            # Buscar solo primeros 500 videos (optimización)
            result = await session.execute(
                select(Video).order_by(Video.added_at.desc()).limit(500)
            )
            all_videos = result.scalars().all()
            
            # Filtrar y rankear resultados
            matching_videos = []
            for video in all_videos:
                # Normalizar campos
                norm_title = self.normalize_text(video.title or "")
                norm_desc = self.normalize_text(video.description or "")
                norm_tags = self.normalize_text(video.tags or "")
                norm_original = self.normalize_text(video.original_title or "")
                
                # Calcular score de relevancia
                score = 0
                
                # Búsqueda exacta en título vale más
                if normalized_query in norm_title:
                    score += 10
                
                # Título original también importante
                if normalized_query in norm_original:
                    score += 8
                    
                # Términos individuales en título
                for term in search_terms:
                    if term in norm_title:
                        score += 3
                    if term in norm_original:
                        score += 2
                    if term in norm_desc:
                        score += 1
                    if term in norm_tags:
                        score += 1
                
                if score > 0:
                    matching_videos.append((score, video))
            
            # Ordenar por score y retornar top resultados
            matching_videos.sort(reverse=True, key=lambda x: x[0])
            return [video for score, video in matching_videos[:limit]]
    
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
    
    async def create_ad_token(self, user_id, video_id, message_id=None):
        """Crea un token único para ver un anuncio antes de recibir el video"""
        from datetime import timedelta
        
        async with self.async_session() as session:
            token = secrets.token_urlsafe(32)
            
            # Token expira en 24 horas
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            ad_token = AdToken(
                token=token,
                user_id=user_id,
                video_id=video_id,
                message_id=message_id,
                expires_at=expires_at
            )
            session.add(ad_token)
            await session.commit()
            return token
    
    async def get_ad_token(self, token):
        """Obtiene información del token de anuncio si es válido y no expiró"""
        async with self.async_session() as session:
            result = await session.execute(
                select(AdToken).where(AdToken.token == token)
            )
            ad_token = result.scalar_one_or_none()
            
            # Verificar si el token expiró
            if ad_token and ad_token.expires_at:
                if datetime.utcnow() > ad_token.expires_at:
                    print(f"⚠️ Token expirado: {token[:10]}...")
                    return None
            
            return ad_token
    
    async def complete_ad_token(self, token):
        """Marca un token como completado cuando el usuario ve el anuncio"""
        async with self.async_session() as session:
            result = await session.execute(
                select(AdToken).where(AdToken.token == token)
            )
            ad_token = result.scalar_one_or_none()
            if ad_token and not ad_token.completed:
                ad_token.completed = True
                ad_token.completed_at = datetime.utcnow()
                await session.commit()
                return True
            return False
    
    async def get_video_by_message_id(self, message_id):
        """Verifica si un video ya existe en la base de datos por su message_id."""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Video).where(Video.message_id == message_id)
                )
                return result.scalar_one_or_none()
        except asyncio.CancelledError:
            print(f"[CANCELLED] Operación cancelada al buscar video con message_id={message_id}")
            return None
        except Exception as e:
            print(f"[ERROR] Error al buscar video con message_id={message_id}: {e}")
            return None
