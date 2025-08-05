from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import json
import subprocess
import yt_dlp
from pathlib import Path
import difflib
import os
import threading
import time
import random
from datetime import datetime
import logging
from mutagen.easyid3 import EasyID3
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration - make these environment variables in production
MUSIC_JSON_PATH = Path(os.getenv('MUSIC_JSON_PATH', '/mnt/resources/music_index.json'))
PLAYLIST_OUTPUT_DIR = Path(os.getenv('PLAYLIST_OUTPUT_DIR', '/mnt/playlists'))
VIRTUAL_MUSIC_ROOT = os.getenv('VIRTUAL_MUSIC_ROOT', '/music')
MUSIC_ROOT = Path(os.getenv('MUSIC_ROOT', '/mnt/hdd3/Music/Derriks_Music'))
DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', '/mnt/hdd3/Music/Downloads'))
MISSING_FILE = Path('missing_songs.txt')
AUTO_TAG_SCRIPT = Path('auto_tag_lastfm.py')
ORGANIZE_SCRIPT = Path('organize_music.py')

# Global variables for async operations
download_status = {'running': False, 'progress': '', 'complete': False, 'current_song': '', 'downloaded': 0, 'total': 0}
indexed_tracks = {}
search_results_cache = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_music_index():
    """Load and index the music library"""
    global indexed_tracks
    try:
        if not MUSIC_JSON_PATH.exists():
            logger.warning(f"Music index not found at {MUSIC_JSON_PATH}")
            indexed_tracks = {}
            return True
            
        with open(MUSIC_JSON_PATH, "r", encoding="utf-8") as f:
            music_data = json.load(f)
        
        indexed_tracks = {
            f"{entry['artist'].strip().lower()} - {entry['title'].strip().lower()}": entry
            for entry in music_data
            if entry.get("artist") and entry.get("title") and entry.get("path")
        }
        logger.info(f"Loaded {len(indexed_tracks)} tracks from music index")
        return True
    except Exception as e:
        logger.error(f"Error loading music index: {e}")
        return False

def find_match(artist, title):
    """Find matching track in indexed library"""
    search_key = f"{artist.lower()} - {title.lower()}"
    candidates = list(indexed_tracks.keys())
    match = difflib.get_close_matches(search_key, candidates, n=1, cutoff=0.85)
    if match:
        return indexed_tracks[match[0]]
    return None

def search_youtube(artist, title, max_results=3):
    """Search YouTube for song matches using yt-dlp"""
    search_query = f"{artist} - {title}"
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'default_search': 'ytsearch5:',  # Search top 5 results
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(search_query, download=False)
            
            if not search_results or 'entries' not in search_results:
                return []
            
            results = []
            for entry in search_results['entries'][:max_results]:
                if entry:
                    # Filter out obvious non-music results
                    title_lower = entry.get('title', '').lower()
                    if any(skip_word in title_lower for skip_word in ['tutorial', 'lesson', 'how to', 'reaction', 'review', 'cover version']):
                        continue
                    
                    result = {
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'uploader': entry.get('uploader'),
                        'duration': entry.get('duration'),
                        'view_count': entry.get('view_count'),
                        'thumbnail': entry.get('thumbnail'),
                        'webpage_url': entry.get('webpage_url'),
                        'description': entry.get('description', '')[:200] + '...' if entry.get('description') else '',
                        'upload_date': entry.get('upload_date')
                    }
                    results.append(result)
            
            return results
            
    except Exception as e:
        logger.error(f"Error searching YouTube for '{search_query}': {e}")
        return []

def process_song_list(song_list):
    """Process list of songs and search for matches"""
    songs = [line.strip() for line in song_list.strip().split('\n') if line.strip()]
    results = []
    
    for i, song in enumerate(songs):
        if " - " not in song:
            results.append({
                'original': song,
                'artist': '',
                'title': song,
                'status': 'invalid_format',
                'library_match': None,
                'youtube_results': []
            })
            continue
        
        try:
            artist, title = song.split(" - ", 1)
            artist, title = artist.strip(), title.strip()
            
            # Check if already in library
            library_match = find_match(artist, title)
            
            # Search YouTube
            youtube_results = search_youtube(artist, title)
            
            status = 'found' if youtube_results else 'not_found'
            if library_match:
                status = 'in_library'
            
            result = {
                'original': song,
                'artist': artist,
                'title': title,
                'status': status,
                'library_match': library_match,
                'youtube_results': youtube_results
            }
            results.append(result)
            
            # Small delay to avoid overwhelming YouTube
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error processing song '{song}': {e}")
            results.append({
                'original': song,
                'artist': '',
                'title': song,
                'status': 'error',
                'library_match': None,
                'youtube_results': []
            })
    
    return results

def download_selected_songs(selected_downloads):
    """Download selected songs with random intervals"""
    global download_status
    
    download_status = {
        'running': True,
        'progress': 'Starting downloads...',
        'complete': False,
        'current_song': '',
        'downloaded': 0,
        'total': len(selected_downloads)
    }
    
    # Ensure download directory exists
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failed_downloads = []
    
    for i, download_info in enumerate(selected_downloads):
        try:
            # Random delay between 0-60 seconds (except for first download)
            if i > 0:
                delay = random.randint(0, 60)
                download_status['progress'] = f'Waiting {delay} seconds before next download...'
                time.sleep(delay)
            
            artist = download_info['artist']
            title = download_info['title']
            youtube_url = download_info['youtube_url']
            
            download_status['current_song'] = f"{artist} - {title}"
            download_status['progress'] = f'Downloading: {artist} - {title}'
            
            # Safe filename for download
            safe_filename = re.sub(r'[^\w\s-]', '', f"{artist} - {title}").strip()
            safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': str(DOWNLOAD_DIR / f'{safe_filename}.%(ext)s'),
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
                'embed_metadata': True,
                'writeinfojson': False,
                'writethumbnail': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            success_count += 1
            download_status['downloaded'] = success_count
            
        except Exception as e:
            logger.error(f"Error downloading {artist} - {title}: {e}")
            failed_downloads.append(f"{artist} - {title}: {str(e)}")
        
        download_status['downloaded'] = i + 1
    
    # Run post-processing scripts if they exist
    download_status['progress'] = 'Running post-processing...'
    
    try:
        if AUTO_TAG_SCRIPT.exists():
            subprocess.run(["python3", str(AUTO_TAG_SCRIPT)], check=False)
        
        if ORGANIZE_SCRIPT.exists():
            subprocess.run(["python3", str(ORGANIZE_SCRIPT)], check=False)
    except Exception as e:
        logger.error(f"Post-processing error: {e}")
    
    # Update status
    download_status['complete'] = True
    download_status['running'] = False
    if failed_downloads:
        download_status['progress'] = f'Complete! Downloaded {success_count}/{len(selected_downloads)}. Failures: {len(failed_downloads)}'
    else:
        download_status['progress'] = f'All downloads complete! Successfully downloaded {success_count} songs.'

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/library-status')
def library_status():
    """Check music library status"""
    return jsonify({
        'indexed': len(indexed_tracks),
        'library_path': str(MUSIC_ROOT),
        'index_path': str(MUSIC_JSON_PATH),
        'playlist_dir': str(PLAYLIST_OUTPUT_DIR),
        'download_dir': str(DOWNLOAD_DIR)
    })

@app.route('/search-songs', methods=['POST'])
def search_songs():
    """Search for songs and return results for review"""
    data = request.get_json()
    song_list = data.get('song_list', '')
    
    if not song_list.strip():
        return jsonify({'error': 'No songs provided'}), 400
    
    # Process songs in background thread to avoid timeout
    search_id = str(int(time.time()))
    
    def search_thread():
        results = process_song_list(song_list)
        search_results_cache[search_id] = results
    
    thread = threading.Thread(target=search_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'search_id': search_id, 'message': 'Search started'})

@app.route('/search-results/<search_id>')
def get_search_results(search_id):
    """Get search results"""
    if search_id not in search_results_cache:
        return jsonify({'status': 'processing'})
    
    results = search_results_cache[search_id]
    return jsonify({'status': 'complete', 'results': results})

@app.route('/download-selected', methods=['POST'])
def download_selected():
    """Download selected songs"""
    global download_status
    
    if download_status['running']:
        return jsonify({'error': 'Download already in progress'}), 400
    
    data = request.get_json()
    selected_downloads = data.get('downloads', [])
    
    if not selected_downloads:
        return jsonify({'error': 'No songs selected for download'}), 400
    
    # Start download in background thread
    thread = threading.Thread(target=download_selected_songs, args=(selected_downloads,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Downloads started', 'total': len(selected_downloads)})

@app.route('/download-status')
def get_download_status():
    """Get current download status"""
    return jsonify(download_status)

@app.route('/playlists')
def list_playlists():
    """List available playlists"""
    if not PLAYLIST_OUTPUT_DIR.exists():
        return jsonify([])
    
    playlists = []
    for playlist_file in PLAYLIST_OUTPUT_DIR.glob('*.m3u'):
        stat = playlist_file.stat()
        playlists.append({
            'name': playlist_file.stem,
            'filename': playlist_file.name,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'size': stat.st_size
        })
    
    return jsonify(sorted(playlists, key=lambda x: x['created'], reverse=True))

@app.route('/playlist/<filename>')
def download_playlist(filename):
    """Download playlist file"""
    playlist_path = PLAYLIST_OUTPUT_DIR / secure_filename(filename)
    if not playlist_path.exists():
        return "Playlist not found", 404
    
    return send_file(playlist_path, as_attachment=True)

@app.route('/create-playlist', methods=['POST'])
def create_playlist():
    """Create playlist from selected songs"""
    data = request.get_json()
    playlist_name = data.get('playlist_name', f'playlist_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    selected_songs = data.get('songs', [])
    
    if not selected_songs:
        return jsonify({'error': 'No songs selected'}), 400
    
    # Sanitize playlist name
    playlist_name = secure_filename(playlist_name)
    
    # Create playlist file
    PLAYLIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    playlist_path = PLAYLIST_OUTPUT_DIR / f"{playlist_name}.m3u"
    
    with open(playlist_path, "w", encoding="utf-8") as f:
        for song in selected_songs:
            if song.get('library_path'):
                f.write(song['library_path'] + "\n")
            elif song.get('download_path'):
                f.write(song['download_path'] + "\n")
    
    return jsonify({'message': f'Playlist created: {playlist_name}.m3u', 'path': str(playlist_path)})

@app.route('/reload-index', methods=['POST'])
def reload_index():
    """Reload music index"""
    success = load_music_index()
    if success:
        return jsonify({'message': f'Index reloaded. {len(indexed_tracks)} tracks available.'})
    else:
        return jsonify({'error': 'Failed to reload music index'}), 500

# Initialize app
if __name__ == '__main__':
    if not load_music_index():
        logger.warning("Music index not loaded - some features may not work")
    
    app.run(host='0.0.0.0', port=5000, debug=True)