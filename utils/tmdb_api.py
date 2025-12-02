import requests
from config.settings import TMDB_API_KEY

class TMDBApi:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    
    def __init__(self):
        self.api_key = TMDB_API_KEY
    
    def search_movie(self, title, year=None, return_multiple=False, limit=5):
        """
        Busca una película por título - Primero en español, luego en inglés
        
        Args:
            title: Título de la película
            year: Año (opcional, mejora precisión)
            return_multiple: Si True, retorna lista de resultados. Si False, solo el primero
            limit: Número máximo de resultados cuando return_multiple=True
            
        Returns:
            Si return_multiple=False: dict con datos de película o None
            Si return_multiple=True: lista de dicts con resultados ordenados por relevancia
        """
        try:
            # 1. Buscar en español con año
            results = self._search_with_language(title, "es-ES", year, return_all=True)
            
            # 2. Si no encuentra suficientes, buscar en inglés
            if len(results) < limit:
                en_results = self._search_with_language(title, "en-US", year, return_all=True)
                # Agregar resultados en inglés que no estén duplicados
                existing_ids = {r['tmdb_id'] for r in results}
                for r in en_results:
                    if r['tmdb_id'] not in existing_ids:
                        results.append(r)
                        if len(results) >= limit:
                            break
            
            # 3. Si aún no encuentra y había año, intentar sin año
            if len(results) == 0 and year:
                results = self._search_with_language(title, "es-ES", None, return_all=True)
                if len(results) < limit:
                    en_results = self._search_with_language(title, "en-US", None, return_all=True)
                    existing_ids = {r['tmdb_id'] for r in results}
                    for r in en_results:
                        if r['tmdb_id'] not in existing_ids:
                            results.append(r)
                            if len(results) >= limit:
                                break
            
            # Calcular score de confianza para cada resultado
            for result in results:
                result['confidence'] = self._calculate_confidence(title, year, result)
            
            # Ordenar por confianza
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            if return_multiple:
                return results[:limit]
            else:
                return results[0] if results else None
            
        except Exception as e:
            print(f"Error buscando película: {e}")
            return [] if return_multiple else None
    
    def _calculate_confidence(self, search_title, search_year, result):
        """
        Calcula un score de confianza (0-100) basado en similitud de título y año
        """
        score = 0
        
        # Score por popularidad (0-30 puntos)
        popularity = result.get('popularity', 0)
        score += min(30, popularity / 10)
        
        # Score por coincidencia de año (0-30 puntos)
        if search_year and result.get('year'):
            try:
                if int(search_year) == int(result['year']):
                    score += 30
                elif abs(int(search_year) - int(result['year'])) == 1:
                    score += 15  # Año cercano
            except:
                pass
        
        # Score por similitud de título (0-40 puntos)
        search_lower = search_title.lower().strip()
        title_lower = result.get('title', '').lower().strip()
        original_lower = result.get('original_title', '').lower().strip()
        
        # Coincidencia exacta
        if search_lower == title_lower or search_lower == original_lower:
            score += 40
        # Coincidencia parcial
        elif search_lower in title_lower or title_lower in search_lower:
            score += 30
        elif search_lower in original_lower or original_lower in search_lower:
            score += 25
        # Palabras en común
        else:
            search_words = set(search_lower.split())
            title_words = set(title_lower.split())
            common_words = search_words & title_words
            if common_words:
                score += 20 * (len(common_words) / max(len(search_words), 1))
        
        return min(100, score)
    
    def _search_with_language(self, title, language, year=None, return_all=False):
        """
        Busca en un idioma específico
        
        Args:
            return_all: Si True, retorna lista de todos los resultados. Si False, solo el primero
        """
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
                if return_all:
                    return [self._format_movie_data(movie) for movie in data["results"][:10]]
                else:
                    return self._format_movie_data(data["results"][0])
            return [] if return_all else None
            
        except Exception as e:
            print(f"Error en búsqueda ({language}): {e}")
            return [] if return_all else None
    
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
        year_str = show.get("first_air_date", "")[:4] if show.get("first_air_date") else None
        year = int(year_str) if year_str and year_str.isdigit() else None
        
        return {
            "tmdb_id": show.get("id"),
            "name": show.get("name", "Sin título"),
            "original_name": show.get("original_name", ""),
            "year": year,
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
            
            year_str = show.get("first_air_date", "")[:4] if show.get("first_air_date") else None
            year = int(year_str) if year_str and year_str.isdigit() else None
            
            return {
                "tmdb_id": show.get("id"),
                "name": show.get("name", "Sin título"),
                "original_name": show.get("original_name", ""),
                "year": year,
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

