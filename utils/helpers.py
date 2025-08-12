"""
Utility functions and helpers for the Telegram Movie Bot
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def format_error_message(error_description: str) -> str:
    """
    Format error messages for user display
    
    Args:
        error_description: Description of the error
        
    Returns:
        Formatted error message
    """
    return f"❌ {error_description}\n\nPlease try again or use /help for assistance."

def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate if file size is within limits
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if file size is valid, False otherwise
    """
    return file_size <= max_size

def clean_movie_title(title: str) -> str:
    """
    Clean movie title for better search results
    
    Args:
        title: Raw movie title
        
    Returns:
        Cleaned movie title
    """
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Remove common suffixes that might interfere with search
    suffixes_to_remove = [
        r'\s*\(\d{4}\)$',  # Year in parentheses
        r'\s*\[.*\]$',     # Anything in square brackets
        r'\s*-\s*trailer$',  # " - trailer"
        r'\s*official\s*trailer$',  # " official trailer"
    ]
    
    for suffix in suffixes_to_remove:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    
    return title.strip()

def extract_year_from_string(text: str) -> Optional[str]:
    """
    Extract year from a string (movie title, description, etc.)
    
    Args:
        text: Text that might contain a year
        
    Returns:
        Year as string if found, None otherwise
    """
    # Look for 4-digit years (1900-2099)
    year_pattern = r'\b(19\d{2}|20\d{2})\b'
    match = re.search(year_pattern, text)
    
    if match:
        return match.group(1)
    
    return None

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix
    
    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix

def format_runtime(minutes: int) -> str:
    """
    Format runtime in minutes to hours and minutes
    
    Args:
        minutes: Runtime in minutes
        
    Returns:
        Formatted runtime string
    """
    if minutes < 60:
        return f"{minutes}min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes}min"

def format_rating(rating: float, max_rating: float = 10.0) -> str:
    """
    Format rating with appropriate emoji
    
    Args:
        rating: Rating value
        max_rating: Maximum possible rating
        
    Returns:
        Formatted rating string with emoji
    """
    try:
        normalized_rating = rating / max_rating
        
        if normalized_rating >= 0.8:
            emoji = "🌟"
        elif normalized_rating >= 0.7:
            emoji = "⭐"
        elif normalized_rating >= 0.6:
            emoji = "🔸"
        else:
            emoji = "📊"
        
        return f"{emoji} {rating}/{max_rating}"
        
    except (TypeError, ZeroDivisionError):
        return f"📊 {rating}"

def parse_imdb_id(imdb_string: str) -> Optional[str]:
    """
    Extract IMDB ID from various formats
    
    Args:
        imdb_string: String that might contain IMDB ID
        
    Returns:
        IMDB ID if found, None otherwise
    """
    # IMDB ID pattern: tt followed by 7+ digits
    imdb_pattern = r'\b(tt\d{7,})\b'
    match = re.search(imdb_pattern, imdb_string)
    
    if match:
        return match.group(1)
    
    return None

def format_list_with_limit(items: List[str], limit: int = 3, separator: str = ", ") -> str:
    """
    Format a list with a limit on number of items shown
    
    Args:
        items: List of items to format
        limit: Maximum number of items to show
        separator: Separator between items
        
    Returns:
        Formatted string
    """
    if not items:
        return "N/A"
    
    if len(items) <= limit:
        return separator.join(items)
    
    limited_items = items[:limit]
    return separator.join(limited_items) + f" and {len(items) - limit} more"

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    # Characters that need to be escaped in Telegram Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def convert_duration_to_minutes(duration_str: str) -> Optional[int]:
    """
    Convert various duration formats to minutes
    
    Args:
        duration_str: Duration string (e.g., "PT2H30M", "150 min", "2h 30m")
        
    Returns:
        Duration in minutes if parsed successfully, None otherwise
    """
    try:
        # ISO 8601 duration format (YouTube API format)
        if duration_str.startswith('PT'):
            hours_match = re.search(r'(\d+)H', duration_str)
            minutes_match = re.search(r'(\d+)M', duration_str)
            seconds_match = re.search(r'(\d+)S', duration_str)
            
            total_minutes = 0
            
            if hours_match:
                total_minutes += int(hours_match.group(1)) * 60
            
            if minutes_match:
                total_minutes += int(minutes_match.group(1))
            
            if seconds_match:
                total_minutes += int(seconds_match.group(1)) / 60
            
            return int(total_minutes)
        
        # Other common formats
        # "150 min" or "150min"
        min_match = re.search(r'(\d+)\s*min', duration_str, re.IGNORECASE)
        if min_match:
            return int(min_match.group(1))
        
        # "2h 30m" or "2h30m"
        hm_match = re.search(r'(\d+)h\s*(\d+)m', duration_str, re.IGNORECASE)
        if hm_match:
            hours = int(hm_match.group(1))
            minutes = int(hm_match.group(2))
            return hours * 60 + minutes
        
        # "2h" or "2 hours"
        h_match = re.search(r'(\d+)\s*h(?:ours?)?', duration_str, re.IGNORECASE)
        if h_match:
            return int(h_match.group(1)) * 60
        
        return None
        
    except (ValueError, AttributeError):
        return None

def calculate_confidence_emoji(confidence: float) -> str:
    """
    Get appropriate emoji based on confidence score
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
        
    Returns:
        Appropriate emoji
    """
    if confidence >= 0.9:
        return "🎯"  # Very high confidence
    elif confidence >= 0.75:
        return "⭐"  # High confidence
    elif confidence >= 0.5:
        return "🔸"  # Medium confidence
    elif confidence >= 0.3:
        return "❓"  # Low confidence
    else:
        return "❌"  # Very low confidence

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for most filesystems
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename
    
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Limit length
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized

def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename
        
    Returns:
        File extension (without dot) in lowercase
    """
    return os.path.splitext(filename.lower())[1][1:]  # Remove the dot

def format_bytes(bytes_value: float) -> str:
    """
    Format bytes into human readable format
    
    Args:
        bytes_value: Size in bytes
        
    Returns:
        Human readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}TB"
