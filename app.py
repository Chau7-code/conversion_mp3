from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
import sys
import os
import uuid
import threading
import time
import json
import downloader

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'downloads'
app.config['FFMPEG_FOLDER'] = 'ffmpeg_local'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max

# Configurer le module downloader
downloader.setup(app.config['UPLOAD_FOLDER'], app.config['FFMPEG_FOLDER'])

# Dictionnaire pour stocker les progressions des téléchargements
download_progress = {}

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_video():
    """Endpoint principal de conversion"""
    data = request.json
    url = data.get('url')
    custom_filename = data.get('filename')
    source_type = data.get('source_type', 'auto')
    
    if not url:
        return jsonify({'error': 'URL manquante'}), 400
    
    # Auto-détection de la source
    if source_type == 'auto':
        if downloader.is_youtube_url(url):
            source_type = 'youtube'
        elif downloader.is_soundcloud_url(url):
            source_type = 'soundcloud'
        elif downloader.is_spotify_url(url):
            source_type = 'spotify'
        elif downloader.is_instagram_url(url):
            source_type = 'instagram'
        else:
            return jsonify({'error': 'Source non reconnue. Veuillez utiliser une URL YouTube, SoundCloud, Spotify ou Instagram.'}), 400
    
    # Générer un ID unique pour suivre la progression
    progress_id = str(uuid.uuid4())
    download_progress[progress_id] = {
        'percent': 0,
        'status': 'starting'
    }
    
    def process_download():
        try:
            # Vérifier si c'est une playlist
            if downloader.is_playlist(url):
                try:
                    zip_path, zip_filename = downloader.process_playlist(url, source_type, progress_id, download_progress)
                    download_progress[progress_id] = {
                        'percent': 100,
                        'status': 'completed',
                        'file_id': os.path.basename(zip_path).replace('.zip', ''),
                        'filename': zip_filename,
                        'is_zip': True
                    }
                except Exception as e:
                    download_progress[progress_id] = {
                        'status': 'error',
                        'message': str(e)
                    }
                return

            # Traitement fichier unique
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{progress_id}.mp3')
            
            if source_type == 'youtube':
                final_path, final_filename = downloader.download_youtube(url, output_path, custom_filename, progress_id, download_progress)
            elif source_type == 'soundcloud':
                final_path, final_filename = downloader.download_soundcloud(url, output_path, custom_filename, progress_id, download_progress)
            elif source_type == 'spotify':
                final_path, final_filename = downloader.download_spotify(url, output_path, custom_filename, progress_id, download_progress)
            elif source_type == 'instagram':
                final_path, final_filename = downloader.download_instagram(url, output_path, custom_filename, progress_id, download_progress)
            else:
                raise Exception("Type de source non supporté")
            
            # Succès
            download_progress[progress_id] = {
                'percent': 100,
                'status': 'completed',
                'file_id': progress_id,
                'filename': final_filename,
                'is_zip': False
            }
            
        except Exception as e:
            print(f"Erreur de conversion: {str(e)}")
            download_progress[progress_id] = {
                'status': 'error',
                'message': str(e)
            }
            # Nettoyage en cas d'erreur
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass

    # Lancer le téléchargement en arrière-plan
    thread = threading.Thread(target=process_download)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'progress_id': progress_id})

@app.route('/download/<file_id>')
def download_file(file_id):
    """Télécharge le fichier converti"""
    mp3_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}.mp3')
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}.zip')
    
    if os.path.exists(mp3_path):
        file_path = mp3_path
        mimetype = 'audio/mpeg'
    elif os.path.exists(zip_path):
        file_path = zip_path
        mimetype = 'application/zip'
    else:
        return jsonify({'error': 'Fichier non trouvé'}), 404
    
    # Obtenir la taille du fichier pour estimer le temps de téléchargement
    file_size = os.path.getsize(file_path)
    # Estimer le temps de téléchargement (environ 1 Mo par seconde pour une connexion moyenne)
    # Ajouter 30 secondes de marge de sécurité
    estimated_download_time = max(60, (file_size / (1024 * 1024)) + 30)
    
    # Utiliser le nom du fichier passé en paramètre ou le nom du fichier sur disque
    requested_filename = request.args.get('filename')
    if requested_filename:
        # S'assurer que l'extension est correcte
        if not requested_filename.lower().endswith(('.mp3', '.zip')):
            ext = os.path.splitext(file_path)[1]
            requested_filename += ext
        download_name = requested_filename
    else:
        download_name = os.path.basename(file_path)
    
    # Supprimer le fichier après l'envoi dans un thread
    def delete_file_after_download():
        # Attendre que le téléchargement soit terminé (temps estimé + marge)
        time.sleep(int(estimated_download_time))
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Fichier supprimé après téléchargement: {file_path}")
        except Exception as e:
            print(f"Erreur lors du suppression du fichier: {e}")
    
    thread = threading.Thread(target=delete_file_after_download)
    thread.daemon = True
    thread.start()
    
    return send_file(file_path, as_attachment=True, download_name=download_name, mimetype=mimetype)

@app.route('/delete/<file_id>', methods=['POST'])
def delete_file(file_id):
    """Supprime un fichier du serveur"""
    mp3_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}.mp3')
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}.zip')
    
    try:
        deleted = False
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            deleted = True
        
        if os.path.exists(zip_path):
            os.remove(zip_path)
            deleted = True
            
        if deleted:
            return jsonify({'success': True, 'message': 'Fichier supprimé'})
        else:
            return jsonify({'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-progress/<progress_id>')
def check_progress(progress_id):
    """Endpoint simple pour vérifier le statut d'une conversion"""
    data = download_progress.get(progress_id)
    if data:
        return jsonify(data)
    else:
        return jsonify({'status': 'not_found'}), 404

@app.route('/progress/<progress_id>')
def progress(progress_id):
    """
    Flux SSE pour suivre la progression d'un téléchargement / conversion.
    """
    def generate():
        last_state = None
        max_wait = 300  # Maximum 5 minutes d'attente (300 * 0.5s)
        wait_count = 0

        while wait_count < max_wait:
            data = download_progress.get(progress_id)

            if not data:
                wait_count += 1
                time.sleep(0.5)
                continue

            # Comparer les états de manière plus fiable
            current_state_key = json.dumps(data, sort_keys=True)
            last_state_key = json.dumps(last_state, sort_keys=True) if last_state else None

            if current_state_key != last_state_key:
                # on envoie les données au client
                yield f"data: {json.dumps(data)}\n\n"
                last_state = data.copy() if isinstance(data, dict) else data

            # si terminé ou erreur, on envoie un dernier message et on sort
            if data.get('status') in ('completed', 'error'):
                # S'assurer que le dernier message est bien envoyé
                yield f"data: {json.dumps(data)}\n\n"
                break

            time.sleep(0.5)
            wait_count += 1

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)