"""
Video analysis service for movie identification
"""

import asyncio
import aiohttp
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    """Service for analyzing videos to identify movie content"""
    
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
    
    async def analyze_video(self, video_data: bytes, filename: str = "video") -> Dict[str, Any]:
        """
        Analyze a video to identify potential movie content
        
        Args:
            video_data: Raw video bytes
            filename: Original filename for format detection
            
        Returns:
            Analysis results with potential movie identification
        """
        try:
            # Validate video
            validation_result = await self._validate_video(video_data, filename)
            if not validation_result['success']:
                return validation_result
            
            # Extract frames for analysis
            frames_result = await self._extract_key_frames(video_data, filename)
            if not frames_result['success']:
                return frames_result
            
            # Analyze extracted frames
            analysis_results = await self._analyze_frames(frames_result['frames'])
            
            # Process audio for additional clues (simplified)
            audio_results = await self._analyze_audio_metadata(video_data, filename)
            
            # Combine results
            combined_results = self._combine_video_analysis(analysis_results, audio_results)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            return {
                'success': False,
                'error': f"Failed to analyze video: {str(e)}",
                'potential_movies': []
            }
    
    async def _validate_video(self, video_data: bytes, filename: str) -> Dict[str, Any]:
        """Validate video file"""
        try:
            # Check file size
            if len(video_data) > self.config.MAX_FILE_SIZE:
                return {
                    'success': False,
                    'error': 'Video file too large (max 20MB)'
                }
            
            # Check file extension
            file_ext = os.path.splitext(filename.lower())[1]
            if file_ext not in self.config.SUPPORTED_VIDEO_FORMATS:
                return {
                    'success': False,
                    'error': f'Unsupported video format. Supported: {", ".join(self.config.SUPPORTED_VIDEO_FORMATS)}'
                }
            
            # Basic video validation
            if len(video_data) < 1024:  # At least 1KB
                return {
                    'success': False,
                    'error': 'Video file appears to be corrupted or too small'
                }
            
            return {
                'success': True,
                'format': file_ext,
                'size': len(video_data)
            }
            
        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return {
                'success': False,
                'error': f"Video validation failed: {str(e)}"
            }
    
    async def _extract_key_frames(self, video_data: bytes, filename: str) -> Dict[str, Any]:
        """Extract key frames from video for analysis"""
        try:
            # In a production environment, you would use OpenCV or ffmpeg
            # For this implementation, we'll simulate frame extraction
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as temp_file:
                temp_file.write(video_data)
                temp_file_path = temp_file.name
            
            try:
                # Simulate frame extraction (in reality, you'd use cv2.VideoCapture)
                # For now, return a placeholder result
                frames = []
                
                # Cleanup
                os.unlink(temp_file_path)
                
                return {
                    'success': True,
                    'frames': frames,
                    'frame_count': len(frames)
                }
                
            except Exception as e:
                # Cleanup on error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise e
                
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return {
                'success': False,
                'error': f"Frame extraction failed: {str(e)}"
            }
    
    async def _analyze_frames(self, frames: List[bytes]) -> Dict[str, Any]:
        """Analyze extracted frames for movie content"""
        try:
            if not frames:
                return {
                    'success': True,
                    'potential_movies': [],
                    'confidence': 0.0
                }
            
            # Import image analysis service for frame analysis
            from .image_analysis import ImageAnalysisService
            
            frame_results = []
            async with ImageAnalysisService(self.config) as image_service:
                for i, frame_data in enumerate(frames[:5]):  # Analyze max 5 frames
                    try:
                        frame_analysis = await image_service.analyze_image(frame_data)
                        if frame_analysis.get('success'):
                            frame_results.append({
                                'frame_index': i,
                                'analysis': frame_analysis
                            })
                    except Exception as e:
                        logger.warning(f"Error analyzing frame {i}: {e}")
                        continue
            
            # Combine frame analysis results
            combined_movies = self._combine_frame_results(frame_results)
            
            return {
                'success': True,
                'potential_movies': combined_movies,
                'frames_analyzed': len(frame_results)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing frames: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _combine_frame_results(self, frame_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine movie candidates from multiple frames"""
        movie_candidates = {}
        
        for frame_result in frame_results:
            analysis = frame_result.get('analysis', {})
            potential_movies = analysis.get('potential_movies', [])
            
            for movie in potential_movies:
                title = movie['title'].lower()
                confidence = movie['confidence']
                
                if title in movie_candidates:
                    # Increase confidence if seen in multiple frames
                    movie_candidates[title]['confidence'] = min(
                        movie_candidates[title]['confidence'] + confidence * 0.3,
                        1.0
                    )
                    movie_candidates[title]['frame_count'] += 1
                else:
                    movie_candidates[title] = {
                        'title': movie['title'],
                        'confidence': confidence,
                        'frame_count': 1,
                        'source': 'video_frames'
                    }
        
        # Convert to list and sort by confidence
        sorted_movies = sorted(
            movie_candidates.values(),
            key=lambda x: (x['confidence'], x['frame_count']),
            reverse=True
        )
        
        return sorted_movies[:3]  # Return top 3 candidates
    
    async def _analyze_audio_metadata(self, video_data: bytes, filename: str) -> Dict[str, Any]:
        """Analyze audio metadata for additional movie identification clues"""
        try:
            # In a production environment, you would use libraries like mutagen
            # to extract metadata from video files
            
            # For this implementation, we'll return a placeholder
            return {
                'success': True,
                'metadata': {},
                'audio_clues': []
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio metadata: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _combine_video_analysis(self, frame_analysis: Dict[str, Any], 
                              audio_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine frame and audio analysis results"""
        try:
            potential_movies = []
            
            # Get movies from frame analysis
            if frame_analysis.get('success'):
                potential_movies.extend(frame_analysis.get('potential_movies', []))
            
            # Add any audio-based clues
            if audio_analysis.get('success'):
                audio_clues = audio_analysis.get('audio_clues', [])
                for clue in audio_clues:
                    potential_movies.append({
                        'title': clue['title'],
                        'confidence': clue['confidence'],
                        'source': 'audio_metadata'
                    })
            
            # Remove duplicates and sort
            unique_movies = {}
            for movie in potential_movies:
                title_key = movie['title'].lower()
                if title_key not in unique_movies or movie['confidence'] > unique_movies[title_key]['confidence']:
                    unique_movies[title_key] = movie
            
            final_movies = sorted(
                unique_movies.values(),
                key=lambda x: x['confidence'],
                reverse=True
            )
            
            return {
                'success': True,
                'potential_movies': final_movies[:3],  # Top 3 results
                'analysis_methods': ['frame_analysis', 'audio_metadata'],
                'frames_analyzed': frame_analysis.get('frames_analyzed', 0)
            }
            
        except Exception as e:
            logger.error(f"Error combining video analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'potential_movies': []
            }
    
    def format_video_analysis_message(self, analysis_results: Dict[str, Any]) -> str:
        """Format video analysis results into a readable message"""
        try:
            if not analysis_results.get('success'):
                return f"❌ Video analysis failed: {analysis_results.get('error', 'Unknown error')}"
            
            potential_movies = analysis_results.get('potential_movies', [])
            frames_analyzed = analysis_results.get('frames_analyzed', 0)
            
            if not potential_movies:
                return ("🎥 *Video Analysis Complete*\n\n"
                       "No movie content detected in the video. "
                       "This might be original content or the quality might not be sufficient for identification.")
            
            message_parts = ["🎥 *Video Analysis Results*\n"]
            
            if frames_analyzed > 0:
                message_parts.append(f"📊 Analyzed {frames_analyzed} video frames")
            
            message_parts.append("\n*Potential movies identified:*")
            
            for i, movie in enumerate(potential_movies, 1):
                title = movie['title']
                confidence = movie['confidence']
                source = movie.get('source', 'unknown')
                confidence_percent = int(confidence * 100)
                
                confidence_emoji = "🎯" if confidence > 0.8 else "🎲" if confidence > 0.5 else "❓"
                source_emoji = "🎬" if source == 'video_frames' else "🎵" if source == 'audio_metadata' else "🔍"
                
                message_parts.append(
                    f"{i}. {confidence_emoji} *{title}* ({confidence_percent}% confidence) {source_emoji}"
                )
            
            message_parts.append("\n💡 Tip: Use /search command with any of these titles to get detailed movie information!")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting video analysis message: {e}")
            return "❌ Error formatting video analysis results."
