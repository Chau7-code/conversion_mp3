import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import downloader
import asyncio
import shutil

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuration
UPLOAD_FOLDER = 'downloads_bot'
FFMPEG_FOLDER = 'ffmpeg_local'
downloader.setup(UPLOAD_FOLDER, FFMPEG_FOLDER)

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord!')

@bot.command(name='convert')
async def convert(ctx, url: str):
    # Vérifier si l'utilisateur demande de l'aide
    if url in ['-h', '-help', '--help']:
        embed = discord.Embed(
            title="🤖 Présentation du Bot Musique",
            description="Ce bot vous permet de télécharger et convertir des musiques depuis plusieurs plateformes directement sur Discord.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🛠️ Fonctionnalités",
            value=(
                "• **Téléchargement direct** : Convertit les liens en fichiers MP3.\n"
                "• **Support Playlists** : Télécharge les playlists complètes et les envoie sous forme de fichier ZIP.\n"
                "• **Organisation** : Envoie automatiquement les fichiers dans le salon `#musique`."
            ),
            inline=False
        )
        
        embed.add_field(
            name="🌍 Plateformes Supportées",
            value=(
                "• **YouTube** (Vidéos & Playlists)\n"
                "• **SoundCloud** (Tracks & Sets)\n"
                "• **Spotify** (Tracks & Playlists)\n"
                "• **Instagram** (Reels)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Utilisation",
            value="`!convert <url>`",
            inline=False
        )
        
        embed.set_footer(text="Profitez de votre musique ! 🎵")
        await ctx.send(embed=embed)
        return

    # Vérifier si on est dans le bon channel ou rediriger
    target_channel_name = "musique"
    target_channel = discord.utils.get(ctx.guild.channels, name=target_channel_name)
    
    if not target_channel:
        await ctx.send(f"Le salon '{target_channel_name}' n'existe pas. Veuillez le créer.")
        return

    # Message de confirmation
    status_msg = await ctx.send(f"Traitement de l'URL : {url} ...")

    # Dictionnaire de progression (non utilisé pour l'affichage temps réel ici pour simplifier)
    progress_dict = {}
    progress_id = "bot_task"

    try:
        # Exécuter le téléchargement dans un thread séparé pour ne pas bloquer le bot
        loop = asyncio.get_event_loop()
        
        # Déterminer la source
        source_type = 'auto'
        if downloader.is_youtube_url(url):
            source_type = 'youtube'
        elif downloader.is_soundcloud_url(url):
            source_type = 'soundcloud'
        elif downloader.is_spotify_url(url):
            source_type = 'spotify'
        elif downloader.is_instagram_url(url):
            source_type = 'instagram'
        else:
            await status_msg.edit(content="URL non supportée.")
            return

        await status_msg.edit(content=f"Téléchargement en cours ({source_type})...")

        if downloader.is_playlist(url):
            # Playlist
            zip_path, zip_filename = await loop.run_in_executor(
                None, 
                lambda: downloader.process_playlist(url, source_type, progress_id, progress_dict)
            )
            file_path = zip_path
            filename = zip_filename + ".zip"
        else:
            # Fichier unique
            output_path = os.path.join(UPLOAD_FOLDER, f"{progress_id}.mp3")
            
            if source_type == 'youtube':
                final_path, final_filename = await loop.run_in_executor(None, lambda: downloader.download_youtube(url, output_path, None, progress_id, progress_dict))
            elif source_type == 'soundcloud':
                final_path, final_filename = await loop.run_in_executor(None, lambda: downloader.download_soundcloud(url, output_path, None, progress_id, progress_dict))
            elif source_type == 'spotify':
                final_path, final_filename = await loop.run_in_executor(None, lambda: downloader.download_spotify(url, output_path, None, progress_id, progress_dict))
            elif source_type == 'instagram':
                final_path, final_filename = await loop.run_in_executor(None, lambda: downloader.download_instagram(url, output_path, None, progress_id, progress_dict))
            
            file_path = final_path
            filename = final_filename + ".mp3"

        # Vérifier la taille du fichier (limite Discord ~8MB sans nitro, on met une limite safe à 25MB pour les serveurs boostés ou on prévient)
        file_size = os.path.getsize(file_path)
        limit_bytes = 25 * 1024 * 1024 # 25 MB
        
        if file_size > limit_bytes:
            await status_msg.edit(content=f"Le fichier est trop volumineux ({file_size / (1024*1024):.2f} MB) pour être envoyé sur Discord.")
        else:
            await status_msg.edit(content="Envoi du fichier dans le salon musique...")
            await target_channel.send(f"Conversion demandée par {ctx.author.mention}", file=discord.File(file_path, filename=filename))
            await status_msg.edit(content="Fichier envoyé avec succès !")

        # Nettoyage
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status_msg.edit(content=f"Erreur lors de la conversion : {str(e)}")
        # Nettoyage en cas d'erreur
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not TOKEN:
        print("Erreur: Le token Discord n'est pas défini dans le fichier .env")
    else:
        bot.run(TOKEN)
