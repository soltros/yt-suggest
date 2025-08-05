python -c "
import json, os
from mutagen import File
from pathlib import Path

music_dir = '/path/to/your/music'
entries = []

for root, dirs, files in os.walk(music_dir):
    for file in files:
        if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg', '.wav')):
            path = os.path.join(root, file)
            try:
                audio = File(path)
                if audio and audio.tags:
                    artist = str(audio.tags.get('TPE1', audio.tags.get('ARTIST', ['']))[0] or '')
                    title = str(audio.tags.get('TIT2', audio.tags.get('TITLE', ['']))[0] or '')
                    album = str(audio.tags.get('TALB', audio.tags.get('ALBUM', ['']))[0] or '')
                    year = str(audio.tags.get('TDRC', audio.tags.get('DATE', ['']))[0] or '')[:4]
                    
                    if artist and title:
                        entries.append({
                            'artist': artist,
                            'title': title, 
                            'path': path,
                            'album': album,
                            'year': year
                        })
            except: pass

with open('music_index.json', 'w') as f:
    json.dump(entries, f, indent=2)
print(f'Generated music_index.json with {len(entries)} tracks')
"