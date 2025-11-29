from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, func
from .models import Base, User, Video, Search, Favorite, AdToken
from config.settings import DATABASE_URL
import unicodedata
import secrets
from datetime import datetime

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
    
    async def add_video(self, file_id, message_id, title, description="", tags="", 
                       tmdb_id=None, original_title=None, year=None, overview=None,
                       poster_url=None, backdrop_url=None, vote_average=None, 
                       runtime=None, genres=None, channel_message_id=None):
        async with self.async_session() as session:
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
            # Normalizar la búsqueda
            normalized_query = self.normalize_text(query)
            search_term = f"%{normalized_query}%"
            
            # Buscar en todos los videos
            result = await session.execute(select(Video))
            all_videos = result.scalars().all()
            
            # Filtrar manualmente con normalización
            matching_videos = []
            for video in all_videos:
                # Normalizar título, descripción y tags
                norm_title = self.normalize_text(video.title)
                norm_desc = self.normalize_text(video.description)
                norm_tags = self.normalize_text(video.tags)
                
                # Verificar si la query está en alguno de los campos
                if (normalized_query in norm_title or 
                    normalized_query in norm_desc or 
                    normalized_query in norm_tags):
                    matching_videos.append(video)
                    
                    if len(matching_videos) >= limit:
                        break
            
            return matching_videos
    
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
        async with self.async_session() as session:
            token = secrets.token_urlsafe(32)
            ad_token = AdToken(
                token=token,
                user_id=user_id,
                video_id=video_id,
                message_id=message_id
            )
            session.add(ad_token)
            await session.commit()
            return token
    
    async def get_ad_token(self, token):
        """Obtiene información del token de anuncio"""
        async with self.async_session() as session:
            result = await session.execute(
                select(AdToken).where(AdToken.token == token)
            )
            return result.scalar_one_or_none()
    
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
        """Obtiene video por message_id del canal de almacenamiento"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Video).where(Video.message_id == message_id)
            )
            return result.scalar_one_or_none()
