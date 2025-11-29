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
