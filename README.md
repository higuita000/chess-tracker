Chess Tracker

A Windows tool that reads a chess board on your screen, follows the game move by move, and shows you the best move using Stockfish. It works with any chess website or app because it doesn't connect to any of them: it just looks at your screen.

It tells you which piece to move and where (Knight g1 → f3) and also highlights both squares directly on the board. The highlight doesn't interfere with your mouse: you can click and drag pieces as usual.

Note: the program's interface (window text, buttons, messages) is currently in Spanish. This README gives the English meaning of each label where it matters.

Responsible use

This tool is meant for practicing against bots, analyzing games and learning. Using it in games against real people on sites like Chess.com or Lichess breaks their rules, gets detected, and ends in a ban. Use it at your own risk.

What's in this repository
File	Purpose
chess_tracker.py	The program
crear_exe.bat	Builds the program into a single .exe with one click
README.md	This file

Stockfish is not included. You have to download it yourself (see step 2).

Requirements
Windows 10 (version 2004 or newer) or Windows 11.
Python 3.9 or newer. During installation, check "Add Python to PATH". If you skip it, nothing below will work.
An 8x8 chess board visible on your screen.
Installation
1. Download this repository

Click the green Code → Download ZIP button and extract it into a folder (for example C:\ChessTracker).

2. Download Stockfish
Go to stockfishchess.org/download.
Download the Windows version. If you can choose by processor, the x86-64 or universal build works on almost every machine.
Extract the downloaded .zip. Inside there's a folder with a .exe file with a long name, something like stockfish-windows-x86-64-universal.exe.
3. Rename it and copy it to the project folder
Copy that .exe into the same folder as chess_tracker.py and crear_exe.bat.
Rename it to stockfish.exe (exactly like that, in lowercase). The build script looks for that name.

Your folder should look like this:

ChessTracker/
├── chess_tracker.py
├── crear_exe.bat
├── README.md
└── stockfish.exe
4. Build the executable

Double-click crear_exe.bat. It installs the dependencies and builds the program, which takes a few minutes. When it's done, your program will be in the dist folder:

dist/AjedrezTracker.exe

That file already contains Stockfish inside. You can copy it anywhere (your desktop, for example) and delete the rest.

The build script's messages are also in Spanish. If it says ERROR: falta el archivo stockfish.exe, it means stockfish.exe is missing from the folder.

Usage
Open a game on your chess website or app and leave it in the starting position, with the whole board visible.
Double-click AjedrezTracker.exe.
A dialog asks whether you have the white pieces at the bottom of the screen (¿Tienes las piezas BLANCAS abajo...?). Answer according to your board.
With the screen frozen, drag the mouse over the board, from corner to corner.
The program window appears. With the game still in the starting position, click Calibrar (Calibrate). If it says Calibrado (Calibrated), it's working.
Play. Whenever it's your turn, you'll see the best move in the window and highlighted on the board:
Yellow: the square of the piece you should move.
Green: the square to move it to.
Blue arrow: the path.

When it's the opponent's turn, the window says Turno del rival (Opponent's turn) and shows nothing else. Your color is taken from your answer in step 3 (the side at the bottom).

Window status indicator
Dot	Meaning
Gray	Not calibrated yet, or waiting
Orange	Stockfish is thinking (Pensando…)
Green	Move ready (Mejor jugada, best move)
Red	Something failed (the message says what)

Piece names are shown in Spanish: Peón (Pawn), Caballo (Knight), Alfil (Bishop), Torre (Rook), Dama (Queen), Rey (King). If there's a forced mate, the window shows it (for example Mate en 3, mate in 3). Otherwise it simply shows the best move the engine finds.

Tips for best results
Always start from the initial position. During calibration the program learns what each piece looks like in your theme, and it needs to see all 32 pieces in place. It can't pick up a game that's already in progress.
Use a flat-colored board. Textured themes (grass, grainy wood, marble) can make it see pieces on empty squares. The plain green and brown boards on Chess.com or Lichess work well.
Don't cover the board with the program window. By default it appears in the top-right corner, but you can move it.
Select the board tightly, without including frames or player names. A couple of pixels of error don't matter.
If you change website, theme or board size, reopen the program and calibrate again.
Advanced options

If you'd rather not use the .exe, you can run the script directly:

pip install mss pillow numpy python-chess
python chess_tracker.py --engine "C:\path\to\stockfish.exe"
Option	What it does
--engine PATH	Path to Stockfish (not needed if you use the .exe with Stockfish bundled)
--negras-abajo	Use it if Black is at the bottom of your screen
--tiempo N	Seconds Stockfish thinks per move (default 0.5). More time means better moves but slower answers
--ambos	Also show suggestions on the opponent's turn

If you run it with no options, it asks everything through dialog windows and remembers the Stockfish path in a config.json file. Delete that file if you want it to ask for Stockfish again.

Troubleshooting

"python is not recognized as a command" Python isn't in your PATH. Reinstall it and check "Add Python to PATH".

"ERROR: falta el archivo stockfish.exe en esta carpeta" crear_exe.bat can't find Stockfish. Make sure you copied it into the same folder and that it's named exactly stockfish.exe.

Windows says "Windows protected your PC" or your antivirus blocks the .exe This is normal for unsigned programs built with PyInstaller. Choose More info → Run anyway, or add an exception. Since you build it yourself from this code, you can inspect exactly what it contains.

"Falló la calibración" (Calibration failed) The message lists the squares it couldn't understand. It's almost always one of these:

The game is no longer in the starting position.
You picked the wrong orientation (white or black at the bottom).
Your selection doesn't cover the whole board.
The board theme has textures. Switch to a flat-colored one.

The program window covers part of the board Move it to the side before calibrating.

The board looks offset when selecting it This happens with Windows display scaling (125%, 150%). Current versions already handle it, so make sure you rebuilt the .exe with the latest code.

The highlight shows as "outline mode" (Resaltado en modo contorno) Your Windows version doesn't allow hiding the highlight layer from screen captures, so the program draws only the border of each square to avoid confusing itself. This is normal on some versions.

It stops detecting my moves Usually something covered part of the board during a move, or the website's animation hadn't finished. Since the program follows the game from the start, it can't recover mid-game: start a new game and calibrate again.

How it works
It captures the board area you selected.
During calibration it learns what each piece looks like in your theme, using the starting position as a reference.
Each time the screen changes it recognizes the pieces and compares them against every legal move (using the python-chess library) to work out what was played.
It asks Stockfish for the best move in the current position and shows it.
Limitations
8x8 boards and standard chess only.
Windows only (the transparent highlight relies on Windows features).
It only tracks games that start from the initial position.
It can't play for you and doesn't control the mouse. It only shows the suggestion.
The interface is in Spanish for now.
