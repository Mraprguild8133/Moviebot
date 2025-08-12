"""
YouTube service for finding movie trailers
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from config import Config

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service for finding movie trailers on YouTube"""
    
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
    
    async def find_trailer(self, movie_title: str, release_year: Optional[str] = None) -> Dict[str, Any]:
        """
        Find movie trailer on YouTube
        
        Args:
            movie_title: Title of the movie
            release_year: Optional release year for better matching
            
        Returns:
            Trailer information with YouTube URL
        """
        try:
            if not self.config.YOUTUBE_API_KEY:
                return {
                    'success': False,
                    'error': 'YouTube API key not configured',
                    'trailers': []
                }
            
            # Construct search query
            search_queries = self._build_search_queries(movie_title, release_year)
            
            # Try each search query until we find good results
            for query in search_queries:
                trailer_results = await self._search_youtube(query)
                
                if trailer_results.get('success') and trailer_results.get('videos'):
                    # Filter and rank results
                    filtered_trailers = self._filter_trailer_results(
                        trailer_results['videos'], 
                        movie_title, 
                        release_year
                    )
                    
                    if filtered_trailers:
                        return {
                            'success': True,
                            'trailers': filtered_trailers,
                            'search_query': query
                        }
            
            # No good results found
            return {
                'success': True,
                'trailers': [],
                'message': 'No trailers found for this movie'
            }
            
        except Exception as e:
            logger.error(f"Error finding trailer for '{movie_title}': {e}")
            return {
                'success': False,
                'error': f"Failed to search for trailers: {str(e)}",
                'trailers': []
            }
    
    def _build_search_queries(self, movie_title: str, release_year: Optional[str] = None) -> List[str]:
        """Build multiple search queries for better results"""
        queries = []
        
        # Clean movie title
        clean_title = movie_title.strip()
        
        # Primary queries
        if release_year:
            queries.append(f"{clean_title} {release_year} official trailer")
            queries.append(f"{clean_title} {release_year} trailer")
            queries.append(f"{clean_title} movie {release_year} trailer")
        
        queries.extend([
            f"{clean_title} official trailer",
            f"{clean_title} movie trailer",
            f"{clean_title} trailer",
            f"{clean_title} film trailer"
        ])
        
        return queries
    
    async def _search_youtube(self, query: str) -> Dict[str, Any]:
        """Search YouTube using the Data API"""
        try:
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': 10,
                'order': 'relevance',
                'videoDuration': 'any',
                'videoDefinition': 'any',
                'key': self.config.YOUTUBE_API_KEY
            }
            
            url = f"{self.config.YOUTUBE_BASE_URL}/search?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    videos = []
                    for item in data.get('items', []):
                        video_info = self._parse_youtube_item(item)
                        if video_info:
                            videos.append(video_info)
                    
                    return {
                        'success': True,
                        'videos': videos,
                        'total_results': data.get('pageInfo', {}).get('totalResults', 0)
                    }
                else:
                    logger.error(f"YouTube API error: {response.status}")
                    return {
                        'success': False,
                        'error': f"YouTube API returned status {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_youtube_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse YouTube API response item"""
        try:
            video_id = item.get('id', {}).get('videoId')
            if not video_id:
                return None
            
            snippet = item.get('snippet', {})
            
            return {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
            
        except Exception as e:
            logger.error(f"Error parsing YouTube item: {e}")
            return None
    
    def _filter_trailer_results(self, videos: List[Dict[str, Any]], 
                              movie_title: str, release_year: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter and rank YouTube results to find the best trailers"""
        try:
            scored_videos = []
            movie_title_lower = movie_title.lower()
            
            for video in videos:
                score = self._calculate_trailer_score(video, movie_title_lower, release_year)
                if score > 0.3:  # Minimum relevance threshold
                    video['relevance_score'] = score
                    scored_videos.append(video)
            
            # Sort by relevance score
            scored_videos.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return scored_videos[:3]  # Return top 3 trailers
            
        except Exception as e:
            logger.error(f"Error filtering trailer results: {e}")
            return videos[:3]  # Fallback to first 3 results
    
    def _calculate_trailer_score(self, video: Dict[str, Any], 
                               movie_title_lower: str, release_year: Optional[str] = None) -> float:
        """Calculate relevance score for a YouTube video"""
        try:
            title = video.get('title', '').lower()
            description = video.get('description', '').lower()
            channel = video.get('channel_title', '').lower()
            
            score = 0.0
            
            # Title matching
            if movie_title_lower in title:
                score += 0.5
            
            # Check for trailer keywords
            trailer_keywords = ['trailer', 'official trailer', 'movie trailer', 'teaser']
            for keyword in trailer_keywords:
                if keyword in title:
                    score += 0.3
                    break
            
            # Official channels get bonus points
            official_channels = ['sony pictures', 'warner bros', 'disney', 'universal', 
                               'paramount', 'fox', 'lionsgate', 'marvel', 'dc']
            for official_channel in official_channels:
                if official_channel in channel:
                    score += 0.2
                    break
            
            # Year matching
            if release_year and release_year in title:
                score += 0.2
            
            # Penalty for fan-made or reaction videos
            penalty_keywords = ['reaction', 'review', 'analysis', 'breakdown', 
                              'fan made', 'unofficial', 'mashup', 'parody']
            for keyword in penalty_keywords:
                if keyword in title or keyword in description:
                    score -= 0.3
                    break
            
            # Bonus for official content
            if 'official' in title:
                score += 0.2
            
            return max(score, 0.0)  # Ensure non-negative score
            
        except Exception as e:
            logger.error(f"Error calculating trailer score: {e}")
            return 0.5  # Default score
    
    async def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get detailed information about a YouTube video"""
        try:
            if not self.config.YOUTUBE_API_KEY:
                return {
                    'success': False,
                    'error': 'YouTube API key not configured'
                }
            
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': video_id,
                'key': self.config.YOUTUBE_API_KEY
            }
            
            url = f"{self.config.YOUTUBE_BASE_URL}/videos?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    
                    if items:
                        video_data = items[0]
                        return {
                            'success': True,
                            'video': self._parse_video_details(video_data)
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Video not found'
                        }
                else:
                    return {
                        'success': False,
                        'error': f"YouTube API returned status {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_video_details(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse detailed video information"""
        try:
            snippet = video_data.get('snippet', {})
            statistics = video_data.get('statistics', {})
            content_details = video_data.get('contentDetails', {})
            
            return {
                'id': video_data.get('id'),
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'channel_title': snippet.get('channelTitle'),
                'published_at': snippet.get('publishedAt'),
                'duration': content_details.get('duration'),
                'view_count': statistics.get('viewCount'),
                'like_count': statistics.get('likeCount'),
                'comment_count': statistics.get('commentCount'),
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url')
            }
            
        except Exception as e:
            logger.error(f"Error parsing video details: {e}")
            return {}
    
    def format_trailer_message(self, trailers: List[Dict[str, Any]], movie_title: str) -> str:
        """Format trailer results into a readable message"""
        try:
            if not trailers:
                return f"🎬 No trailers found for '{movie_title}'"
            
            message_parts = [f"🎬 *Trailers for '{movie_title}'*\n"]
            
            for i, trailer in enumerate(trailers, 1):
                title = trailer.get('title', 'Unknown Title')
                channel = trailer.get('channel_title', 'Unknown Channel')
                url = trailer.get('url', '')
                relevance = trailer.get('relevance_score', 0)
                
                # Truncate long titles
                if len(title) > 60:
                    title = title[:57] + "..."
                
                relevance_emoji = "🎯" if relevance > 0.8 else "⭐" if relevance > 0.6 else "🔗"
                
                message_parts.append(
                    f"{i}. {relevance_emoji} [{title}]({url})\n"
                    f"   📺 *Channel:* {channel}"
                )
            
            return "\n\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting trailer message: {e}")
            return f"🎬 Found trailers for '{movie_title}' but failed to format results."
