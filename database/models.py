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
    
    # Relaciones para el sistema de puntos
    points = relationship("UserPoints", back_populates="user", uselist=False)
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")

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


class UserPoints(Base):
    __tablename__ = 'user_points'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, unique=True)
    total_points = Column(Float, default=0.0, nullable=False)
    available_points = Column(Float, default=0.0, nullable=False)
    used_points = Column(Float, default=0.0, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="points")
    transactions = relationship("PointsTransaction", back_populates="user_points")


class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referrer_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    referred_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    status = Column(String(20), default='pending', nullable=False)  # pending, completed, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # Código expira después de 30 días
    
    # Relaciones
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")


class PointsTransaction(Base):
    __tablename__ = 'points_transactions'
    
    id = Column(Integer, primary_key=True)
    user_points_id = Column(Integer, ForeignKey('user_points.id'), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # earned, used, bonus, referral
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    reference_id = Column(String(100))  # ID de referencia (video_id, referral_id, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user_points = relationship("UserPoints", back_populates="transactions")
