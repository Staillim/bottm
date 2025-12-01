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
