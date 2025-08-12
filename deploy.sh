#!/bin/bash

# Deployment script for Telegram Movie Bot
echo "🎬 Deploying Telegram Movie Bot..."

# Check if all required environment variables are set
required_vars=("TELEGRAM_BOT_TOKEN" "TMDB_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var environment variable is not set"
        echo "Please set the required environment variables before deploying"
        exit 1
    fi
done

echo "✅ Required environment variables are set"

# Install dependencies
echo "📦 Installing dependencies..."
pip install python-telegram-bot==20.7 aiohttp==3.12.15 Pillow==11.3.0

# Optional: Check API connectivity
echo "🔍 Testing API connectivity..."
python -c "
import os
import aiohttp
import asyncio

async def test_apis():
    async with aiohttp.ClientSession() as session:
        # Test TMDB API
        try:
            async with session.get(f'https://api.themoviedb.org/3/configuration?api_key={os.getenv(\"TMDB_API_KEY\")}') as resp:
                if resp.status == 200:
                    print('✅ TMDB API: Connected')
                else:
                    print('❌ TMDB API: Failed')
        except Exception as e:
            print(f'❌ TMDB API: Error - {e}')
        
        # Test Telegram Bot API
        try:
            async with session.get(f'https://api.telegram.org/bot{os.getenv(\"TELEGRAM_BOT_TOKEN\")}/getMe') as resp:
                if resp.status == 200:
                    print('✅ Telegram Bot API: Connected')
                else:
                    print('❌ Telegram Bot API: Failed')
        except Exception as e:
            print(f'❌ Telegram Bot API: Error - {e}')

asyncio.run(test_apis())
"

echo "🚀 Starting Telegram Movie Bot..."
python main.py