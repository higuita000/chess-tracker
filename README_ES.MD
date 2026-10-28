Ajedrez Tracker

Programa para Windows que lee un tablero de ajedrez en tu pantalla, sigue la partida jugada a jugada y te muestra la mejor jugada con Stockfish. Funciona con cualquier web o app de ajedrez, porque no se conecta a ninguna: solo mira la pantalla.

Te dice qué pieza mover y a dónde (Caballo g1 → f3) y además resalta las dos casillas directamente sobre el tablero. El resaltado no interfiere con el mouse: puedes hacer clic y arrastrar piezas como siempre.

Uso responsable

Esta herramienta es para practicar contra bots, analizar partidas y aprender. Usarla en partidas contra personas en sitios como Chess.com o Lichess va contra sus reglas, se detecta y termina en baneo. Úsala bajo tu responsabilidad.

Qué incluye este repositorio
Archivo	Para qué sirve
chess_tracker.py	El programa
crear_exe.bat	Convierte el programa en un .exe con un solo clic
README.md	Este archivo

No incluye Stockfish. Tienes que descargarlo tú (ver paso 2).

Requisitos
Windows 10 (versión 2004 o más nueva) o Windows 11.
Python 3.9 o superior. Al instalarlo, marca la casilla "Add Python to PATH". Si te la saltas, nada de lo siguiente funciona.
Un tablero de ajedrez de 8x8 visible en pantalla.
Instalación
1. Descarga este repositorio

Botón verde Code → Download ZIP, y descomprímelo en una carpeta (por ejemplo C:\ChessTracker).

2. Descarga Stockfish
Entra a stockfishchess.org/download.
Descarga la versión para Windows. Si te da a elegir según el procesador, la versión x86-64 o universal funciona en casi todos los equipos.
Descomprime el .zip descargado. Dentro hay una carpeta con un archivo .exe de nombre largo, algo como stockfish-windows-x86-64-universal.exe.
3. Cambia el nombre y cópialo a la carpeta del proyecto
Copia ese .exe a la misma carpeta donde están chess_tracker.py y crear_exe.bat.
Renómbralo a stockfish.exe (exactamente así, en minúsculas). El script de instalación busca ese nombre.

La carpeta debe quedar así:

ChessTracker/
├── chess_tracker.py
├── crear_exe.bat
├── README.md
└── stockfish.exe
4. Crea el ejecutable

Haz doble clic en crear_exe.bat. Instala las dependencias y arma el programa, y tarda unos minutos. Al terminar, tu programa estará en la carpeta dist:

dist/AjedrezTracker.exe

Ese archivo ya trae Stockfish adentro. Puedes copiarlo a donde quieras (por ejemplo el escritorio) y borrar el resto.

Uso
Abre una partida en tu web o app de ajedrez y déjala en la posición inicial, con el tablero completo visible.
Haz doble clic en AjedrezTracker.exe.
Te pregunta si tienes las piezas blancas abajo en pantalla. Responde según tu tablero.
Con la pantalla congelada, arrastra el mouse sobre el tablero, de esquina a esquina.
Aparece la ventana del programa. Con la partida todavía en posición inicial, pulsa Calibrar. Si dice "Calibrado", ya está funcionando.
Juega. Cada vez que sea tu turno verás la mejor jugada en la ventana y resaltada en el tablero:
Amarillo: la casilla de la pieza que debes mover.
Verde: la casilla a donde moverla.
Flecha azul: el recorrido.

Cuando es el turno del rival, la ventana dice "Turno del rival" y no muestra nada. Tu color se toma de lo que respondiste en el paso 3 (el que está abajo).

Estados de la ventana
Punto	Significado
Gris	Sin calibrar o esperando
Naranja	Stockfish está pensando
Verde	Jugada lista
Rojo	Algo falló (el mensaje dice qué)

Si hay un mate forzado, la ventana lo indica (por ejemplo Mate en 3). Si no, simplemente muestra la mejor jugada que encuentra el motor.

Consejos para que funcione bien
Empieza siempre en la posición inicial. El programa aprende cómo se ve cada pieza en tu tema durante la calibración y necesita ver las 32 piezas en su sitio. No puede engancharse a una partida ya empezada.
Usa un tablero de colores lisos. Los temas con texturas (pasto, madera marcada, mármol) pueden hacer que vea piezas donde no hay. Los verdes y marrones planos de Chess.com o Lichess funcionan bien.
No tapes el tablero con la ventana del programa. Por defecto aparece arriba a la derecha, pero puedes moverla.
Selecciona el tablero ajustado, sin incluir marcos ni nombres de jugadores. Un par de píxeles de error no importan.
Si cambias de web, de tema o de tamaño de tablero, vuelve a abrir el programa y calibra otra vez.
Opciones avanzadas

Si prefieres no usar el .exe, puedes correr el script directamente:

pip install mss pillow numpy python-chess
python chess_tracker.py --engine "C:\ruta\a\stockfish.exe"
Opción	Qué hace
--engine RUTA	Ruta a Stockfish (no hace falta si usas el .exe con Stockfish incluido)
--negras-abajo	Úsala si tienes las negras abajo en pantalla
--tiempo N	Segundos que piensa Stockfish por jugada (por defecto 0.5). Más tiempo, mejores jugadas, pero más lento
--ambos	Muestra sugerencias también en el turno del rival

Si lo corres sin ninguna opción, te pregunta todo con ventanas y recuerda la ruta de Stockfish en un archivo config.json. Si quieres que te vuelva a pedir Stockfish, borra ese archivo.

Solución de problemas

"python no se reconoce como un comando" Python no quedó en el PATH. Reinstálalo marcando "Add Python to PATH".

"falta el archivo stockfish.exe en esta carpeta" crear_exe.bat no encuentra Stockfish. Revisa que lo copiaste a la misma carpeta y que se llama exactamente stockfish.exe.

Windows dice "Windows protegió tu PC" o el antivirus bloquea el .exe Es normal con programas hechos con PyInstaller que no están firmados. Elige Más información → Ejecutar de todos modos, o agrega una excepción. Como lo construyes tú mismo desde este código, puedes revisar qué contiene.

"Falló la calibración" El mensaje indica qué casillas no entendió. Casi siempre es una de estas:

La partida ya no está en posición inicial.
Elegiste mal la orientación (blancas o negras abajo).
La selección no abarca el tablero completo.
El tema del tablero tiene texturas. Cambia a uno de colores lisos.

La ventana del programa tapa una parte del tablero Muévela hacia un lado antes de calibrar.

El tablero se ve desfasado al seleccionarlo Pasa con el escalado de pantalla de Windows (125 %, 150 %). Las versiones actuales ya lo corrigen, así que asegúrate de haber reconstruido el .exe con el código más reciente.

El resaltado aparece como "modo contorno" Tu Windows no permite ocultar la capa de resaltado a las capturas, así que el programa dibuja solo el borde de las casillas para no confundirse a sí mismo. Es normal en algunas versiones.

Deja de detectar mis jugadas Normalmente es porque algo tapó parte del tablero durante una jugada, o porque la animación de la web no había terminado. Como el programa sigue la partida desde el inicio, no puede recuperarse a mitad de partida: empieza una partida nueva y calibra de nuevo.

Cómo funciona
Captura la zona del tablero que seleccionaste.
Durante la calibración aprende cómo se ve cada pieza en tu tema, usando la posición inicial como referencia.
En cada cambio de pantalla reconoce las piezas y las compara con todas las jugadas legales posibles (con ayuda de la librería python-chess) para deducir qué se movió.
Le pide a Stockfish la mejor jugada para la posición actual y la muestra.
Limitaciones
Solo tableros 8x8 y ajedrez estándar.
Solo Windows (el resaltado transparente depende de funciones de Windows).
Solo detecta partidas que empiezan desde la posición inicial.
No puede jugar por ti ni controla el mouse. Solo muestra la sugerencia.
