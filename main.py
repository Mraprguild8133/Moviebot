#!/usr/bin/env python3
"""
Telegram Movie Search Bot with Webhook Support
Deployable to Render.com with port 8000 configuration
"""

import logging
import asyncio
import signal
import os
from typing import Optional
from aiohttp import web
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import Config
from handlers.bot_handlers import BotHandlers

# In the MovieBot class initialization:
self.bot_handlers = BotHandlers(self.config)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('movie_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MovieBot:
    """Main bot class with webhook support for Render.com"""
    
    def __init__(self):
        self.config = Config()
        self.application: Optional[Application] = None
        self.bot_handlers: Optional[BotHandlers] = None
        self.shutdown_event = asyncio.Event()
        self.webhook_url = os.getenv('WEBHOOK_URL', '')
        self.port = int(os.getenv('PORT', '8000'))
        self.webhook_path = '/telegram_webhook'
        self.web_app = None

    async def initialize(self):
        """Initialize bot components"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN:
                raise ValueError("Telegram bot token not configured")
                
            logger.info("Initializing Telegram Movie Bot...")
            
            self.application = (
                Application.builder()
                .token(self.config.TELEGRAM_BOT_TOKEN)
                .post_init(self.post_init)
                .post_shutdown(self.post_shutdown)
                .build()
            )
            
            self.bot_handlers = BotHandlers(self.config)
            self._register_handlers()
            self._setup_signal_handlers()
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    def _register_handlers(self):
        """Register all command and message handlers"""
        if not self.application or not self.bot_handlers:
            raise RuntimeError("Application or handlers not initialized")
            
        # Command handlers
        command_handlers = [
            ("start", self.bot_handlers.start),
            ("help", self.bot_handlers.help),
            ("search", self.bot_handlers.search),
            ("status", self.bot_handlers.status),
        ]
        
        for command, callback in command_handlers:
            self.application.add_handler(CommandHandler(command, callback))
            
        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, 
                         self.bot_handlers.handle_message)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self.shutdown(s))
            )

    async def setup_webhook(self):
        """Set up webhook for Render.com"""
        if not self.webhook_url:
            logger.info("WEBHOOK_URL not set, using polling instead")
            return False
            
        await self.application.bot.set_webhook(
            url=f"{self.webhook_url}{self.webhook_path}",
            drop_pending_updates=True
        )
        logger.info(f"Webhook set up at {self.webhook_url}{self.webhook_path}")
        return True

    async def create_web_app(self):
        """Create aiohttp web application for webhook"""
        self.web_app = web.Application()
        self.web_app.router.add_post(self.webhook_path, self.handle_webhook)
        self.web_app.router.add_get('/', self.handle_root)
        return self.web_app

    async def handle_root(self, request):
        """Handle root endpoint for health checks"""
        return web.Response(text="Movie Bot is running")

    async def handle_webhook(self, request):
        """Handle incoming Telegram updates"""
        if not self.application:
            return web.Response(status=503)
            
        await self.application.update_queue.put(
            await request.json()
        )
        return web.Response()

    async def post_init(self, application: Application):
        """Post initialization callback"""
        logger.info("Bot initialization completed")

    async def post_shutdown(self, application: Application):
        """Post shutdown callback"""
        logger.info("Bot shutdown completed")

    async def error_handler(self, update: object, context):
        """Global error handler"""
        logger.error(f"Exception while handling update: {update}", exc_info=context.error)
        
    async def run(self):
        """Run the bot"""
        if not self.application:
            raise RuntimeError("Application not initialized")
            
        try:
            await self.application.initialize()
            
            # Try to set up webhook, fall back to polling if not configured
            use_webhook = await self.setup_webhook()
            
            if use_webhook:
                logger.info("Running in webhook mode")
                await self.application.start()
                
                # Start web server
                web_app = await self.create_web_app()
                runner = web.AppRunner(web_app)
                await runner.setup()
                site = web.TCPSite(runner, '0.0.0.0', self.port)
                await site.start()
                
                logger.info(f"Web server started on port {self.port}")
                await self.shutdown_event.wait()
                
                # Cleanup
                await site.stop()
                await runner.cleanup()
            else:
                logger.info("Running in polling mode")
                await self.application.run_polling()
                
        except asyncio.CancelledError:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Bot runtime error: {e}")
            raise
        finally:
            await self.cleanup()

    async def shutdown(self, signal):
        """Graceful shutdown procedure"""
        logger.info(f"Received {signal.name}, shutting down...")
        self.shutdown_event.set()

    async def cleanup(self):
        """Cleanup resources"""
        if self.application:
            if self.webhook_url:
                await self.application.bot.delete_webhook()
                logger.info("Webhook removed")
            await self.application.stop()
            await self.application.shutdown()

async def main():
    """Entry point for the bot"""
    bot = MovieBot()
    await bot.initialize()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
