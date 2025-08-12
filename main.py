#!/usr/bin/env python3
"""
Telegram Movie Search Bot
Main entry point for the bot application
"""

import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import Config
from handlers.bot_handlers import BotHandlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the Telegram bot"""
    try:
        # Initialize configuration
        config = Config()
        
        # Create application
        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize bot handlers
        bot_handlers = BotHandlers()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", bot_handlers.start_command))
        application.add_handler(CommandHandler("help", bot_handlers.help_command))
        application.add_handler(CommandHandler("search", bot_handlers.search_command))
        
        # Add message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_text_message))
        application.add_handler(MessageHandler(filters.PHOTO, bot_handlers.handle_image))
        application.add_handler(MessageHandler(filters.VIDEO, bot_handlers.handle_video))
        application.add_handler(MessageHandler(filters.Document.ALL, bot_handlers.handle_document))
        
        # Start the bot
        logger.info("Starting Telegram Movie Bot...")
        await application.initialize()
        await application.start()
        
        # Run the bot with polling
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await application.updater.start_polling()
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        if 'application' in locals():
            await application.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
