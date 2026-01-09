from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger, ForeignKey, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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
    content_type = Column(String(20), default='movie')  # 'movie' o 'tv_episode'
    
    # Campos de TMDB
    tmdb_id = Column(Integer)
    original_title = Column(String(500))
    year = Column(String(10))
    overview = Column(Text)
    poster_url = Column(String(500))
    backdrop_url = Column(String(500))
    vote_average = Column(Integer)
    runtime = Column(Integer)
    genres = Column(String(500))  # separados por coma
    channel_message_id = Column(BigInteger)  # ID del mensaje publicado en canal verificación

class TvShow(Base):
    __tablename__ = 'tv_shows'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    tmdb_id = Column(Integer)
    original_name = Column(String(500))
    year = Column(Integer)
    overview = Column(Text)
    poster_url = Column(Text)
    backdrop_url = Column(Text)
    vote_average = Column(Float)
    genres = Column(Text)
    number_of_seasons = Column(Integer)
    status = Column(String(50))
    added_at = Column(DateTime, server_default=func.now())

class Episode(Base):
    __tablename__ = 'episodes'
    
    id = Column(Integer, primary_key=True)
    tv_show_id = Column(Integer, ForeignKey('tv_shows.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(String(200), nullable=False)
    message_id = Column(Integer, nullable=False)
    season_number = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    title = Column(String(500))
    overview = Column(Text)
    air_date = Column(Date)
    runtime = Column(Integer)
    still_path = Column(Text)
    channel_message_id = Column(Integer)
    added_at = Column(DateTime, server_default=func.now())

class UserNavigationState(Base):
    __tablename__ = 'user_navigation_state'
    
    user_id = Column(BigInteger, primary_key=True)
    current_menu = Column(String(50))
    selected_show_id = Column(Integer, ForeignKey('tv_shows.id', ondelete='SET NULL'))
    last_interaction = Column(DateTime, server_default=func.now())

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

class AdToken(Base):
    __tablename__ = 'ad_tokens'
    
    id = Column(Integer, primary_key=True)
    token = Column(String(100), unique=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    video_id = Column(Integer, nullable=False)
    message_id = Column(BigInteger)  # ID del mensaje del video original
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)  # Tokens expiran después de 24 horas
    ip_address = Column(String(50))  # Para detectar uso abusivo

class BotConfig(Base):
    __tablename__ = 'bot_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)  # Ej: 'last_indexed_message'
    value = Column(String(500), nullable=False)  # Valor como string
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ============ SISTEMA DE TICKETS Y REFERIDOS ============

class UserTicket(Base):
    """Tickets del usuario para ver contenido sin anuncios"""
    __tablename__ = 'user_tickets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    tickets = Column(Integer, default=0)  # Tickets disponibles
    tickets_used = Column(Integer, default=0)  # Total tickets usados
    tickets_earned = Column(Integer, default=0)  # Total tickets ganados
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class TicketTransaction(Base):
    """Historial de transacciones de tickets"""
    __tablename__ = 'ticket_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(Integer, nullable=False)  # Positivo = ganado, Negativo = usado
    reason = Column(String(100), nullable=False)  # 'referral', 'admin_gift', 'used', 'task'
    description = Column(String(500))  # Descripción adicional
    reference_id = Column(BigInteger)  # ID del referido, video, o admin
    created_at = Column(DateTime, server_default=func.now())

class Referral(Base):
    """Sistema de referidos"""
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, nullable=False)  # Quien invitó
    referred_id = Column(BigInteger, unique=True, nullable=False)  # Quien fue invitado
    status = Column(String(20), default='pending')  # pending, verified, rewarded
    referred_at = Column(DateTime, server_default=func.now())
    verified_at = Column(DateTime)  # Cuando el referido se verificó en el canal
    rewarded_at = Column(DateTime)  # Cuando se dieron los tickets al referrer

class UserActivity(Base):
    """Registro de actividad del usuario"""
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    action_type = Column(String(50), nullable=False)  # 'search', 'watch_movie', 'watch_episode', 'ad_viewed'
    content_id = Column(Integer)  # ID del video/episodio
    content_type = Column(String(20))  # 'movie', 'episode'
    used_ticket = Column(Boolean, default=False)  # Si usó ticket para ver sin anuncio
    created_at = Column(DateTime, server_default=func.now())

class ChannelSource(Base):
    """Canales fuente para tracking de estadísticas"""
    __tablename__ = 'channel_sources'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(100), unique=True, nullable=False)  # ej: "canal_principal"
    channel_name = Column(String(200), nullable=False)  # ej: "@tu_canal_principal"
    channel_url = Column(String(300))  # URL del canal
    description = Column(Text)  # Descripción del canal
    added_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

class ChannelVisit(Base):
    """Registro de visitas desde canales específicos"""
    __tablename__ = 'channel_visits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    channel_source_id = Column(Integer, ForeignKey('channel_sources.id', ondelete='CASCADE'), nullable=False)
    visited_at = Column(DateTime, server_default=func.now())
    is_new_user = Column(Boolean, default=False)  # Si es primera vez que usa el bot
    
    # Relación
    channel_source = relationship("ChannelSource")
