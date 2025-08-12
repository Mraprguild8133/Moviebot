# 🎬 Telegram Movie Search Bot

A comprehensive Telegram bot that provides movie information through multiple search methods including text search, image analysis, and video recognition. Built with Python using advanced APIs for accurate movie identification and rich content delivery.

## Features

- **Text Search**: Search movies using TMDB and OMDB APIs
- **Image Analysis**: Upload movie posters for AI-powered identification
- **Video Recognition**: Analyze movie clips to identify films
- **YouTube Integration**: Find official movie trailers automatically
- **Rich Information**: Get ratings, cast, plot, release dates, and more
- **Multi-Language Support**: Works with movies in multiple languages

## APIs Used

- **Telegram Bot API**: Core bot functionality
- **TMDB (The Movie Database)**: Primary movie data source
- **OMDB (Open Movie Database)**: Additional movie metadata  
- **YouTube Data API**: Trailer search and discovery
- **Google Vision API**: Image text recognition (optional)

## Quick Start

### Prerequisites

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get a free TMDB API key from [themoviedb.org](https://www.themoviedb.org/settings/api)
3. (Optional) Get additional API keys for enhanced features

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TMDB_API_KEY=your_tmdb_api_key
OMDB_API_KEY=your_omdb_api_key (optional)
YOUTUBE_API_KEY=your_youtube_api_key (optional)
GOOGLE_VISION_API_KEY=your_google_vision_api_key (optional)
```

### Local Development

1. **Clone and install dependencies:**
```bash
git clone <repository>
cd telegram-movie-bot
pip install python-telegram-bot==20.7 aiohttp==3.12.15 Pillow==11.3.0
```

2. **Set environment variables:**
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TMDB_API_KEY="your_key_here"
```

3. **Run the bot:**
```bash
python main.py
```

### Docker Deployment

1. **Using docker-compose (recommended):**
```bash
# Create .env file with your API keys
cp .env.example .env
# Edit .env with your actual API keys
docker-compose up -d
```

2. **Using Docker directly:**
```bash
docker build -t telegram-movie-bot .
docker run -d \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  -e TMDB_API_KEY="your_key" \
  --name movie-bot \
  telegram-movie-bot
```

### Cloud Deployment

#### Render.com
1. Fork this repository
2. Connect to Render.com
3. Set environment variables in Render dashboard
4. Deploy using the included `render.yaml`

#### Railway
```bash
railway login
railway new
railway add
railway env set TELEGRAM_BOT_TOKEN="your_token"
railway env set TMDB_API_KEY="your_key"
railway up
```

#### Heroku
```bash
heroku create your-movie-bot
heroku config:set TELEGRAM_BOT_TOKEN="your_token"
heroku config:set TMDB_API_KEY="your_key"
git push heroku main
```

## Bot Commands

- `/start` - Welcome message and feature overview
- `/help` - Detailed help with API status  
- `/search <movie title>` - Search for specific movies
- Send movie titles directly for instant search
- Upload images for poster analysis
- Upload videos for content identification

## Project Structure

```
telegram-movie-bot/
├── main.py                 # Bot entry point
├── config.py              # Configuration management
├── handlers/              # Telegram bot handlers
│   └── bot_handlers.py    # Message and command handlers
├── services/              # Core services
│   ├── movie_service.py   # TMDB/OMDB integration
│   ├── image_analysis.py  # Image processing
│   ├── video_analysis.py  # Video processing
│   └── youtube_service.py # YouTube integration
├── utils/                 # Utility functions
│   └── helpers.py         # Helper functions
├── static/               # Static files
│   └── templates/        # HTML templates
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Local development setup
├── render.yaml          # Render.com deployment
└── deploy.sh            # Deployment script
```

## API Status

The bot provides graceful degradation when APIs are unavailable:

- **Required**: Telegram Bot API, TMDB API
- **Enhanced Features**: OMDB API (additional metadata)
- **Optional**: YouTube API (trailers), Google Vision API (image analysis)

## Error Handling

- Graceful API failures with user-friendly messages
- Automatic fallback when optional services are unavailable
- Comprehensive logging for debugging
- Input validation and file size limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the logs for error details
2. Verify all required API keys are set
3. Test individual API endpoints
4. Create an issue with detailed information

## Roadmap

- [ ] Advanced video analysis with OpenCV
- [ ] Multi-language movie search
- [ ] Movie recommendation system
- [ ] User favorites and watchlists
- [ ] TV show support
- [ ] Web interface for bot management