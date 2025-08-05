# YT-Suggest 🎵

A self-hostable web application that transforms your music recommendations into organized playlists by intelligently searching YouTube, providing interactive previews, and enabling selective downloads with built-in rate limiting.

![YT-Suggest Interface](https://img.shields.io/badge/Interface-Web%20Based-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11+-orange) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 🔍 **Smart YouTube Search**
- Uses yt-dlp to search YouTube for your song recommendations
- Displays results with thumbnails, metadata, view counts, and durations
- Filters out obvious non-music content (tutorials, reactions, etc.)

### 🎵 **Interactive Preview & Selection**
- Visual preview of each YouTube result with thumbnails
- Checkbox selection system - choose exactly which versions to download
- Bulk selection controls (Select All, Select None, Select Found Only)

### 📥 **Intelligent Download Management**
- **Built-in rate limiting**: Random 0-60 second delays between downloads
- Real-time progress tracking with current song display
- Automatic post-processing with custom scripts
- Respects YouTube's terms of service

### 📚 **Library Integration**
- Checks existing music library to avoid duplicates
- Loads music index from JSON file for fast lookups
- Shows which songs are already in your collection

### 🎼 **Playlist Generation**
- Creates standard .m3u playlist files
- Supports both library tracks and downloaded content
- Easy playlist management and download

### 🐳 **Self-Hostable**
- Complete Docker setup with docker-compose
- Runs entirely on your own infrastructure
- No external dependencies or cloud services required

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.x (for secret key generation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo>
   cd yt-suggest
   ```

2. **Generate a secret key**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Create required directories**
   ```bash
   mkdir -p playlists downloads templates scripts
   ```

4. **Update docker-compose.yml**
   - Replace `/path/to/your/music/library` with your actual music directory
   - Replace `/path/to/your/music_index.json` with your music index file path
   - Update the `SECRET_KEY` with your generated key

5. **Start the application**
   ```bash
   docker-compose up -d
   ```

6. **Access YT-Suggest**
   Open http://localhost:5000 in your browser

## 📁 Required Files

### Core Application Files
```
yt-suggest/
├── app.py                    # Flask backend application
├── templates/
│   └── index.html           # Web interface
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Deployment configuration
└── README.md               # This file
```

### Configuration Files (Create these)
```
├── playlists/              # Generated playlists (auto-created)
├── downloads/              # Downloaded music (auto-created)
└── scripts/                # Optional post-processing scripts
    ├── auto_tag_lastfm.py  # Auto-tag downloaded music
    └── organize_music.py   # Organize downloaded files
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MUSIC_JSON_PATH` | Path to your music index JSON file | `/mnt/resources/music_index.json` |
| `MUSIC_ROOT` | Path to your music library | `/mnt/hdd3/Music/Derriks_Music` |
| `DOWNLOAD_DIR` | Where to save downloaded music | `/mnt/downloads` |
| `PLAYLIST_OUTPUT_DIR` | Where to save playlist files | `/mnt/playlists` |
| `VIRTUAL_MUSIC_ROOT` | Virtual path used in playlists | `/music` |
| `SECRET_KEY` | Flask session security key | Required |

### Music Index Format

Create a `music_index.json` file with your existing music library:

```json
[
    {
        "artist": "The Beatles",
        "title": "Hey Jude",
        "path": "/path/to/music/The Beatles/Hey Jude.mp3",
        "album": "The Beatles 1967-1970",
        "year": "1968"
    },
    {
        "artist": "Led Zeppelin", 
        "title": "Stairway to Heaven",
        "path": "/path/to/music/Led Zeppelin/Stairway to Heaven.mp3",
        "album": "Led Zeppelin IV",
        "year": "1971"
    }
]
```

## 🎯 How to Use

### 1. **Enter Song Recommendations**
Paste your song list in the format:
```
Artist - Song Title
The Beatles - Hey Jude
Led Zeppelin - Stairway to Heaven
Pink Floyd - Comfortably Numb
```

### 2. **Search & Review**
- Click "Search for Songs" to find YouTube matches
- Browse results with thumbnails and metadata
- Review view counts, upload dates, and durations

### 3. **Select Downloads**
- Check the specific versions you want to download
- Use bulk selection controls for efficiency
- Songs already in your library are highlighted

### 4. **Download with Rate Limiting**
- Click "Download Selected Songs" 
- System automatically adds 0-60 second random delays
- Monitor real-time progress with current song display

### 5. **Enjoy Your Playlists**
- Generated .m3u playlists are saved automatically
- Download playlists from the web interface
- Use with any media player that supports .m3u files

## 🔒 Rate Limiting & Ethics

YT-Suggest includes built-in protections:
- **Random delays**: 0-60 seconds between each download
- **Respectful searching**: Small delays between search requests
- **Quality filtering**: Removes obvious non-music content
- **User control**: You choose exactly what to download

This ensures compliance with YouTube's terms of service and prevents IP blocking.

## 🛠️ Optional Enhancements

### Post-Processing Scripts

Create these optional scripts in the `scripts/` folder:

**`auto_tag_lastfm.py`** - Auto-tag downloaded music using Last.fm API
**`organize_music.py`** - Organize downloaded files into Artist/Album folders

These scripts will run automatically after downloads complete.

### Custom Docker Build

To customize the Docker image:
```bash
docker build -t yt-suggest .
docker run -p 5000:5000 -v /your/paths:/mnt/paths yt-suggest
```

## 🔧 API Endpoints

YT-Suggest exposes these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/search-songs` | POST | Start YouTube search for song list |
| `/search-results/<id>` | GET | Get search results by ID |
| `/download-selected` | POST | Begin downloading selected songs |
| `/download-status` | GET | Get current download progress |
| `/playlists` | GET | List available playlists |
| `/playlist/<filename>` | GET | Download playlist file |
| `/library-status` | GET | Get music library statistics |
| `/reload-index` | POST | Reload music index from file |

## 🐛 Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker-compose logs -f music-playlist-generator
```

**Can't find music index:**
- Verify the path in docker-compose.yml
- Ensure the JSON file is valid
- Check file permissions

**Downloads failing:**
- Verify yt-dlp is up to date
- Check internet connectivity
- Ensure download directory is writable

**Port conflicts:**
Change the host port in docker-compose.yml:
```yaml
ports:
  - "8080:5000"  # Access via localhost:8080
```

### Performance Tips

- Use SSD storage for download directory
- Ensure adequate disk space for downloads
- Monitor system resources during bulk downloads

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⭐ Star History

If you find YT-Suggest useful, please consider giving it a star!

---

**YT-Suggest** - Transform your music recommendations into curated playlists with intelligent YouTube integration.