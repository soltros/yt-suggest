# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/templates /app/static /mnt/playlists /mnt/downloads

# Copy application files
COPY app.py .
COPY templates/ ./templates/

# Create a non-root user
RUN useradd -m -u 1000 musicuser && \
    chown -R musicuser:musicuser /app /mnt
USER musicuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/library-status || exit 1

# Run the application
CMD ["python", "app.py"]

---

# requirements.txt
Flask==3.0.3
yt-dlp>=2025.06.30
mutagen==1.47.0
Werkzeug==3.0.4

---

# docker-compose.yml
version: '3.8'

services:
  music-playlist-generator:
    build: .
    container_name: music-playlist-generator
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - MUSIC_JSON_PATH=/mnt/resources/music_index.json
      - PLAYLIST_OUTPUT_DIR=/mnt/playlists
      - VIRTUAL_MUSIC_ROOT=/music
      - MUSIC_ROOT=/mnt/hdd3/Music/Derriks_Music
      - DOWNLOAD_DIR=/mnt/downloads
    volumes:
      # Mount your music library (read-only)
      - /path/to/your/music/library:/mnt/hdd3/Music/Derriks_Music:ro
      # Mount your music index file
      - /path/to/your/music_index.json:/mnt/resources/music_index.json:ro
      # Mount playlists directory (read-write)
      - ./playlists:/mnt/playlists
      # Mount downloads directory (read-write)
      - ./downloads:/mnt/downloads
      # Optional: Mount additional scripts
      - ./scripts:/app/scripts:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/library-status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

---

# .env.example
# Copy this to .env and modify the paths for your setup

# Path to your music index JSON file
MUSIC_JSON_PATH=/mnt/resources/music_index.json

# Directory where playlists will be saved
PLAYLIST_OUTPUT_DIR=/mnt/playlists

# Virtual music root path (used in playlist files)
VIRTUAL_MUSIC_ROOT=/music

# Actual path to your music library
MUSIC_ROOT=/mnt/hdd3/Music/Derriks_Music

# Directory where downloaded music will be saved
DOWNLOAD_DIR=/mnt/downloads

# Flask configuration
FLASK_ENV=production
SECRET_KEY=change-this-to-a-random-string

---

# setup.sh
#!/bin/bash

# Music Playlist Generator Setup Script

echo "🎵 Setting up Music Playlist Generator..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p playlists downloads scripts templates

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual paths before running docker-compose up"
fi

# Create basic music index if it doesn't exist
if [ ! -f music_index.json ]; then
    echo "📋 Creating sample music index..."
    cat > music_index.json << 'EOF'
[
    {
        "artist": "Sample Artist",
        "title": "Sample Song",
        "path": "/mnt/hdd3/Music/Derriks_Music/Sample Artist/Sample Song.mp3",
        "album": "Sample Album",
        "year": "2025"
    }
]
EOF
    echo "📝 Created sample music_index.json - replace with your actual music index"
fi

# Make scripts executable
chmod +x setup.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your actual paths"
echo "2. Update music_index.json with your music library data"
echo "3. Run: docker-compose up -d"
echo "4. Access the app at http://localhost:5000"
echo ""
echo "Optional helper scripts to create:"
echo "- auto_tag_lastfm.py (for auto-tagging downloaded music)"
echo "- organize_music.py (for organizing downloaded music)"

---

# README.md
# Music Playlist Generator

A web-based self-hostable tool for generating music playlists by searching YouTube for your song recommendations, with preview capabilities and selective downloading.

## Features

- 🔍 **Smart Search**: Uses yt-dlp to search YouTube for your song recommendations
- 🎵 **Interactive Preview**: View YouTube results with thumbnails, duration, and metadata
- ✅ **Selective Download**: Choose exactly which songs to download with checkboxes
- ⏱️ **Rate Limit Protection**: Random 0-60 second delays between downloads
- 📚 **Library Integration**: Checks existing music library to avoid duplicates
- 🎼 **Playlist Generation**: Creates .m3u playlist files
- 📱 **Responsive UI**: Works on desktop and mobile devices
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd music-playlist-generator
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure**
   - Edit `.env` file with your paths
   - Update `music_index.json` with your music library data

3. **Run**
   ```bash
   docker-compose up -d
   ```

4. **Access**
   Open http://localhost:5000 in your browser

## Configuration

### Environment Variables

- `MUSIC_JSON_PATH`: Path to your music index JSON file
- `MUSIC_ROOT`: Path to your music library
- `DOWNLOAD_DIR`: Where to save downloaded music
- `PLAYLIST_OUTPUT_DIR`: Where to save playlist files
- `VIRTUAL_MUSIC_ROOT`: Virtual path used in playlists

### Music Index Format

Your `music_index.json` should contain an array of music entries:

```json
[
    {
        "artist": "Artist Name",
        "title": "Song Title", 
        "path": "/path/to/song.mp3",
        "album": "Album Name",
        "year": "2025"
    }
]
```

## Usage

1. **Enter Songs**: Paste your song list in "Artist - Title" format
2. **Search**: Click "Search for Songs" to find YouTube matches
3. **Review**: Browse results with thumbnails and metadata
4. **Select**: Check the songs you want to download
5. **Download**: Click "Download Selected Songs" with random delays
6. **Playlist**: Generated playlists are saved automatically

## Optional Scripts

Create these Python scripts in the project directory for enhanced functionality:

- `auto_tag_lastfm.py`: Auto-tag downloaded music using Last.fm
- `organize_music.py`: Organize downloaded music into folders

## Docker Volumes

- `./playlists`: Generated playlist files
- `./downloads`: Downloaded music files  
- Your music library (read-only)
- Your music index file (read-only)

## API Endpoints

- `GET /`: Main interface
- `POST /search-songs`: Start song search
- `GET /search-results/<id>`: Get search results
- `POST /download-selected`: Start downloads
- `GET /download-status`: Download progress
- `GET /playlists`: List playlists
- `POST /reload-index`: Reload music index

## Rate Limiting

The app includes built-in rate limiting with random delays (0-60 seconds) between downloads to avoid YouTube rate limits and prevent IP blocking.

## Security Notes

- Run as non-root user in container
- Music library mounted read-only
- Configurable secret key
- Input sanitization for filenames

## Troubleshooting

- Check Docker logs: `docker-compose logs -f`
- Verify paths in `.env` file
- Ensure music index JSON is valid
- Check file permissions on mounted volumes