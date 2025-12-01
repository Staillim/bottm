import requests
from config.settings import TMDB_API_KEY

class TMDBApi:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    
    def __init__(self):
        self.api_key = TMDB_API_KEY
    
    def search_movie(self, title):
        """Busca una película por título - Primero en español, luego en inglés"""
        try:
            # Extraer año si está presente (ej: "Thor (2022)" -> "Thor", "2022")
            year = None
            clean_title = title
            if "(" in title and ")" in title:
                parts = title.split("(")
                clean_title = parts[0].strip()
                year_text = parts[1].split(")")[0].strip()
                if year_text.isdigit():
                    year = year_text
            
            # 1. Intentar buscar en español
            result = self._search_with_language(clean_title, "es-ES", year)
            if result:
                return result
            
            # 2. Si no encuentra en español, buscar en inglés
            result = self._search_with_language(clean_title, "en-US", year)
            if result:
                return result
            
            # 3. Último intento sin año
            if year:
                result = self._search_with_language(clean_title, "es-ES", None)
                if result:
                    return result
            
            return None
            
        except Exception as e:
            print(f"Error buscando película: {e}")
            return None
    
    def _search_with_language(self, title, language, year=None):
        """Busca en un idioma específico"""
        try:
            url = f"{self.BASE_URL}/search/movie"
            params = {
                "api_key": self.api_key,
                "query": title,
                "language": language,
                "page": 1
            }
            
            if year:
                params["year"] = year
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["results"]:
                return self._format_movie_data(data["results"][0])
            return None
            
        except Exception as e:
            print(f"Error en búsqueda ({language}): {e}")
            return None
    
    def _format_movie_data(self, movie):
        """Formatea los datos de la película"""
        return {
            "tmdb_id": movie.get("id"),
            "title": movie.get("title", "Sin título"),
            "original_title": movie.get("original_title", ""),
            "year": movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A",
            "overview": movie.get("overview", "Sin descripción disponible."),
            "poster_url": f"{self.IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
            "backdrop_url": f"{self.IMAGE_BASE_URL}{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
            "vote_average": movie.get("vote_average", 0),
            "popularity": movie.get("popularity", 0),
            "genre_ids": movie.get("genre_ids", [])
        }
    
    def get_movie_details(self, tmdb_id):
        """Obtiene detalles completos de una película por su ID de TMDB"""
        try:
            url = f"{self.BASE_URL}/movie/{tmdb_id}"
            params = {
                "api_key": self.api_key,
                "language": "es-ES"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            movie = response.json()
            
            return {
                "tmdb_id": movie.get("id"),
                "title": movie.get("title", "Sin título"),
                "original_title": movie.get("original_title", ""),
                "year": movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A",
                "overview": movie.get("overview", "Sin descripción disponible."),
                "poster_url": f"{self.IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
                "backdrop_url": f"{self.IMAGE_BASE_URL}{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
                "vote_average": movie.get("vote_average", 0),
                "runtime": movie.get("runtime", 0),
                "genres": [g["name"] for g in movie.get("genres", [])],
                "budget": movie.get("budget", 0),
                "revenue": movie.get("revenue", 0),
                "tagline": movie.get("tagline", "")
            }
            
        except Exception as e:
            print(f"Error obteniendo detalles: {e}")
            return None
    
    # ==================== MÉTODOS PARA SERIES ====================
    
    def search_tv_show(self, name):
        """Busca una serie por nombre - Primero en español, luego en inglés"""
        try:
            # Extraer año si está presente (ej: "Loki (2021)" -> "Loki", "2021")
            year = None
            clean_name = name
            if "(" in name and ")" in name:
                parts = name.split("(")
                clean_name = parts[0].strip()
                year_text = parts[1].split(")")[0].strip()
                if year_text.isdigit():
                    year = year_text
            
            # 1. Intentar buscar en español
            result = self._search_tv_with_language(clean_name, "es-ES", year)
            if result:
                return result
            
            # 2. Si no encuentra en español, buscar en inglés
            result = self._search_tv_with_language(clean_name, "en-US", year)
            if result:
                return result
            
            # 3. Último intento sin año
            if year:
                result = self._search_tv_with_language(clean_name, "es-ES", None)
                if result:
                    return result
            
            return None
            
        except Exception as e:
            print(f"Error buscando serie: {e}")
            return None
    
    def _search_tv_with_language(self, name, language, year=None):
        """Busca serie en un idioma específico"""
        try:
            url = f"{self.BASE_URL}/search/tv"
            params = {
                "api_key": self.api_key,
                "query": name,
                "language": language,
                "page": 1
            }
            
            if year:
                params["first_air_date_year"] = year
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["results"]:
                return self._format_tv_data(data["results"][0])
            return None
            
        except Exception as e:
            print(f"Error en búsqueda de serie ({language}): {e}")
            return None
    
    def _format_tv_data(self, show):
        """Formatea los datos de la serie"""
        return {
            "tmdb_id": show.get("id"),
            "name": show.get("name", "Sin título"),
            "original_name": show.get("original_name", ""),
            "year": show.get("first_air_date", "")[:4] if show.get("first_air_date") else "N/A",
            "overview": show.get("overview", "Sin descripción disponible."),
            "poster_url": f"{self.IMAGE_BASE_URL}{show['poster_path']}" if show.get("poster_path") else None,
            "backdrop_url": f"{self.IMAGE_BASE_URL}{show['backdrop_path']}" if show.get("backdrop_path") else None,
            "vote_average": show.get("vote_average", 0),
            "popularity": show.get("popularity", 0),
            "genre_ids": show.get("genre_ids", [])
        }
    
    def get_tv_show_details(self, tmdb_id):
        """Obtiene detalles completos de una serie por su ID de TMDB"""
        try:
            url = f"{self.BASE_URL}/tv/{tmdb_id}"
            params = {
                "api_key": self.api_key,
                "language": "es-ES"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            show = response.json()
            
            return {
                "tmdb_id": show.get("id"),
                "name": show.get("name", "Sin título"),
                "original_name": show.get("original_name", ""),
                "year": show.get("first_air_date", "")[:4] if show.get("first_air_date") else "N/A",
                "overview": show.get("overview", "Sin descripción disponible."),
                "poster_url": f"{self.IMAGE_BASE_URL}{show['poster_path']}" if show.get("poster_path") else None,
                "backdrop_url": f"{self.IMAGE_BASE_URL}{show['backdrop_path']}" if show.get("backdrop_path") else None,
                "vote_average": show.get("vote_average", 0),
                "number_of_seasons": show.get("number_of_seasons", 0),
                "number_of_episodes": show.get("number_of_episodes", 0),
                "genres": [g["name"] for g in show.get("genres", [])],
                "status": show.get("status", "Unknown"),
                "tagline": show.get("tagline", ""),
                "networks": [n["name"] for n in show.get("networks", [])],
                "created_by": [c["name"] for c in show.get("created_by", [])]
            }
            
        except Exception as e:
            print(f"Error obteniendo detalles de serie: {e}")
            return None
    
    def get_season_details(self, tmdb_id, season_number):
        """Obtiene detalles de una temporada específica incluyendo episodios"""
        try:
            url = f"{self.BASE_URL}/tv/{tmdb_id}/season/{season_number}"
            params = {
                "api_key": self.api_key,
                "language": "es-ES"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            season = response.json()
            
            episodes = []
            for ep in season.get("episodes", []):
                episodes.append({
                    "episode_number": ep.get("episode_number"),
                    "name": ep.get("name", f"Episodio {ep.get('episode_number')}"),
                    "overview": ep.get("overview", "Sin descripción disponible."),
                    "air_date": ep.get("air_date"),
                    "runtime": ep.get("runtime"),
                    "still_path": f"{self.IMAGE_BASE_URL}{ep['still_path']}" if ep.get("still_path") else None,
                    "vote_average": ep.get("vote_average", 0)
                })
            
            return {
                "season_number": season.get("season_number"),
                "name": season.get("name", f"Temporada {season.get('season_number')}"),
                "overview": season.get("overview", ""),
                "air_date": season.get("air_date"),
                "poster_url": f"{self.IMAGE_BASE_URL}{season['poster_path']}" if season.get("poster_path") else None,
                "episodes": episodes
            }
            
        except Exception as e:
            print(f"Error obteniendo temporada: {e}")
            return None

