"""
Configuration management for the Telegram Movie Bot
"""

import os
from typing import Optional

class Config:
    """Configuration class to manage environment variables and API keys"""
    
    def __init__(self):
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # TMDB API Configuration
        self.TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
        self.TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
        self.TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"
        
        # OMDB API Configuration
        self.OMDB_API_KEY: str = os.getenv("OMDB_API_KEY", "")
        self.OMDB_BASE_URL: str = "http://www.omdbapi.com/"
        
        # YouTube API Configuration
        self.YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
        self.YOUTUBE_BASE_URL: str = "https://www.googleapis.com/youtube/v3"
        
        # Google Vision API (for image analysis)
        self.GOOGLE_VISION_API_KEY: str = os.getenv("GOOGLE_VISION_API_KEY", "")
        
        # Application Configuration
        self.MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
        self.SUPPORTED_IMAGE_FORMATS: list = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        self.SUPPORTED_VIDEO_FORMATS: list = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        
        # Rate limiting
        self.REQUEST_TIMEOUT: int = 30
        self.MAX_RETRIES: int = 3
    
    def validate_apis(self) -> dict:
        """Validate which APIs are properly configured"""
        apis = {
            'tmdb': bool(self.TMDB_API_KEY),
            'omdb': bool(self.OMDB_API_KEY),
            'youtube': bool(self.YOUTUBE_API_KEY),
            'google_vision': bool(self.GOOGLE_VISION_API_KEY)
        }
        return apis
    
    def get_api_status(self) -> str:
        """Get a formatted string of API status"""
        apis = self.validate_apis()
        status_lines = []
        for api, configured in apis.items():
            status = "✅ Configured" if configured else "❌ Not configured"
            status_lines.append(f"{api.upper()}: {status}")
        return "\n".join(status_lines)
