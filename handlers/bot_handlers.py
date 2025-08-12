"""
Telegram bot handlers for processing different types of messages and commands
"""

import logging
import asyncio
from typing import Dict, Any
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction
from config import Config
from services.movie_service import MovieService
from services.image_analysis import ImageAnalysisService
from services.video_analysis import VideoAnalysisService
from services.youtube_service import YouTubeService
from utils.helpers import format_error_message, validate_file_size

logger = logging.getLogger(__name__)

class BotHandlers:
    """Handler class for all bot commands and messages"""
    
    def __init__(self):
        self.config = Config()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        try:
            user = update.effective_user
            welcome_message = (
                f"🎬 *Welcome to Movie Search Bot, {user.first_name}!*\n\n"
                "I can help you find movie information in multiple ways:\n\n"
                "📝 *Text Search:* Send me a movie title or use `/search Movie Name`\n"
                "🖼️ *Image Analysis:* Send me a movie poster image\n"
                "🎥 *Video Analysis:* Send me a movie clip or trailer\n"
                "🎞️ *Trailer Search:* Get YouTube trailers for any movie\n\n"
                "*Available Commands:*\n"
                "• `/search <movie name>` - Search for a specific movie\n"
                "• `/help` - Show this help message\n\n"
                "Just send me any movie-related content and I'll do my best to identify it! 🍿"
            )
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                "❌ Sorry, something went wrong. Please try again."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        try:
            api_status = self.config.get_api_status()
            
            help_message = (
                "🎬 *Movie Search Bot Help*\n\n"
                "*How to use:*\n"
                "1️⃣ **Text Search:** Type a movie name or use `/search Movie Title`\n"
                "2️⃣ **Image Upload:** Send a movie poster image\n"
                "3️⃣ **Video Upload:** Send a movie clip or trailer\n\n"
                "*Features:*\n"
                "🔍 Search movies using TMDB and OMDB databases\n"
                "🖼️ Analyze images to identify movie posters\n"
                "🎥 Analyze videos to identify movie content\n"
                "🎞️ Find YouTube trailers for movies\n"
                "⭐ Get ratings, cast, plot, and release information\n\n"
                "*Commands:*\n"
                "• `/start` - Welcome message\n"
                "• `/search <title>` - Search for a specific movie\n"
                "• `/help` - Show this help message\n\n"
                f"*API Status:*\n{api_status}\n\n"
                "💡 *Tips:*\n"
                "• Use clear, high-quality images for better recognition\n"
                "• Videos should be under 20MB\n"
                "• Try different movie titles if no results are found"
            )
            
            await update.message.reply_text(
                help_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text(
                "❌ Sorry, something went wrong. Please try again."
            )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /search command"""
        try:
            # Extract search query from command arguments
            if not context.args:
                await update.message.reply_text(
                    "🔍 Please provide a movie title to search.\n"
                    "Example: `/search The Matrix`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            query = " ".join(context.args)
            await self._search_and_reply(update, query)
            
        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await update.message.reply_text(
                format_error_message("Failed to process search command")
            )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle plain text messages (treated as movie search queries)"""
        try:
            query = update.message.text.strip()
            
            if len(query) < 2:
                await update.message.reply_text(
                    "🔍 Please send a movie title to search.\n"
                    "Or use `/help` to see all available options."
                )
                return
            
            await self._search_and_reply(update, query)
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text(
                format_error_message("Failed to process your message")
            )
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle image uploads for movie poster analysis"""
        try:
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            # Get the largest photo
            photo = update.message.photo[-1]
            
            # Check file size
            if not validate_file_size(photo.file_size, self.config.MAX_FILE_SIZE):
                await update.message.reply_text(
                    f"❌ Image too large. Maximum size is {self.config.MAX_FILE_SIZE // (1024*1024)}MB."
                )
                return
            
            # Download image
            file = await context.bot.get_file(photo.file_id)
            image_data = await file.download_as_bytearray()
            
            # Analyze image
            async with ImageAnalysisService(self.config) as image_service:
                await update.message.reply_chat_action(ChatAction.TYPING)
                analysis_result = await image_service.analyze_image(bytes(image_data))
                
                # Send analysis results
                analysis_message = image_service.format_analysis_message(analysis_result)
                await update.message.reply_text(
                    analysis_message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                # If movies were detected, search for details
                potential_movies = analysis_result.get('potential_movies', [])
                if potential_movies:
                    best_match = potential_movies[0]
                    if best_match['confidence'] > 0.6:
                        await update.message.reply_text("🔍 Searching for movie details...")
                        await self._search_and_reply(update, best_match['title'])
                        
        except Exception as e:
            logger.error(f"Error handling image: {e}")
            await update.message.reply_text(
                format_error_message("Failed to analyze the image")
            )
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle video uploads for movie content analysis"""
        try:
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            video = update.message.video
            
            # Check file size
            if not validate_file_size(video.file_size, self.config.MAX_FILE_SIZE):
                await update.message.reply_text(
                    f"❌ Video too large. Maximum size is {self.config.MAX_FILE_SIZE // (1024*1024)}MB."
                )
                return
            
            # Download video
            file = await context.bot.get_file(video.file_id)
            video_data = await file.download_as_bytearray()
            
            # Analyze video
            async with VideoAnalysisService(self.config) as video_service:
                await update.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
                analysis_result = await video_service.analyze_video(
                    bytes(video_data), 
                    video.file_name or "video.mp4"
                )
                
                # Send analysis results
                analysis_message = video_service.format_video_analysis_message(analysis_result)
                await update.message.reply_text(
                    analysis_message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                # If movies were detected, search for details
                potential_movies = analysis_result.get('potential_movies', [])
                if potential_movies:
                    best_match = potential_movies[0]
                    if best_match['confidence'] > 0.6:
                        await update.message.reply_text("🔍 Searching for movie details...")
                        await self._search_and_reply(update, best_match['title'])
                        
        except Exception as e:
            logger.error(f"Error handling video: {e}")
            await update.message.reply_text(
                format_error_message("Failed to analyze the video")
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle document uploads (images/videos sent as files)"""
        try:
            document = update.message.document
            
            if not document.file_name:
                await update.message.reply_text(
                    "❌ Unable to determine file type. Please send as photo or video."
                )
                return
            
            # Check file extension
            file_ext = document.file_name.lower().split('.')[-1]
            
            if f".{file_ext}" in self.config.SUPPORTED_IMAGE_FORMATS:
                # Handle as image
                await self._handle_document_as_image(update, context, document)
            elif f".{file_ext}" in self.config.SUPPORTED_VIDEO_FORMATS:
                # Handle as video
                await self._handle_document_as_video(update, context, document)
            else:
                await update.message.reply_text(
                    f"❌ Unsupported file format: {file_ext}\n"
                    f"Supported images: {', '.join(self.config.SUPPORTED_IMAGE_FORMATS)}\n"
                    f"Supported videos: {', '.join(self.config.SUPPORTED_VIDEO_FORMATS)}"
                )
                
        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await update.message.reply_text(
                format_error_message("Failed to process the file")
            )
    
    async def _handle_document_as_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, document) -> None:
        """Handle document as image"""
        # Check file size
        if not validate_file_size(document.file_size, self.config.MAX_FILE_SIZE):
            await update.message.reply_text(
                f"❌ File too large. Maximum size is {self.config.MAX_FILE_SIZE // (1024*1024)}MB."
            )
            return
        
        # Download and process as image
        file = await context.bot.get_file(document.file_id)
        image_data = await file.download_as_bytearray()
        
        async with ImageAnalysisService(self.config) as image_service:
            await update.message.reply_chat_action(ChatAction.TYPING)
            analysis_result = await image_service.analyze_image(bytes(image_data))
            
            analysis_message = image_service.format_analysis_message(analysis_result)
            await update.message.reply_text(
                analysis_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    
    async def _handle_document_as_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, document) -> None:
        """Handle document as video"""
        # Check file size
        if not validate_file_size(document.file_size, self.config.MAX_FILE_SIZE):
            await update.message.reply_text(
                f"❌ File too large. Maximum size is {self.config.MAX_FILE_SIZE // (1024*1024)}MB."
            )
            return
        
        # Download and process as video
        file = await context.bot.get_file(document.file_id)
        video_data = await file.download_as_bytearray()
        
        async with VideoAnalysisService(self.config) as video_service:
            await update.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
            analysis_result = await video_service.analyze_video(
                bytes(video_data), 
                document.file_name
            )
            
            analysis_message = video_service.format_video_analysis_message(analysis_result)
            await update.message.reply_text(
                analysis_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    
    async def _search_and_reply(self, update: Update, query: str) -> None:
        """Search for movie and send results"""
        try:
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            # Search for movies
            async with MovieService(self.config) as movie_service:
                search_results = await movie_service.search_movies(query)
                
                if not search_results.get('success'):
                    await update.message.reply_text(
                        f"❌ Search failed: {search_results.get('error', 'Unknown error')}"
                    )
                    return
                
                movies = search_results.get('movies', [])
                
                if not movies:
                    await update.message.reply_text(
                        f"🔍 No movies found for '{query}'\n\n"
                        "💡 Try:\n"
                        "• Different spelling or title\n"
                        "• Original title if it's a foreign film\n"
                        "• Year if there are multiple versions"
                    )
                    return
                
                # Send results for each movie
                for i, movie in enumerate(movies[:3], 1):  # Limit to 3 results
                    movie_message = movie_service.format_movie_message(movie)
                    
                    # Send movie poster if available
                    poster_url = movie.get('poster_url')
                    if poster_url:
                        try:
                            await update.message.reply_photo(
                                photo=poster_url,
                                caption=movie_message,
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except Exception as poster_error:
                            logger.warning(f"Failed to send poster: {poster_error}")
                            await update.message.reply_text(
                                movie_message,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True
                            )
                    else:
                        await update.message.reply_text(
                            movie_message,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                    
                    # Find and send trailer for the first movie
                    if i == 1:
                        await self._find_and_send_trailer(update, movie)
                
                if len(movies) > 3:
                    await update.message.reply_text(
                        f"📊 Found {len(movies)} total results. Showing top 3."
                    )
                    
        except Exception as e:
            logger.error(f"Error in search and reply: {e}")
            await update.message.reply_text(
                format_error_message("Failed to search for movies")
            )
    
    async def _find_and_send_trailer(self, update: Update, movie: Dict[str, Any]) -> None:
        """Find and send YouTube trailer for a movie"""
        try:
            movie_title = movie.get('title')
            release_date = movie.get('release_date')
            release_year = release_date[:4] if release_date and len(release_date) >= 4 else None
            
            async with YouTubeService(self.config) as youtube_service:
                trailer_results = await youtube_service.find_trailer(movie_title, release_year)
                
                if trailer_results.get('success') and trailer_results.get('trailers'):
                    trailer_message = youtube_service.format_trailer_message(
                        trailer_results['trailers'], 
                        movie_title
                    )
                    await update.message.reply_text(
                        trailer_message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=False
                    )
                else:
                    await update.message.reply_text(
                        f"🎬 No trailers found for '{movie_title}'"
                    )
                    
        except Exception as e:
            logger.error(f"Error finding trailer: {e}")
            # Don't send error message for trailer failures as it's supplementary
            pass
