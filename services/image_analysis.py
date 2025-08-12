"""
Image analysis service for movie poster recognition
"""

import asyncio
import aiohttp
import logging
import base64
import io
from typing import Dict, List, Optional, Any
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    """Service for analyzing images to identify movie posters"""
    
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
    
    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze an image to identify potential movie content
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Analysis results with potential movie titles and confidence scores
        """
        try:
            # Validate and process image
            processed_image = await self._process_image(image_data)
            if not processed_image['success']:
                return processed_image
            
            # Perform text detection for movie titles
            text_results = await self._detect_text_in_image(processed_image['data'])
            
            # Perform object detection for movie poster characteristics
            object_results = await self._detect_poster_features(processed_image['data'])
            
            # Combine and analyze results
            analysis_results = self._combine_analysis_results(text_results, object_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                'success': False,
                'error': f"Failed to analyze image: {str(e)}",
                'potential_movies': []
            }
    
    async def _process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process and validate image data"""
        try:
            # Check file size
            if len(image_data) > self.config.MAX_FILE_SIZE:
                return {
                    'success': False,
                    'error': 'Image file too large (max 20MB)'
                }
            
            # Open and validate image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 1920x1080)
            max_width, max_height = 1920, 1080
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=85)
            processed_data = img_buffer.getvalue()
            
            return {
                'success': True,
                'data': processed_data,
                'width': image.width,
                'height': image.height
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                'success': False,
                'error': f"Invalid image format: {str(e)}"
            }
    
    async def _detect_text_in_image(self, image_data: bytes) -> Dict[str, Any]:
        """Use Google Vision API to detect text in the image"""
        if not self.config.GOOGLE_VISION_API_KEY:
            return await self._fallback_text_detection(image_data)
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request payload
            payload = {
                'requests': [{
                    'image': {
                        'content': image_base64
                    },
                    'features': [{
                        'type': 'TEXT_DETECTION',
                        'maxResults': 10
                    }]
                }]
            }
            
            # Make API request
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.config.GOOGLE_VISION_API_KEY}"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_vision_text_results(data)
                else:
                    logger.error(f"Google Vision API error: {response.status}")
                    return await self._fallback_text_detection(image_data)
                    
        except Exception as e:
            logger.error(f"Google Vision text detection error: {e}")
            return await self._fallback_text_detection(image_data)
    
    async def _fallback_text_detection(self, image_data: bytes) -> Dict[str, Any]:
        """Fallback text detection using basic image processing"""
        try:
            # This is a simplified fallback - in a real implementation,
            # you might use pytesseract or other OCR libraries
            return {
                'success': True,
                'detected_text': [],
                'confidence': 0.3,
                'method': 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Fallback text detection error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_vision_text_results(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Google Vision API text detection results"""
        try:
            responses = vision_data.get('responses', [])
            if not responses:
                return {
                    'success': True,
                    'detected_text': [],
                    'confidence': 0.0
                }
            
            response = responses[0]
            text_annotations = response.get('textAnnotations', [])
            
            detected_texts = []
            for annotation in text_annotations:
                text = annotation.get('description', '').strip()
                confidence = annotation.get('confidence', 0.5)
                
                if text and len(text) > 2:  # Filter out very short text
                    detected_texts.append({
                        'text': text,
                        'confidence': confidence
                    })
            
            return {
                'success': True,
                'detected_text': detected_texts,
                'confidence': max([t['confidence'] for t in detected_texts], default=0.0),
                'method': 'google_vision'
            }
            
        except Exception as e:
            logger.error(f"Error processing Vision API results: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _detect_poster_features(self, image_data: bytes) -> Dict[str, Any]:
        """Detect features that indicate this might be a movie poster"""
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # Basic poster characteristics analysis
            aspect_ratio = height / width if width > 0 else 0
            is_portrait = aspect_ratio > 1.2  # Typical movie poster aspect ratio
            
            # Analyze image for poster-like characteristics
            poster_features = {
                'is_portrait': is_portrait,
                'aspect_ratio': aspect_ratio,
                'width': width,
                'height': height,
                'poster_likelihood': 0.5 if is_portrait else 0.3
            }
            
            return {
                'success': True,
                'features': poster_features
            }
            
        except Exception as e:
            logger.error(f"Error detecting poster features: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _combine_analysis_results(self, text_results: Dict[str, Any], 
                                object_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine text and object detection results"""
        try:
            potential_movies = []
            
            # Extract potential movie titles from detected text
            if text_results.get('success') and text_results.get('detected_text'):
                for text_item in text_results['detected_text']:
                    text = text_item['text']
                    confidence = text_item['confidence']
                    
                    # Filter text that might be movie titles
                    if self._is_potential_movie_title(text):
                        potential_movies.append({
                            'title': text,
                            'confidence': confidence,
                            'source': 'text_detection'
                        })
            
            # Adjust confidence based on poster features
            poster_likelihood = 0.5
            if object_results.get('success'):
                features = object_results.get('features', {})
                poster_likelihood = features.get('poster_likelihood', 0.5)
            
            # Boost confidence for potential movies if image looks like a poster
            for movie in potential_movies:
                movie['confidence'] = min(movie['confidence'] * (1 + poster_likelihood), 1.0)
            
            # Sort by confidence
            potential_movies.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'success': True,
                'potential_movies': potential_movies[:5],  # Top 5 candidates
                'poster_likelihood': poster_likelihood,
                'analysis_methods': [
                    text_results.get('method', 'unknown'),
                    'poster_features'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error combining analysis results: {e}")
            return {
                'success': False,
                'error': str(e),
                'potential_movies': []
            }
    
    def _is_potential_movie_title(self, text: str) -> bool:
        """Determine if text could be a movie title"""
        # Clean the text
        text = text.strip()
        
        # Basic filters
        if len(text) < 2 or len(text) > 100:
            return False
        
        # Skip common non-title text
        skip_patterns = [
            'rating', 'pg-13', 'rated', 'minutes', 'min', 'hrs', 'hours',
            'dvd', 'blu-ray', 'digital', 'download', 'streaming',
            'trailer', 'teaser', 'poster', 'coming soon',
            'www.', 'http', '.com', '.net', '.org'
        ]
        
        text_lower = text.lower()
        for pattern in skip_patterns:
            if pattern in text_lower:
                return False
        
        # Skip if mostly numbers or special characters
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars < len(text) * 0.5:
            return False
        
        return True
    
    def format_analysis_message(self, analysis_results: Dict[str, Any]) -> str:
        """Format image analysis results into a readable message"""
        try:
            if not analysis_results.get('success'):
                return f"❌ Image analysis failed: {analysis_results.get('error', 'Unknown error')}"
            
            potential_movies = analysis_results.get('potential_movies', [])
            poster_likelihood = analysis_results.get('poster_likelihood', 0)
            
            if not potential_movies:
                return ("🔍 *Image Analysis Complete*\n\n"
                       "No movie titles detected in the image. "
                       "This might not be a movie poster, or the text might not be clear enough.")
            
            message_parts = ["🔍 *Image Analysis Results*\n"]
            
            # Add poster likelihood
            if poster_likelihood > 0.7:
                message_parts.append("📽️ This looks like a movie poster!")
            elif poster_likelihood > 0.4:
                message_parts.append("🎬 This might be movie-related content.")
            
            message_parts.append("\n*Potential movie titles detected:*")
            
            for i, movie in enumerate(potential_movies, 1):
                title = movie['title']
                confidence = movie['confidence']
                confidence_percent = int(confidence * 100)
                
                confidence_emoji = "🎯" if confidence > 0.8 else "🎲" if confidence > 0.5 else "❓"
                message_parts.append(f"{i}. {confidence_emoji} *{title}* ({confidence_percent}% confidence)")
            
            message_parts.append("\n💡 Tip: Use /search command with any of these titles to get movie details!")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting analysis message: {e}")
            return "❌ Error formatting analysis results."
