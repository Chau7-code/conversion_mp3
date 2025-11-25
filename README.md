# Convertisseur de Musique & Bot Discord

Ce projet permet de télécharger et convertir des musiques depuis YouTube, SoundCloud, Spotify et Instagram. Il propose deux interfaces :
1.  **Interface Web** : Une page web simple pour convertir des liens.
2.  **Bot Discord** : Un bot pour convertir des liens directement depuis un serveur Discord.

## 📋 Prérequis

*   **Python 3.8+** doit être installé sur votre machine. [Télécharger Python](https://www.python.org/downloads/)
    *   *Important : Cochez la case "Add Python to PATH" lors de l'installation.*
*   **FFmpeg** : Le programme téléchargera automatiquement FFmpeg s'il n'est pas présent sur votre système (Windows uniquement).

## 🚀 Installation Rapide

1.  Double-cliquez sur le fichier **`setup.bat`**.
    *   Cela va installer toutes les bibliothèques nécessaires (`flask`, `discord.py`, `yt-dlp`, etc.).
2.  Attendez que l'installation se termine.

## 🎮 Utilisation

Pour lancer le projet, double-cliquez sur **`start.bat`**. Un menu s'affichera :

### Option 1 : Interface Web
*   Lance le serveur web local.
*   Ouvrez votre navigateur et allez sur : `http://127.0.0.1:5000`
*   Collez une URL et cliquez sur "Convertir".

### Option 2 : Bot Discord
*   **Configuration requise avant le premier lancement :**
    1.  Ouvrez le fichier `.env` avec un éditeur de texte (Bloc-notes).
    2.  Remplacez `votre_token_ici` par le Token de votre Bot Discord.
    3.  Invitez le bot sur votre serveur.
    4.  Créez un salon textuel nommé **`musique`** (le bot n'enverra les fichiers que dans ce salon).
*   **Commandes du Bot :**
    *   `!convert <url>` : Télécharge et envoie la musique/playlist.
    *   `!convert -h` : Affiche l'aide.

## 📂 Structure du Projet

*   `app.py` : Le code de l'interface Web (Flask).
*   `bot.py` : Le code du Bot Discord.
*   `downloader.py` : Le cœur du système, gère les téléchargements pour les deux interfaces.
*   `requirements.txt` : Liste des dépendances Python.
*   `downloads/` : Dossier où sont stockés temporairement les fichiers téléchargés.

## ⚠️ Notes Importantes

*   **Playlists** : Les playlists sont téléchargées, compressées en ZIP, puis envoyées.
*   **Limites Discord** : Discord limite la taille des fichiers (8Mo ou plus avec Nitro). Si un fichier est trop gros, le bot vous avertira.
*   **Spotify** : Le téléchargement Spotify utilise `spotdl` qui peut parfois nécessiter que YouTube Music soit accessible.

## 🛠️ Dépannage

*   **"Python n'est pas reconnu..."** : Réinstallez Python et cochez bien "Add Python to PATH".
*   **Erreur FFmpeg** : Le script essaie de le télécharger automatiquement. Si cela échoue, installez FFmpeg manuellement.
