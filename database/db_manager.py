from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, func, update
from .models import (
    Base, User, Video, Search, Favorite, AdToken, BotConfig, 
    TvShow, Episode, UserNavigationState,
    UserTicket, TicketTransaction, Referral, UserActivity,
    ChannelSource, ChannelVisit
)
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
    
    async def get_all_users(self):
        """Obtiene todos los usuarios registrados"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).order_by(User.joined_at.desc())
            )
            return result.scalars().all()
    
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
            
            # Filtrar palabras muy cortas (stopwords)
            stopwords = {'de', 'la', 'el', 'y', 'en', 'a', 'los', 'las', 'un', 'una', 'del', 'al'}
            search_terms = [term for term in normalized_query.split() if len(term) >= 3 and term not in stopwords]
            
            # Si no hay términos válidos después de filtrar, usar la query completa
            if not search_terms:
                search_terms = normalized_query.split()
            
            # Buscar solo primeros 1000 videos (aumentado para mejor cobertura)
            result = await session.execute(
                select(Video).order_by(Video.added_at.desc()).limit(1000)
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
                matches = 0  # Contador de términos que coinciden
                
                # Búsqueda exacta completa en título (máxima prioridad)
                if normalized_query in norm_title:
                    score += 100
                    matches = len(search_terms)
                
                # Búsqueda exacta en título original
                if normalized_query in norm_original:
                    score += 80
                    matches = len(search_terms)
                
                # Términos individuales en título (solo si coinciden)
                for term in search_terms:
                    if len(term) >= 3:  # Solo términos de 3+ caracteres
                        if term in norm_title:
                            score += 10
                            matches += 1
                        if term in norm_original:
                            score += 8
                            matches += 1
                
                # Bonus si coinciden todos los términos en el título
                if matches >= len(search_terms) and len(search_terms) > 1:
                    score += 50
                
                # Solo agregar si tiene score significativo y al menos 1 coincidencia
                if score > 0 and matches > 0:
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
    
    async def get_all_videos(self, limit=500):
        """Obtiene todas las películas para el catálogo de la Mini App"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Video).order_by(Video.id.desc()).limit(limit)
            )
            return result.scalars().all()
    
    async def log_search(self, user_id, query, results_count, metadata=None):
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
    
    async def update_video_title(self, message_id, new_title):
        """Actualiza solo el título de un video"""
        return await self.update_video(message_id, title=new_title)
    
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
            
            # Filtrar palabras muy cortas (stopwords)
            stopwords = {'de', 'la', 'el', 'y', 'en', 'a', 'los', 'las', 'un', 'una', 'del', 'al'}
            search_terms = [term for term in normalized_query.split() if len(term) >= 3 and term not in stopwords]
            
            if not search_terms:
                search_terms = normalized_query.split()
            
            result = await session.execute(
                select(TvShow).order_by(TvShow.added_at.desc()).limit(1000)
            )
            all_shows = result.scalars().all()
            
            matching_shows = []
            for show in all_shows:
                norm_name = self.normalize_text(show.name or "")
                norm_original = self.normalize_text(show.original_name or "")
                
                score = 0
                matches = 0
                
                # Búsqueda exacta completa
                if normalized_query in norm_name:
                    score += 100
                    matches = len(search_terms)
                if normalized_query in norm_original:
                    score += 80
                    matches = len(search_terms)
                
                # Términos individuales
                for term in search_terms:
                    if len(term) >= 3:
                        if term in norm_name:
                            score += 10
                            matches += 1
                        if term in norm_original:
                            score += 8
                            matches += 1
                
                # Bonus por todos los términos
                if matches >= len(search_terms) and len(search_terms) > 1:
                    score += 50
                
                # Solo agregar si tiene score y coincidencias
                if score > 0 and matches > 0:
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

    # ============ SISTEMA DE TICKETS ============
    
    async def get_user_tickets(self, user_id):
        """Obtiene los tickets de un usuario"""
        async with self.async_session() as session:
            result = await session.execute(
                select(UserTicket).where(UserTicket.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def create_user_tickets(self, user_id):
        """Crea registro de tickets para un usuario nuevo"""
        async with self.async_session() as session:
            user_ticket = UserTicket(user_id=user_id, tickets=0)
            session.add(user_ticket)
            await session.commit()
            return user_ticket
    
    async def add_tickets(self, user_id, amount, reason, description=None, reference_id=None):
        """Agrega tickets a un usuario y registra la transacción"""
        async with self.async_session() as session:
            # Obtener o crear registro de tickets
            result = await session.execute(
                select(UserTicket).where(UserTicket.user_id == user_id)
            )
            user_ticket = result.scalar_one_or_none()
            
            if not user_ticket:
                user_ticket = UserTicket(user_id=user_id, tickets=0, tickets_earned=0, tickets_used=0)
                session.add(user_ticket)
            
            # Actualizar tickets
            user_ticket.tickets += amount
            user_ticket.tickets_earned += amount
            
            # Registrar transacción
            transaction = TicketTransaction(
                user_id=user_id,
                amount=amount,
                reason=reason,
                description=description,
                reference_id=reference_id
            )
            session.add(transaction)
            
            await session.commit()
            return user_ticket.tickets
    
    async def use_ticket(self, user_id, content_id, content_type='movie'):
        """Usa un ticket para ver contenido sin anuncios"""
        async with self.async_session() as session:
            result = await session.execute(
                select(UserTicket).where(UserTicket.user_id == user_id)
            )
            user_ticket = result.scalar_one_or_none()
            
            if not user_ticket or user_ticket.tickets <= 0:
                return False
            
            # Descontar ticket
            user_ticket.tickets -= 1
            user_ticket.tickets_used += 1
            
            # Registrar transacción
            transaction = TicketTransaction(
                user_id=user_id,
                amount=-1,
                reason='used',
                description=f'Usado para ver {content_type}',
                reference_id=content_id
            )
            session.add(transaction)
            
            # Registrar actividad
            activity = UserActivity(
                user_id=user_id,
                action_type=f'watch_{content_type}',
                content_id=content_id,
                content_type=content_type,
                used_ticket=True
            )
            session.add(activity)
            
            await session.commit()
            return True
    
    async def get_ticket_transactions(self, user_id, limit=20):
        """Obtiene historial de transacciones de tickets"""
        async with self.async_session() as session:
            result = await session.execute(
                select(TicketTransaction)
                .where(TicketTransaction.user_id == user_id)
                .order_by(TicketTransaction.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    # ============ SISTEMA DE REFERIDOS ============
    
    async def create_referral(self, referrer_id, referred_id):
        """Crea un nuevo referido pendiente"""
        async with self.async_session() as session:
            # Verificar que no exista ya
            result = await session.execute(
                select(Referral).where(Referral.referred_id == referred_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return None  # Ya fue referido por alguien
            
            referral = Referral(
                referrer_id=referrer_id,
                referred_id=referred_id,
                status='pending'
            )
            session.add(referral)
            await session.commit()
            return referral
    
    async def get_referral_by_referred(self, referred_id):
        """Obtiene el referido por el ID del usuario referido"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Referral).where(Referral.referred_id == referred_id)
            )
            return result.scalar_one_or_none()
    
    async def verify_referral(self, referred_id):
        """Verifica un referido cuando se une al canal"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Referral).where(
                    Referral.referred_id == referred_id,
                    Referral.status == 'pending'
                )
            )
            referral = result.scalar_one_or_none()
            
            if not referral:
                return None
            
            referral.status = 'verified'
            referral.verified_at = datetime.now(timezone.utc)
            await session.commit()
            return referral
    
    async def reward_referral(self, referred_id, tickets_reward=5):
        """Recompensa al referrer cuando el referido se verifica"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Referral).where(
                    Referral.referred_id == referred_id,
                    Referral.status == 'verified'
                )
            )
            referral = result.scalar_one_or_none()
            
            if not referral:
                return None
            
            # Marcar como recompensado
            referral.status = 'rewarded'
            referral.rewarded_at = datetime.now(timezone.utc)
            await session.commit()
            
            # Dar tickets al referrer
            tickets = await self.add_tickets(
                user_id=referral.referrer_id,
                amount=tickets_reward,
                reason='referral',
                description=f'Referido verificado: {referred_id}',
                reference_id=referred_id
            )
            
            return referral.referrer_id, tickets
    
    async def get_user_referrals(self, referrer_id):
        """Obtiene todos los referidos de un usuario"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Referral)
                .where(Referral.referrer_id == referrer_id)
                .order_by(Referral.referred_at.desc())
            )
            return result.scalars().all()
    
    async def get_referral_stats(self, referrer_id):
        """Obtiene estadísticas de referidos de un usuario"""
        async with self.async_session() as session:
            # Total referidos
            total = await session.execute(
                select(func.count(Referral.id))
                .where(Referral.referrer_id == referrer_id)
            )
            total_count = total.scalar()
            
            # Verificados
            verified = await session.execute(
                select(func.count(Referral.id))
                .where(
                    Referral.referrer_id == referrer_id,
                    Referral.status.in_(['verified', 'rewarded'])
                )
            )
            verified_count = verified.scalar()
            
            # Pendientes
            pending = await session.execute(
                select(func.count(Referral.id))
                .where(
                    Referral.referrer_id == referrer_id,
                    Referral.status == 'pending'
                )
            )
            pending_count = pending.scalar()
            
            return {
                'total': total_count,
                'verified': verified_count,
                'pending': pending_count
            }

    # ============ ACTIVIDAD DE USUARIO ============
    
    async def log_activity(self, user_id, action_type, content_id=None, content_type=None, used_ticket=False):
        """Registra una actividad del usuario"""
        async with self.async_session() as session:
            activity = UserActivity(
                user_id=user_id,
                action_type=action_type,
                content_id=content_id,
                content_type=content_type,
                used_ticket=used_ticket
            )
            session.add(activity)
            await session.commit()
            return activity
    
    async def get_user_watch_history(self, user_id, limit=20):
        """Obtiene historial de videos vistos por el usuario"""
        async with self.async_session() as session:
            result = await session.execute(
                select(UserActivity)
                .where(
                    UserActivity.user_id == user_id,
                    UserActivity.action_type.in_(['watch_movie', 'watch_episode'])
                )
                .order_by(UserActivity.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    # ============ ESTADÍSTICAS ADMIN ============
    
    async def get_global_stats(self):
        """Obtiene estadísticas globales para el dashboard admin"""
        async with self.async_session() as session:
            # Total usuarios
            total_users = await session.execute(select(func.count(User.id)))
            
            # Usuarios verificados
            verified_users = await session.execute(
                select(func.count(User.id)).where(User.verified == True)
            )
            
            # Total videos indexados
            total_videos = await session.execute(select(func.count(Video.id)))
            
            # Total series
            total_series = await session.execute(select(func.count(TvShow.id)))
            
            # Total episodios
            total_episodes = await session.execute(select(func.count(Episode.id)))
            
            # Total tickets en circulación
            total_tickets = await session.execute(
                select(func.sum(UserTicket.tickets))
            )
            
            # Total tickets usados
            tickets_used = await session.execute(
                select(func.sum(UserTicket.tickets_used))
            )
            
            # Total referidos
            total_referrals = await session.execute(select(func.count(Referral.id)))
            
            # Referidos verificados
            verified_referrals = await session.execute(
                select(func.count(Referral.id))
                .where(Referral.status.in_(['verified', 'rewarded']))
            )
            
            return {
                'total_users': total_users.scalar() or 0,
                'verified_users': verified_users.scalar() or 0,
                'total_videos': total_videos.scalar() or 0,
                'total_series': total_series.scalar() or 0,
                'total_episodes': total_episodes.scalar() or 0,
                'tickets_available': total_tickets.scalar() or 0,
                'tickets_used': tickets_used.scalar() or 0,
                'total_referrals': total_referrals.scalar() or 0,
                'verified_referrals': verified_referrals.scalar() or 0
            }

    # ======================
    # MÉTODOS CHANNEL STATS
    # ======================
    
    async def add_channel_source(self, channel_id: str, channel_name: str, channel_url: str = None, description: str = None):
        """Agregar nuevo canal para tracking"""
        try:
            async with self.async_session() as session:
                # Verificar si ya existe
                existing = await session.execute(
                    select(ChannelSource).where(ChannelSource.channel_id == channel_id)
                )
                if existing.scalar():
                    return False, "El canal ya existe"
                
                channel = ChannelSource(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    channel_url=channel_url,
                    description=description
                )
                session.add(channel)
                await session.commit()
                return True, "Canal agregado exitosamente"
        except Exception as e:
            logger.error(f"Error agregando canal: {e}")
            return False, f"Error: {e}"
    
    async def register_channel_visit(self, user_id: int, channel_id: str):
        """Registrar visita desde un canal específico"""
        try:
            async with self.async_session() as session:
                # Buscar el canal source
                channel_result = await session.execute(
                    select(ChannelSource).where(ChannelSource.channel_id == channel_id)
                )
                channel = channel_result.scalar()
                
                if not channel:
                    logger.warning(f"Canal {channel_id} no encontrado")
                    return False
                
                # Verificar si es usuario nuevo
                user_result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                is_new_user = user_result.scalar() is None
                
                # Registrar la visita
                visit = ChannelVisit(
                    user_id=user_id,
                    channel_source_id=channel.id,
                    is_new_user=is_new_user
                )
                session.add(visit)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error registrando visita: {e}")
            return False
    
    async def get_channel_stats_by_period(self, period: str = 'today'):
        """Obtener estadísticas de canales por período"""
        try:
            async with self.async_session() as session:
                from datetime import datetime, timedelta
                
                now = datetime.now(timezone.utc)
                
                if period == 'today':
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif period == 'week':
                    start_date = now - timedelta(days=7)
                elif period == 'month':
                    start_date = now - timedelta(days=30)
                else:  # 'total'
                    start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
                
                # Query para obtener stats por canal
                query = select(
                    ChannelSource.channel_id,
                    ChannelSource.channel_name,
                    ChannelSource.added_at,
                    func.count(ChannelVisit.id).label('total_visits'),
                    func.count(func.distinct(ChannelVisit.user_id)).label('unique_users'),
                    func.sum(func.cast(ChannelVisit.is_new_user, Integer)).label('new_users'),
                    func.max(ChannelVisit.visited_at).label('last_visit')
                ).select_from(
                    ChannelSource.__table__.join(
                        ChannelVisit.__table__, 
                        ChannelSource.id == ChannelVisit.channel_source_id,
                        isouter=True
                    )
                ).where(
                    ChannelSource.is_active == True
                ).where(
                    or_(
                        ChannelVisit.visited_at >= start_date,
                        ChannelVisit.visited_at.is_(None)
                    ) if period != 'total' else True
                ).group_by(
                    ChannelSource.id,
                    ChannelSource.channel_id,
                    ChannelSource.channel_name,
                    ChannelSource.added_at
                ).order_by(
                    func.count(func.distinct(ChannelVisit.user_id)).desc()
                )
                
                result = await session.execute(query)
                channels = result.fetchall()
                
                # Calcular totales
                total_users = sum(c.unique_users or 0 for c in channels)
                total_visits = sum(c.total_visits or 0 for c in channels)
                
                return {
                    'channels': [
                        {
                            'channel_id': c.channel_id,
                            'channel_name': c.channel_name,
                            'added_at': c.added_at,
                            'unique_users': c.unique_users or 0,
                            'total_visits': c.total_visits or 0,
                            'new_users': c.new_users or 0,
                            'last_visit': c.last_visit
                        } for c in channels
                    ],
                    'period': period,
                    'total_users': total_users,
                    'total_visits': total_visits,
                    'start_date': start_date,
                    'generated_at': now
                }
        except Exception as e:
            logger.error(f"Error obteniendo stats de canales: {e}")
            return {
                'channels': [],
                'period': period,
                'total_users': 0,
                'total_visits': 0,
                'error': str(e)
            }
    
    async def get_active_channel_sources(self):
        """Obtener lista de canales activos"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(ChannelSource)
                    .where(ChannelSource.is_active == True)
                    .order_by(ChannelSource.added_at.desc())
                )
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error obteniendo canales activos: {e}")
            return []
    
    async def deactivate_channel_source(self, channel_id: str):
        """Desactivar un canal source"""
        try:
            async with self.async_session() as session:
                await session.execute(
                    update(ChannelSource)
                    .where(ChannelSource.channel_id == channel_id)
                    .values(is_active=False)
                )
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error desactivando canal: {e}")
            return False
