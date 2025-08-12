                import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class BotHandlers:
    """Handlers for Telegram bot commands and messages"""
    
    def __init__(self, config=None):
        self.config = config
        logger.info("BotHandlers initialized with config: %s", bool(config))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        await update.message.reply_text('Welcome to Movie Search Bot!')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = """
        Available commands:
        /start - Start the bot
        /help - Show this help message
        /search <movie> - Search for a movie
        /status - Check bot status
        """
        await update.message.reply_text(help_text)

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /search command."""
        query = ' '.join(context.args)
        if not query:
            await update.message.reply_text("Please specify a movie name after /search")
            return
        
        # Here you would implement your actual movie search logic
        await update.message.reply_text(f"Searching for: {query}...")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command."""
        await update.message.reply_text("Bot is running normally")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        text = update.message.text
        await update.message.reply_text(f"You said: {text}")
