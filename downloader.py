import os
import sys
import re
import yt_dlp
from urllib.parse import urlparse
import uuid
import shutil
import subprocess
import requests
import zipfile
import time
import json

# Configuration par défaut
UPLOAD_FOLDER = 'downloads'
FFMPEG_FOLDER = 'ffmpeg_local'

def setup(upload_folder, ffmpeg_folder):
    global UPLOAD_FOLDER, FFMPEG_FOLDER
    UPLOAD_FOLDER = upload_folder
    FFMPEG_FOLDER = ffmpeg_folder
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(FFMPEG_FOLDER, exist_ok=True)

def get_local_ffmpeg_path():
    """Retourne le chemin vers FFmpeg local s'il existe"""
    if os.name == 'nt':  # Windows
        ffmpeg_exe = os.path.join(FFMPEG_FOLDER, 'ffmpeg.exe')
        ffprobe_exe = os.path.join(FFMPEG_FOLDER, 'ffprobe.exe')
    else:  # Linux/Mac
        ffmpeg_exe = os.path.join(FFMPEG_FOLDER, 'ffmpeg')
        ffprobe_exe = os.path.join(FFMPEG_FOLDER, 'ffprobe')
    
    if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
        return FFMPEG_FOLDER
    return None

def check_ffmpeg():
    """Vérifie si FFmpeg est disponible et retourne le chemin si trouvé"""
    # D'abord vérifier FFmpeg local
    local_ffmpeg = get_local_ffmpeg_path()
    if local_ffmpeg:
        return local_ffmpeg
    
    # Ensuite, essayer de trouver FFmpeg dans le PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    
    # Vérifier les emplacements communs sur Windows
    if os.name == 'nt':
        common_paths = [
            r'C:\\ffmpeg\\bin',
            r'C:\\Program Files\\ffmpeg\\bin',
            r'C:\\Program Files (x86)\\ffmpeg\\bin',
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin'),
        ]
        for path in common_paths:
            if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
                return path
    
    # Essayer de lancer ffmpeg pour vérifier s'il est dans le PATH
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      timeout=5,
                      check=True)
        return None  # FFmpeg est dans le PATH
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None

def download_ffmpeg_windows():
    """Télécharge et installe FFmpeg pour Windows automatiquement"""
    ffmpeg_exe = os.path.join(FFMPEG_FOLDER, 'ffmpeg.exe')
    ffprobe_exe = os.path.join(FFMPEG_FOLDER, 'ffprobe.exe')
    
    # Si déjà installé, retourner
    if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
        return True
    
    try:
        # URL pour télécharger FFmpeg Windows (version statique)
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        
        print("Téléchargement de FFmpeg en cours...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        zip_path = os.path.join(FFMPEG_FOLDER, 'ffmpeg.zip')
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if int(progress) % 10 == 0:  # Afficher tous les 10%
                            print(f"Téléchargement: {int(progress)}%")
        
        print("Extraction de FFmpeg...")
        # Créer un dossier temporaire pour l'extraction
        temp_extract_dir = os.path.join(FFMPEG_FOLDER, 'temp_extract')
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extraire tout dans le dossier temporaire
            zip_ref.extractall(temp_extract_dir)
        
        # Chercher ffmpeg.exe et ffprobe.exe dans les sous-dossiers
        for root, dirs, files in os.walk(temp_extract_dir):
            for file in files:
                if file == 'ffmpeg.exe' and not os.path.exists(ffmpeg_exe):
                    source = os.path.join(root, file)
                    shutil.copy2(source, ffmpeg_exe)
                elif file == 'ffprobe.exe' and not os.path.exists(ffprobe_exe):
                    source = os.path.join(root, file)
                    shutil.copy2(source, ffprobe_exe)
        
        if not (os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe)):
            print("Erreur: FFmpeg non trouvé après extraction")
            return False
            
    except Exception as e:
        print(f"Erreur lors du téléchargement de FFmpeg: {str(e)}")
        return False
    finally:
        # Nettoyer le fichier zip et le dossier temporaire
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
    
    return True

def ensure_ffmpeg():
    """S'assure que FFmpeg est disponible, le télécharge si nécessaire (synchrone)"""
    # Vérifier d'abord si FFmpeg existe
    ffmpeg_location = check_ffmpeg()
    if ffmpeg_location is not None:
        # Convertir en chemin absolu
        return os.path.abspath(ffmpeg_location)
    
    # Si on est sur Windows et FFmpeg n'est pas trouvé, le télécharger
    if os.name == 'nt':
        print("FFmpeg non trouvé. Téléchargement automatique en cours...")
        print("Cela peut prendre quelques minutes. Veuillez patienter...")
        if download_ffmpeg_windows():
            local_path = get_local_ffmpeg_path()
            if local_path:
                # Convertir en chemin absolu
                return os.path.abspath(local_path)
            else:
                raise Exception("FFmpeg installé mais introuvable. Veuillez réessayer.")
        else:
            raise Exception("Impossible de télécharger FFmpeg automatiquement. Veuillez l'installer manuellement.")
    
    raise Exception("FFmpeg n'est pas installé. Sur Linux/Mac, installez-le avec: sudo apt-get install ffmpeg ou brew install ffmpeg")

def is_youtube_url(url):
    parsed = urlparse(url)
    return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc

def is_soundcloud_url(url):
    parsed = urlparse(url)
    return 'soundcloud.com' in parsed.netloc

def is_spotify_url(url):
    parsed = urlparse(url)
    return 'spotify.com' in parsed.netloc

def is_instagram_url(url):
    parsed = urlparse(url)
    return 'instagram.com' in parsed.netloc

def is_playlist(url):
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
        return 'list=' in parsed.query
    elif 'soundcloud.com' in parsed.netloc:
        return '/sets/' in parsed.path
    elif 'spotify.com' in parsed.netloc:
        return '/playlist/' in parsed.path or '/album/' in parsed.path
    return False

def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    filename = "".join(x for x in filename if x.isprintable())
    return filename.strip()

def cleanup_temp_files(directory, base_path):
    try:
        base_name = os.path.basename(base_path)
        temp_extensions = ['.m4a', '.webm', '.mp4', '.opus', '.ogg', '.flac', '.wav', '.mkv', '.avi']
        
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if file.startswith(base_name) and any(file.endswith(ext) for ext in temp_extensions):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Impossible de supprimer {file}: {e}")
    except Exception as e:
        print(f"Erreur lors du nettoyage des fichiers temporaires: {e}")

def cleanup_all_temp_files(directory):
    try:
        temp_extensions = ['.m4a', '.webm', '.mp4', '.opus', '.ogg', '.flac', '.wav', '.mkv', '.avi', '.part', '.ytdl']
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if any(file.endswith(ext) for ext in temp_extensions) and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except PermissionError:
                    pass
                except Exception as e:
                    print(f"Impossible de supprimer {file}: {e}")
    except Exception as e:
        print(f"Erreur lors du nettoyage général: {e}")

def get_playlist_title(url, source_type):
    try:
        if source_type == 'spotify':
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                match = re.search(r'<title>(.*?)</title>', response.text)
                if match:
                    title = match.group(1)
                    title = title.replace(' | Spotify', '').replace(' - Spotify', '')
                    return title.strip()
            return "Spotify_Playlist"
        else:
            ydl_opts = {'extract_flat': True, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('title', 'Playlist')
    except Exception as e:
        print(f"Erreur titre playlist: {e}")
        return "Playlist"

def process_playlist(url, source_type, progress_id=None, progress_dict=None):
    raw_title = get_playlist_title(url, source_type)
    playlist_name = sanitize_filename(raw_title)
    if not playlist_name:
        playlist_name = "Playlist"
        
    temp_uuid = str(uuid.uuid4())
    base_temp_dir = os.path.join(UPLOAD_FOLDER, temp_uuid)
    playlist_dir = os.path.join(base_temp_dir, playlist_name)
    os.makedirs(playlist_dir, exist_ok=True)
    
    try:
        downloaded_files = []

        if source_type == 'spotify':
            try:
                import spotdl
            except ImportError:
                raise Exception("spotdl n'est pas installé.")
            
            if progress_id and progress_dict is not None:
                progress_dict[progress_id] = {
                    'percent': 0,
                    'status': 'downloading',
                    'message': f'Démarrage du téléchargement de la playlist "{playlist_name}"...'
                }

            ffmpeg_location = ensure_ffmpeg()
            if os.name == 'nt':
                ffmpeg_exe = os.path.join(ffmpeg_location, 'ffmpeg.exe')
            else:
                ffmpeg_exe = os.path.join(ffmpeg_location, 'ffmpeg')

            cmd = [
                sys.executable, '-m', 'spotdl',
                url,
                '--output', playlist_dir,
                '--format', 'mp3',
                '--bitrate', '320k',
                '--simple-tui',
            ]
            
            if os.path.exists(ffmpeg_exe):
                cmd.extend(['--ffmpeg', ffmpeg_exe])

            print(f"[Spotify Playlist] Exécution: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur spotdl: {stderr}")

            for f in os.listdir(playlist_dir):
                if f.endswith('.mp3'):
                    downloaded_files.append(os.path.join(playlist_dir, f))
            
            if not downloaded_files:
                raise Exception("Aucun fichier MP3 trouvé.")

        else:
            download_func = None
            if source_type == 'youtube':
                download_func = download_youtube
            elif source_type == 'soundcloud':
                download_func = download_soundcloud
            
            if not download_func:
                raise Exception("Type de source non supporté pour les playlists (hors Spotify)")

            ydl_opts = {'extract_flat': True, 'quiet': True}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' not in info:
                    raise Exception("Impossible de récupérer les éléments de la playlist")
                
                entries = list(info['entries'])
                total_items = len(entries)
                
                for i, entry in enumerate(entries):
                    try:
                        if progress_id and progress_dict is not None:
                            progress_dict[progress_id] = {
                                'percent': (i / total_items) * 100,
                                'status': 'downloading',
                                'message': f'Téléchargement piste {i+1}/{total_items}'
                            }
                        
                        item_url = entry.get('url') or entry.get('webpage_url')
                        if not item_url:
                            if source_type == 'youtube':
                                item_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            else:
                                continue

                        item_path, item_filename = download_func(item_url, os.path.join(playlist_dir, f"{i:03d}_{entry['title']}.mp3"))
                        downloaded_files.append(item_path)
                        
                    except Exception as e:
                        print(f"Erreur sur l'élément {i}: {e}")
                        continue
        
        if not downloaded_files:
            raise Exception("Aucun fichier n'a pu être téléchargé de la playlist")
            
        zip_filename = f"{playlist_name}_compress.zip"
        zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
        
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', base_temp_dir, playlist_name)
        shutil.rmtree(base_temp_dir)
        
        return zip_path, zip_filename.replace('.zip', '')
        
    except Exception as e:
        if os.path.exists(base_temp_dir):
            shutil.rmtree(base_temp_dir)
        raise e

def download_youtube(url, output_path, custom_filename=None, progress_id=None, progress_dict=None):
    base_path = output_path.replace('.mp3', '')
    
    try:
        ffmpeg_location = ensure_ffmpeg()
    except Exception as e:
        raise Exception(f"Erreur FFmpeg: {str(e)}")
    
    if not ffmpeg_location:
        raise Exception("FFmpeg n'est pas disponible.")
    
    def progress_hook(d):
        if progress_id and progress_dict is not None:
            status = d.get('status', '')
            if status == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                else:
                    percent = 0
                
                if speed > 0 and total_bytes > 0:
                    remaining_bytes = total_bytes - downloaded_bytes
                    eta_seconds = remaining_bytes / speed
                    eta_approx_min = max(0, int(eta_seconds) - 5)
                    eta_approx_max = max(0, int(eta_seconds) + 5)
                else:
                    eta_seconds = 0
                    eta_approx_min = 0
                    eta_approx_max = 0
                
                progress_dict[progress_id] = {
                    'percent': min(100, max(0, percent)),
                    'eta_seconds': eta_seconds,
                    'eta_approx_min': eta_approx_min,
                    'eta_approx_max': eta_approx_max,
                    'speed': speed,
                    'downloaded': downloaded_bytes,
                    'total': total_bytes
                }
            elif status == 'finished':
                progress_dict[progress_id] = {
                    'percent': 100,
                    'eta_seconds': 0,
                    'eta_approx_min': 0,
                    'eta_approx_max': 0,
                    'status': 'converting'
                }
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': base_path + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
        'ffmpeg_location': ffmpeg_location
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Impossible d'extraire les informations.")
                
                title = info.get('title', 'video')
                if custom_filename:
                    final_filename = sanitize_filename(custom_filename)
                else:
                    final_filename = sanitize_filename(title)
                
            except Exception as e:
                raise Exception(f"Erreur YouTube info: {str(e)}")
            
            ydl.download([url])
            cleanup_temp_files(os.path.dirname(output_path), base_path)
            
            if os.path.exists(output_path):
                final_path = output_path
            else:
                files = [f for f in os.listdir(os.path.dirname(output_path)) 
                        if f.startswith(os.path.basename(base_path)) and f.endswith('.mp3')]
                if files:
                    files_with_time = [(f, os.path.getmtime(os.path.join(os.path.dirname(output_path), f))) 
                                      for f in files]
                    files_with_time.sort(key=lambda x: x[1], reverse=True)
                    final_path = os.path.join(os.path.dirname(output_path), files_with_time[0][0])
                else:
                    raise Exception("Fichier MP3 non créé après conversion")
            
            return final_path, final_filename
    except Exception as e:
        raise Exception(f"Erreur lors du téléchargement YouTube: {str(e)}")

def download_soundcloud(url, output_path, custom_filename=None, progress_id=None, progress_dict=None):
    base_path = output_path.replace('.mp3', '')
    
    try:
        ffmpeg_location = ensure_ffmpeg()
    except Exception as e:
        raise Exception(f"Erreur FFmpeg: {str(e)}")
    
    if not ffmpeg_location:
        raise Exception("FFmpeg n'est pas disponible.")
    
    def progress_hook(d):
        if progress_id and progress_dict is not None:
            status = d.get('status', '')
            if status == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                else:
                    percent = 0
                
                progress_dict[progress_id] = {
                    'percent': min(100, max(0, percent)),
                    'status': 'downloading'
                }
            elif status == 'finished':
                progress_dict[progress_id] = {
                    'percent': 100,
                    'status': 'converting'
                }
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_path + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'extractor_args': {
            'soundcloud': {
                'client_id': None,
            }
        },
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
        'ffmpeg_location': ffmpeg_location
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Impossible d'extraire les informations.")
                
                title = info.get('title', 'sound')
                if custom_filename:
                    final_filename = sanitize_filename(custom_filename)
                else:
                    final_filename = sanitize_filename(title)
                
            except Exception as e:
                raise Exception(f"Erreur SoundCloud info: {str(e)}")
            
            ydl.download([url])
            cleanup_temp_files(os.path.dirname(output_path), base_path)
            
            if os.path.exists(output_path):
                final_path = output_path
            else:
                files = [f for f in os.listdir(os.path.dirname(output_path)) 
                        if f.startswith(os.path.basename(base_path)) and f.endswith('.mp3')]
                if files:
                    files_with_time = [(f, os.path.getmtime(os.path.join(os.path.dirname(output_path), f))) 
                                      for f in files]
                    files_with_time.sort(key=lambda x: x[1], reverse=True)
                    final_path = os.path.join(os.path.dirname(output_path), files_with_time[0][0])
                else:
                    raise Exception("Fichier MP3 non créé après conversion")
            
            return final_path, final_filename
    except Exception as e:
        raise Exception(f"Erreur lors du téléchargement SoundCloud: {str(e)}")

def download_spotify(url, output_path, custom_filename=None, progress_id=None, progress_dict=None):
    try:
        ffmpeg_location = ensure_ffmpeg()
    except Exception as e:
        raise Exception(f"Erreur FFmpeg: {str(e)}")
    
    if not ffmpeg_location:
        raise Exception("FFmpeg n'est pas disponible.")
    
    spotdl_installed = False
    try:
        import spotdl
        spotdl_installed = True
    except ImportError:
        spotdl_installed = False

    if not spotdl_installed:
        print("[Spotify] Module spotdl non trouvé, utilisation du fallback YouTube.")
        return download_spotify_fallback(url, output_path, custom_filename, progress_id, progress_dict)

    try:
        if progress_id and progress_dict is not None:
            progress_dict[progress_id] = {
                'percent': 10,
                'status': 'searching'
            }

        if os.name == 'nt':
            ffmpeg_exe = os.path.join(ffmpeg_location, 'ffmpeg.exe')
        else:
            ffmpeg_exe = os.path.join(ffmpeg_location, 'ffmpeg')

        base_path = output_path.replace('.mp3', '')

        cmd = [
            sys.executable, '-m', 'spotdl',
            url,
            '--output', UPLOAD_FOLDER,
            '--format', 'mp3',
            '--bitrate', '320k',
            '--simple-tui',
        ]

        if os.path.exists(ffmpeg_exe):
            cmd.extend(['--ffmpeg', ffmpeg_exe])
            
        print(f"[Spotify] Exécution de la commande: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False
        )
        
        if result.returncode != 0:
            raise Exception(f"Erreur d'exécution spotdl: {result.stderr}")

        files = [
            (f, os.path.getmtime(os.path.join(UPLOAD_FOLDER, f)))
            for f in os.listdir(UPLOAD_FOLDER)
            if f.endswith('.mp3')
        ]

        if not files:
            raise Exception("Fichier téléchargé introuvable après exécution de spotdl.")

        files.sort(key=lambda x: x[1], reverse=True)
        downloaded_file = files[0][0]
        original_path = os.path.join(UPLOAD_FOLDER, downloaded_file)

        cleanup_temp_files(UPLOAD_FOLDER, base_path)

        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(original_path, output_path)

        if custom_filename:
            final_filename = sanitize_filename(custom_filename)
        else:
            final_filename = sanitize_filename(downloaded_file.replace('.mp3', ''))

        return output_path, final_filename

    except Exception as e:
        print(f"[Spotify] Erreur avec spotdl: {e}. Utilisation du fallback YouTube.")
        try:
            return download_spotify_fallback(url, output_path, custom_filename, progress_id, progress_dict)
        except Exception as e2:
            raise Exception(
                f"Erreur lors du téléchargement Spotify avec spotdl: {e}\n"
                f"Le fallback YouTube a aussi échoué: {e2}"
            )

def download_instagram(url, output_path, custom_filename=None, progress_id=None, progress_dict=None):
    base_path = output_path.replace('.mp3', '')
    
    try:
        ffmpeg_location = ensure_ffmpeg()
    except Exception as e:
        raise Exception(f"Erreur FFmpeg: {str(e)}")
    
    if not ffmpeg_location:
        raise Exception("FFmpeg n'est pas disponible.")
    
    def progress_hook(d):
        if progress_id and progress_dict is not None:
            status = d.get('status', '')
            if status == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                else:
                    percent = 0
                
                progress_dict[progress_id] = {
                    'percent': min(100, max(0, percent)),
                    'status': 'downloading'
                }
            elif status == 'finished':
                progress_dict[progress_id] = {
                    'percent': 100,
                    'status': 'converting'
                }
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_path + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'ffmpeg_location': ffmpeg_location,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Impossible d'extraire les informations Instagram.")
                
                title = info.get('title', 'instagram_reel')
                if custom_filename:
                    final_filename = sanitize_filename(custom_filename)
                else:
                    final_filename = sanitize_filename(title)
                
            except Exception as e:
                raise Exception(f"Erreur Instagram: {str(e)}")
            
            ydl.download([url])
            cleanup_temp_files(os.path.dirname(output_path), base_path)
            
            if os.path.exists(output_path):
                final_path = output_path
            else:
                files = [f for f in os.listdir(os.path.dirname(output_path)) 
                        if f.startswith(os.path.basename(base_path)) and f.endswith('.mp3')]
                if files:
                    files_with_time = [(f, os.path.getmtime(os.path.join(os.path.dirname(output_path), f))) 
                                      for f in files]
                    files_with_time.sort(key=lambda x: x[1], reverse=True)
                    final_path = os.path.join(os.path.dirname(output_path), files_with_time[0][0])
                else:
                    raise Exception("Fichier MP3 non créé après conversion")
            
            return final_path, final_filename

    except Exception as e:
        raise Exception(f"Erreur lors du téléchargement Instagram: {str(e)}")

def download_spotify_fallback(url, output_path, custom_filename=None, progress_id=None, progress_dict=None):
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')

    if len(path_parts) < 2:
        raise Exception("URL Spotify invalide.")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise Exception(f"Impossible de charger la page Spotify (status {resp.status_code}).")

        html = resp.text
        title = None
        artist = None

        meta_desc = re.search(r'<meta\s+property="og:description"\s+content="([^\"]+)"', html, re.IGNORECASE)
        if meta_desc:
            desc = meta_desc.group(1)
            m = re.match(r'([^,]+),\s+[^,]*\s+by\s+([^,]+)', desc)
            if m:
                title = m.group(1).strip()
                artist = m.group(2).strip()

        if not title:
            meta_title = re.search(r'<meta\s+property="og:title"\s+content="([^\"]+)"', html, re.IGNORECASE)
            if meta_title:
                title_raw = meta_title.group(1).strip()
                separators = [' - ', ' – ', ' — ', ' ― ']
                for sep in separators:
                    if sep in title_raw:
                        parts = [p.strip() for p in title_raw.split(sep) if p.strip()]
                        if len(parts) >= 2:
                            artist = parts[0]
                            title = parts[-1]
                            break
                if not title:
                    title = title_raw

        if not artist:
            artist_match = re.search(r'"artists"\s*:\s*\[\s*\{[^\}]*"name"\s*:\s*"([^\"]+)"', html, re.IGNORECASE)
            if artist_match:
                artist = artist_match.group(1).strip()

        if not title or not artist:
             entity_match = re.search(r'Spotify\.Entity\s*=\s*({.*?});', html, re.DOTALL)
             if entity_match:
                 try:
                     data = json.loads(entity_match.group(1))
                     if 'name' in data:
                         title = data['name']
                     if 'artists' in data and len(data['artists']) > 0:
                         artist = data['artists'][0]['name']
                 except:
                     pass

        if not title:
            raise Exception("Impossible de trouver le titre de la musique.")

        search_query = f"{artist} - {title}" if artist else title
        print(f"[Spotify Fallback] Recherche sur YouTube: {search_query}")

        yt_search_url = f"ytsearch1:{search_query}"
        return download_youtube(yt_search_url, output_path, custom_filename, progress_id, progress_dict)

    except Exception as e:
        raise Exception(f"Erreur lors du fallback Spotify: {str(e)}")
