from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, func, update
from .models import Base, User, Video, Search, Favorite, AdToken, BotConfig, TvShow, Episode, UserNavigationState
from config.settings import DATABASE_URL
import unicodedata
import secrets
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

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
            # Primero, invalidar tokens previos del mismo user_id + video_id que no estén completados
            # Esto evita acumulación de tokens no usados
            await session.execute(
                update(AdToken)
                .where(AdToken.user_id == user_id)
                .where(AdToken.video_id == video_id)
                .where(AdToken.completed == False)
                .values(completed=True, completed_at=datetime.utcnow())
            )
            await session.commit()
            
            # Crear nuevo token
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
            
            print(f"🔑 Nuevo token creado: {token[:10]}... para user_id={user_id}, video_id={video_id}")
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
    
    async def has_valid_token(self, user_id, content_id):
        """
        Verifica si el usuario tiene un token válido (completado) para este contenido
        content_id puede ser video_id o episode_id
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(AdToken)
                .where(AdToken.user_id == user_id)
                .where(AdToken.video_id == content_id)
                .where(AdToken.completed == True)
            )
            token = result.scalar_one_or_none()
            return token is not None
    
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
    
    async def update_video(self, message_id, **kwargs):
        """Actualiza un video existente por su message_id"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Video).where(Video.message_id == message_id)
                )
                video = result.scalar_one_or_none()
                
                if not video:
                    print(f"⚠️ Video con message_id={message_id} no encontrado para actualizar")
                    return False
                
                # Actualizar solo los campos proporcionados
                for key, value in kwargs.items():
                    if hasattr(video, key):
                        # Truncar strings largos
                        if isinstance(value, str) and len(value) > 500:
                            value = value[:500]
                        setattr(video, key, value)
                
                await session.commit()
                print(f"✅ Video {message_id} actualizado: {video.title}")
                return True
                
        except Exception as e:
            print(f"❌ Error al actualizar video {message_id}: {e}")
            return False
    
    async def get_config(self, key, default=None):
        """Obtiene un valor de configuración de la base de datos"""
        async with self.async_session() as session:
            result = await session.execute(
                select(BotConfig).where(BotConfig.key == key)
            )
            config = result.scalar_one_or_none()
            return config.value if config else default
    
    async def set_config(self, key, value):
        """Guarda o actualiza un valor de configuración en la base de datos"""
        async with self.async_session() as session:
            result = await session.execute(
                select(BotConfig).where(BotConfig.key == key)
            )
            config = result.scalar_one_or_none()
            
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                config = BotConfig(key=key, value=str(value))
                session.add(config)
            
            await session.commit()
            return True
    
    # ==================== MÉTODOS PARA SERIES ====================
    
    async def add_tv_show(self, name, tmdb_id=None, original_name=None, year=None, 
                         overview=None, poster_url=None, backdrop_url=None, 
                         vote_average=None, genres=None, number_of_seasons=None, status=None):
        """Agrega una nueva serie a la base de datos"""
        async with self.async_session() as session:
            try:
                show = TvShow(
                    name=name,
                    tmdb_id=tmdb_id,
                    original_name=original_name,
                    year=year,
                    overview=overview,
                    poster_url=poster_url,
                    backdrop_url=backdrop_url,
                    vote_average=vote_average,
                    genres=genres,
                    number_of_seasons=number_of_seasons,
                    status=status
                )
                session.add(show)
                await session.commit()
                await session.refresh(show)
                return show
            except Exception as e:
                logger.error(f"Error al agregar serie: {e}", exc_info=True)
                await session.rollback()
                return None
    
    async def get_tv_show_by_id(self, show_id):
        """Obtiene una serie por su ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(TvShow).where(TvShow.id == show_id)
            )
            return result.scalar_one_or_none()
    
    async def get_tv_show_by_tmdb_id(self, tmdb_id):
        """Obtiene una serie por su TMDB ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(TvShow).where(TvShow.tmdb_id == tmdb_id)
            )
            return result.scalar_one_or_none()
    
    async def search_tv_shows(self, query, limit=10):
        """Busca series por nombre"""
        async with self.async_session() as session:
            if not query or query.strip() == "":
                result = await session.execute(
                    select(TvShow).order_by(TvShow.added_at.desc()).limit(limit)
                )
                return result.scalars().all()
            
            normalized_query = self.normalize_text(query)
            search_terms = normalized_query.split()
            
            result = await session.execute(
                select(TvShow).order_by(TvShow.added_at.desc()).limit(500)
            )
            all_shows = result.scalars().all()
            
            matching_shows = []
            for show in all_shows:
                norm_name = self.normalize_text(show.name or "")
                norm_original = self.normalize_text(show.original_name or "")
                
                score = 0
                
                if normalized_query in norm_name:
                    score += 10
                if normalized_query in norm_original:
                    score += 8
                
                for term in search_terms:
                    if term in norm_name:
                        score += 3
                    if term in norm_original:
                        score += 2
                
                if score > 0:
                    matching_shows.append((score, show))
            
            matching_shows.sort(key=lambda x: x[0], reverse=True)
            return [show for score, show in matching_shows[:limit]]
    
    async def add_episode(self, tv_show_id, file_id, message_id, season_number, 
                         episode_number, title=None, overview=None, air_date=None, 
                         runtime=None, still_path=None, channel_message_id=None):
        """Agrega un nuevo episodio a la base de datos"""
        async with self.async_session() as session:
            try:
                episode = Episode(
                    tv_show_id=tv_show_id,
                    file_id=file_id,
                    message_id=message_id,
                    season_number=season_number,
                    episode_number=episode_number,
                    title=title,
                    overview=overview,
                    air_date=air_date,
                    runtime=runtime,
                    still_path=still_path,
                    channel_message_id=channel_message_id
                )
                session.add(episode)
                await session.commit()
                await session.refresh(episode)
                return episode
            except Exception as e:
                print(f"❌ Error al agregar episodio: {e}")
                await session.rollback()
                return None
    
    async def get_episode_by_id(self, episode_id):
        """Obtiene un episodio por su ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Episode).where(Episode.id == episode_id)
            )
            return result.scalar_one_or_none()
    
    async def get_episode(self, tv_show_id, season_number, episode_number):
        """Obtiene un episodio específico"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Episode).where(
                    Episode.tv_show_id == tv_show_id,
                    Episode.season_number == season_number,
                    Episode.episode_number == episode_number
                )
            )
            return result.scalar_one_or_none()
    
    async def get_episode_by_message_id(self, message_id):
        """Obtiene un episodio por su message_id"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Episode).where(Episode.message_id == message_id)
            )
            return result.scalar_one_or_none()
    
    async def get_episodes_by_show(self, tv_show_id):
        """Obtiene todos los episodios de una serie"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Episode)
                .where(Episode.tv_show_id == tv_show_id)
                .order_by(Episode.season_number, Episode.episode_number)
            )
            return result.scalars().all()
    
    async def get_episodes_by_season(self, tv_show_id, season_number):
        """Obtiene todos los episodios de una temporada"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Episode)
                .where(
                    Episode.tv_show_id == tv_show_id,
                    Episode.season_number == season_number
                )
                .order_by(Episode.episode_number)
            )
            return result.scalars().all()
    
    async def get_seasons_for_show(self, tv_show_id):
        """Obtiene lista de temporadas disponibles con conteo de episodios"""
        async with self.async_session() as session:
            result = await session.execute(
                select(
                    Episode.season_number,
                    func.count(Episode.id).label('episode_count')
                )
                .where(Episode.tv_show_id == tv_show_id)
                .group_by(Episode.season_number)
                .order_by(Episode.season_number)
            )
            return result.all()
    
    # ==================== MÉTODOS PARA NAVEGACIÓN ====================
    
    async def set_user_state(self, user_id, menu, show_id=None):
        """Guarda el estado de navegación del usuario"""
        async with self.async_session() as session:
            # Use merge to handle both insert and update
            state = UserNavigationState(
                user_id=user_id,
                current_menu=menu,
                selected_show_id=show_id,
                last_interaction=datetime.utcnow()
            )
            await session.merge(state)
            await session.commit()
            return True
    
    async def get_user_state(self, user_id):
        """Obtiene el estado de navegación del usuario"""
        async with self.async_session() as session:
            result = await session.execute(
                select(UserNavigationState).where(UserNavigationState.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def clear_user_state(self, user_id):
        """Limpia el estado de navegación del usuario"""
        async with self.async_session() as session:
            result = await session.execute(
                select(UserNavigationState).where(UserNavigationState.user_id == user_id)
            )
            state = result.scalar_one_or_none()
            if state:
                await session.delete(state)
                await session.commit()
            return True
