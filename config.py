"""
Movie Bot for Telegram with full Render.com deployment support
"""

import os
import logging
from typing import Dict, Optional
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# --- Configuration Class ---
class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        # Required configurations
        self.TELEGRAM_BOT_TOKEN: str = self._get_required_env("TELEGRAM_BOT_TOKEN")
        
        # Optional API configurations
        self.TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
        self.OMDB_API_KEY: str = os.getenv("OMDB_API_KEY", "")
        self.YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
        
        # Server configuration
        self.PORT: int = int(os.getenv("PORT", 8000))
        self.HOST: str = "0.0.0.0"
        
        # Bot settings
        self.ADMIN_IDS: list = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # Rate limiting
        self.REQUEST_TIMEOUT: int = 30
        self.MAX_RETRIES: int = 3

    def _get_required_env(self, var_name: str) -> str:
        """Get required environment variable or raise exception"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"{var_name} environment variable is required!")
        return value

    def validate_config(self) -> Dict[str, bool]:
        """Validate all configurations"""
        return {
            "telegram": bool(self.TELEGRAM_BOT_TOKEN),
            "tmdb": bool(self.TMDB_API_KEY),
            "omdb": bool(self.OMDB_API_KEY),
            "youtube": bool(self.YOUTUBE_API_KEY),
            "admin_ids": bool(self.ADMIN_IDS)
        }

# --- Bot Handlers ---
class MovieBotHandlers:
    """Contains all bot command handlers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def start(self, update: Update, context: CallbackContext) -> None:
        """Handler for /start command"""
        user = update.effective_user
        self.logger.info(f"User {user.id} started the bot")
        update.message.reply_text(
            f"🎬 Welcome {user.first_name} to Movie Bot!\n"
            "Use /help to see available commands."
        )
    
    def help(self, update: Update, context: CallbackContext) -> None:
        """Handler for /help command"""
        help_text = (
            "📚 Available Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/movie [title] - Search for a movie\n"
            "/tv [title] - Search for a TV show"
        )
        update.message.reply_text(help_text)

# --- Main Application ---
class MovieBot:
    """Main application class"""
    
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        self.handlers = MovieBotHandlers(self.config)
        
    def setup_logging(self) -> None:
        """Configure logging settings"""
        log_level = logging.DEBUG if self.config.DEBUG else logging.INFO
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=log_level
        )
        self.logger = logging.getLogger(__name__)
        
    def run(self) -> None:
        """Start the bot"""
        try:
            self.logger.info("Starting Movie Bot...")
            self.logger.info("Configuration status:\n%s", self._get_config_status())
            
            updater = Updater(token=self.config.TELEGRAM_BOT_TOKEN)
            dp = updater.dispatcher
            
            # Register handlers
            dp.add_handler(CommandHandler("start", self.handlers.start))
            dp.add_handler(CommandHandler("help", self.handlers.help))
            
            # Start the Bot
            updater.start_polling()
            self.logger.info("Bot is now running!")
            
            # Keep the process alive
            updater.idle()
            
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}")
            raise

    def _get_config_status(self) -> str:
        """Get formatted configuration status"""
        status = self.config.validate_config()
        return "\n".join(
            f"{key.upper()}: {'✅' if value else '❌'}"
            for key, value in status.items()
        )

if __name__ == "__main__":
    try:
        bot = MovieBot()
        bot.run()
    except Exception as e:
        logging.critical(f"Application failed: {e}")
        raise
