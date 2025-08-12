"""
Movie service for integrating TMDB and OMDB APIs
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from config import Config

logger = logging.getLogger(__name__)

class MovieService:
    """Service class for movie data retrieval and processing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_movies(self, query: str) -> Dict[str, Any]:
        """
        Search for movies using both TMDB and OMDB APIs
        
        Args:
            query: Movie search query
            
        Returns:
            Combined movie data from both APIs
        """
        try:
            # Search using both APIs concurrently
            tmdb_task = self._search_tmdb(query)
            omdb_task = self._search_omdb(query)
            
            tmdb_results, omdb_results = await asyncio.gather(
                tmdb_task, omdb_task, return_exceptions=True
            )
            
            # Process and combine results
            combined_results = self._combine_movie_data(tmdb_results, omdb_results, query)
            return combined_results
            
        except Exception as e:
            logger.error(f"Error searching movies for query '{query}': {e}")
            return {
                'success': False,
                'error': f"Failed to search movies: {str(e)}",
                'movies': []
            }
    
    async def _search_tmdb(self, query: str) -> Dict[str, Any]:
        """Search movies using TMDB API"""
        if not self.config.TMDB_API_KEY:
            return {'success': False, 'error': 'TMDB API key not configured'}
        
        try:
            params = {
                'api_key': self.config.TMDB_API_KEY,
                'query': query,
                'include_adult': 'false',
                'language': 'en-US',
                'page': 1
            }
            
            url = f"{self.config.TMDB_BASE_URL}/search/movie?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'data': data,
                        'source': 'tmdb'
                    }
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return {
                        'success': False,
                        'error': f"TMDB API returned status {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"TMDB search error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _search_omdb(self, query: str) -> Dict[str, Any]:
        """Search movies using OMDB API"""
        if not self.config.OMDB_API_KEY:
            return {'success': False, 'error': 'OMDB API key not configured'}
        
        try:
            params = {
                'apikey': self.config.OMDB_API_KEY,
                's': query,
                'type': 'movie',
                'r': 'json'
            }
            
            url = f"{self.config.OMDB_BASE_URL}?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'data': data,
                        'source': 'omdb'
                    }
                else:
                    logger.error(f"OMDB API error: {response.status}")
                    return {
                        'success': False,
                        'error': f"OMDB API returned status {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"OMDB search error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_movie_details(self, movie_id: str, source: str = 'tmdb') -> Dict[str, Any]:
        """
        Get detailed movie information
        
        Args:
            movie_id: Movie ID from TMDB or IMDB
            source: API source ('tmdb' or 'omdb')
            
        Returns:
            Detailed movie information
        """
        try:
            if source == 'tmdb':
                return await self._get_tmdb_details(movie_id)
            elif source == 'omdb':
                return await self._get_omdb_details(movie_id)
            else:
                return {'success': False, 'error': 'Invalid source specified'}
                
        except Exception as e:
            logger.error(f"Error getting movie details: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_tmdb_details(self, movie_id: str) -> Dict[str, Any]:
        """Get detailed movie info from TMDB"""
        if not self.config.TMDB_API_KEY:
            return {'success': False, 'error': 'TMDB API key not configured'}
        
        try:
            params = {
                'api_key': self.config.TMDB_API_KEY,
                'language': 'en-US',
                'append_to_response': 'credits,videos,reviews'
            }
            
            url = f"{self.config.TMDB_BASE_URL}/movie/{movie_id}?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'data': data,
                        'source': 'tmdb'
                    }
                else:
                    return {
                        'success': False,
                        'error': f"TMDB API returned status {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"TMDB details error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_omdb_details(self, imdb_id: str) -> Dict[str, Any]:
        """Get detailed movie info from OMDB"""
        if not self.config.OMDB_API_KEY:
            return {'success': False, 'error': 'OMDB API key not configured'}
        
        try:
            params = {
                'apikey': self.config.OMDB_API_KEY,
                'i': imdb_id,
                'plot': 'full',
                'r': 'json'
            }
            
            url = f"{self.config.OMDB_BASE_URL}?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('Response') == 'True':
                        return {
                            'success': True,
                            'data': data,
                            'source': 'omdb'
                        }
                    else:
                        return {
                            'success': False,
                            'error': data.get('Error', 'Unknown OMDB error')
                        }
                else:
                    return {
                        'success': False,
                        'error': f"OMDB API returned status {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"OMDB details error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _combine_movie_data(self, tmdb_results: Any, omdb_results: Any, query: str) -> Dict[str, Any]:
        """Combine and process results from both APIs"""
        movies = []
        
        try:
            # Process TMDB results
            if isinstance(tmdb_results, dict) and tmdb_results.get('success'):
                tmdb_movies = tmdb_results.get('data', {}).get('results', [])
                for movie in tmdb_movies[:5]:  # Limit to top 5 results
                    processed_movie = self._process_tmdb_movie(movie)
                    movies.append(processed_movie)
            
            # Process OMDB results and merge with TMDB where possible
            if isinstance(omdb_results, dict) and omdb_results.get('success'):
                omdb_movies = omdb_results.get('data', {}).get('Search', [])
                for omdb_movie in omdb_movies[:3]:  # Limit to top 3 results
                    # Check if we already have this movie from TMDB
                    existing_movie = None
                    for movie in movies:
                        if (movie['title'].lower() == omdb_movie.get('Title', '').lower() or
                            movie.get('imdb_id') == omdb_movie.get('imdbID')):
                            existing_movie = movie
                            break
                    
                    if existing_movie:
                        # Merge OMDB data into existing TMDB movie
                        self._merge_omdb_data(existing_movie, omdb_movie)
                    else:
                        # Add as new movie from OMDB
                        processed_movie = self._process_omdb_movie(omdb_movie)
                        movies.append(processed_movie)
            
            return {
                'success': True,
                'movies': movies,
                'query': query,
                'total_results': len(movies)
            }
            
        except Exception as e:
            logger.error(f"Error combining movie data: {e}")
            return {
                'success': False,
                'error': f"Failed to process movie results: {str(e)}",
                'movies': []
            }
    
    def _process_tmdb_movie(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Process TMDB movie data into standardized format"""
        poster_path = movie.get('poster_path')
        poster_url = f"{self.config.TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None
        
        return {
            'title': movie.get('title', 'Unknown Title'),
            'original_title': movie.get('original_title'),
            'release_date': movie.get('release_date'),
            'overview': movie.get('overview', 'No overview available'),
            'vote_average': movie.get('vote_average'),
            'vote_count': movie.get('vote_count'),
            'popularity': movie.get('popularity'),
            'poster_url': poster_url,
            'tmdb_id': movie.get('id'),
            'imdb_id': None,  # Will be filled if OMDB data is merged
            'genre_ids': movie.get('genre_ids', []),
            'adult': movie.get('adult', False),
            'source': 'tmdb'
        }
    
    def _process_omdb_movie(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Process OMDB movie data into standardized format"""
        return {
            'title': movie.get('Title', 'Unknown Title'),
            'original_title': movie.get('Title'),
            'release_date': movie.get('Year'),
            'overview': movie.get('Plot', 'No plot available'),
            'vote_average': self._parse_imdb_rating(movie.get('imdbRating')),
            'vote_count': None,
            'popularity': None,
            'poster_url': movie.get('Poster') if movie.get('Poster') != 'N/A' else None,
            'tmdb_id': None,
            'imdb_id': movie.get('imdbID'),
            'genre_ids': [],
            'adult': False,
            'source': 'omdb',
            'type': movie.get('Type'),
            'director': movie.get('Director'),
            'actors': movie.get('Actors')
        }
    
    def _merge_omdb_data(self, tmdb_movie: Dict[str, Any], omdb_movie: Dict[str, Any]) -> None:
        """Merge OMDB data into TMDB movie entry"""
        tmdb_movie['imdb_id'] = omdb_movie.get('imdbID')
        tmdb_movie['director'] = omdb_movie.get('Director')
        tmdb_movie['actors'] = omdb_movie.get('Actors')
        tmdb_movie['type'] = omdb_movie.get('Type')
        
        # Use OMDB poster if TMDB doesn't have one
        if not tmdb_movie.get('poster_url') and omdb_movie.get('Poster') != 'N/A':
            tmdb_movie['poster_url'] = omdb_movie.get('Poster')
    
    def _parse_imdb_rating(self, rating_str: Optional[str]) -> Optional[float]:
        """Parse IMDB rating string to float"""
        try:
            if rating_str and rating_str != 'N/A':
                return float(rating_str)
        except (ValueError, TypeError):
            pass
        return None
    
    def format_movie_message(self, movie: Dict[str, Any]) -> str:
        """Format movie data into a readable message"""
        try:
            title = movie.get('title', 'Unknown Title')
            release_date = movie.get('release_date', 'Unknown')
            overview = movie.get('overview', 'No overview available')
            rating = movie.get('vote_average')
            imdb_id = movie.get('imdb_id')
            director = movie.get('director')
            actors = movie.get('actors')
            
            message_parts = [f"🎬 *{title}*"]
            
            if release_date:
                if len(release_date) >= 4:  # Extract year from date
                    year = release_date[:4]
                    message_parts.append(f"📅 *Year:* {year}")
                else:
                    message_parts.append(f"📅 *Year:* {release_date}")
            
            if rating:
                message_parts.append(f"⭐ *Rating:* {rating}/10")
            
            if director and director != 'N/A':
                message_parts.append(f"🎭 *Director:* {director}")
            
            if actors and actors != 'N/A':
                # Limit actors list to first 3
                actor_list = actors.split(', ')[:3]
                message_parts.append(f"👥 *Cast:* {', '.join(actor_list)}")
            
            if overview:
                # Limit overview length
                if len(overview) > 300:
                    overview = overview[:297] + "..."
                message_parts.append(f"📖 *Plot:* {overview}")
            
            if imdb_id:
                message_parts.append(f"🔗 [View on IMDB](https://www.imdb.com/title/{imdb_id}/)")
            
            return "\n\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting movie message: {e}")
            return f"🎬 *{movie.get('title', 'Unknown Movie')}*\n\nError formatting movie details."
