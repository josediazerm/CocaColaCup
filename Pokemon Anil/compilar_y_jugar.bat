@echo off
echo Reempaquetando scripts...
python repack_scripts.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al reempaquetar scripts.
    pause
    exit /b 1
)
echo Lanzando el juego...
start Game.exe
