@echo off
if not exist stockfish.exe (
  echo ERROR: falta el archivo stockfish.exe en esta carpeta.
  echo Copia tu Stockfish a esta misma carpeta y renombralo a: stockfish.exe
  pause
  exit /b
)
echo Instalando herramientas (puede tardar un par de minutos)...
python -m pip install pyinstaller mss pillow numpy python-chess
echo.
echo Creando el ejecutable con Stockfish incluido...
python -m PyInstaller --onefile --noconsole --name AjedrezTracker --add-binary "stockfish.exe;." chess_tracker.py
echo.
echo Listo. Tu programa esta en la carpeta "dist": AjedrezTracker.exe
pause
