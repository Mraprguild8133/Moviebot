# Telegram Movie Search Bot

## Overview

This is a Telegram bot that provides comprehensive movie information through multiple search methods. The bot integrates with several external APIs to offer text-based movie searches, image analysis of movie posters, video analysis of movie clips, and YouTube trailer searches. Built with Python using the python-telegram-bot library, it provides an interactive chat interface for users to discover and learn about movies through various input types.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern
The application follows a service-oriented architecture with clear separation of concerns:
- **Handler Layer**: Processes Telegram bot events and user interactions
- **Service Layer**: Encapsulates business logic for different functionalities
- **Configuration Layer**: Manages environment variables and API configurations
- **Utilities Layer**: Provides helper functions and common operations

### Bot Framework
- **Telegram Bot Integration**: Uses python-telegram-bot library with async/await patterns
- **Event-Driven Architecture**: Command handlers and message handlers process different user inputs
- **Context Management**: Leverages async context managers for resource cleanup

### Service Architecture
The bot implements multiple specialized services:
- **MovieService**: Integrates TMDB and OMDB APIs for comprehensive movie data
- **ImageAnalysisService**: Processes movie poster images using Google Vision API
- **VideoAnalysisService**: Analyzes video clips to identify movie content
- **YouTubeService**: Searches for movie trailers using YouTube Data API

### Configuration Management
- **Environment-Based Config**: All sensitive API keys stored as environment variables
- **Validation Layer**: Checks API availability and configuration completeness
- **Flexible Settings**: Configurable file size limits, supported formats, and rate limiting

### Error Handling Strategy
- **Graceful Degradation**: Bot continues functioning even if some APIs are unavailable
- **User-Friendly Messages**: Technical errors translated to helpful user feedback
- **Retry Logic**: Built-in retry mechanisms for API failures

### Media Processing
- **Multi-Format Support**: Handles various image and video formats
- **File Size Validation**: Enforces upload limits to prevent resource exhaustion
- **Async Processing**: Non-blocking file analysis using async operations

## External Dependencies

### Required APIs
- **Telegram Bot API**: Core bot functionality and message handling
- **TMDB (The Movie Database)**: Primary movie data source with comprehensive information
- **OMDB (Open Movie Database)**: Secondary movie data for enhanced coverage
- **YouTube Data API**: Trailer search and video content discovery
- **Google Vision API**: Image analysis and movie poster recognition

### Python Libraries
- **python-telegram-bot**: Telegram bot framework with async support
- **aiohttp**: Async HTTP client for API requests
- **PIL (Pillow)**: Image processing and validation
- **asyncio**: Async programming support

### Infrastructure Requirements
- **Environment Variables**: Secure storage for API keys and configuration
- **File System Access**: Temporary storage for media processing
- **Network Access**: HTTP/HTTPS connections to multiple external APIs

### Optional Features
- **Web Interface Templates**: HTML templates prepared for potential web interface
- **Rate Limiting**: Built-in request throttling for API compliance
- **Logging System**: Comprehensive logging for debugging and monitoring