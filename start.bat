@echo off
title Lanceur Convertisseur Musique
cls

:MENU
echo ===================================================
echo    CONVERTISSEUR MUSIQUE - MENU PRINCIPAL
echo ===================================================
echo.
echo 1. Lancer l'interface Web (app.py)
echo 2. Lancer le Bot Discord (bot.py)
echo 3. Installer/Mettre a jour les dependances
echo 4. Quitter
echo.
set /p choix="Votre choix (1-4) : "

if "%choix%"=="1" goto WEB
if "%choix%"=="2" goto BOT
if "%choix%"=="3" goto INSTALL
if "%choix%"=="4" goto END

echo Choix invalide.
goto MENU

:WEB
cls
echo Lancement de l'interface Web...
echo Ouvrez votre navigateur sur http://127.0.0.1:5000
echo Appuyez sur CTRL+C pour arreter le serveur.
echo.
python app.py
pause
goto MENU

:BOT
cls
echo Lancement du Bot Discord...
echo Assurez-vous d'avoir configure votre token dans le fichier .env
echo Appuyez sur CTRL+C pour arreter le bot.
echo.
python bot.py
pause
goto MENU

:INSTALL
cls
call setup.bat
goto MENU

:END
exit
