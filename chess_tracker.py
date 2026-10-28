#!/usr/bin/env python3
"""
Auto-tracker + mejor jugada para ajedrez (cualquier app/web, 8x8).

Uso:
    pip install mss pillow numpy python-chess
    python chess_tracker.py --engine /ruta/a/stockfish [--negras-abajo] [--tiempo 1.0]

Flujo:
 1. Corre el script y arrastra el mouse sobre el tablero (esquina a esquina).
 2. Con el tablero en POSICION INICIAL, pulsa "Calibrar".
 3. Juega. El script detecta cada jugada y te muestra la mejor.
"""
import argparse
import ctypes
import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import chess
import chess.engine
import mss
import numpy as np
from PIL import Image, ImageTk

# Windows con zoom 125%/150%: sin esto la captura y la ventana no coinciden
try:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


# ---------- captura de pantalla ----------
def grab(region):
    with mss.mss() as s:
        shot = s.grab(region)
    return np.array(Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX"))


def select_region():
    """Pantalla completa congelada; arrastras para marcar el tablero."""
    time.sleep(0.6)  # deja que desaparezca el cuadro de aviso antes de capturar
    with mss.mss() as s:
        mon = s.monitors[1]
        shot = s.grab(mon)
    img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.update()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    fx, fy = img.width / sw, img.height / sh
    tk_img = ImageTk.PhotoImage(img.resize((sw, sh)))
    canvas = tk.Canvas(root, width=sw, height=sh, cursor="cross", highlightthickness=0)
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    st = {"x0": 0, "y0": 0, "rect": None, "box": None}

    def press(e):
        st["x0"], st["y0"] = e.x, e.y
        st["rect"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="red", width=2)

    def drag(e):
        canvas.coords(st["rect"], st["x0"], st["y0"], e.x, e.y)

    def release(e):
        x0, y0, x1, y1 = st["x0"], st["y0"], e.x, e.y
        side = min(abs(x1 - x0), abs(y1 - y0))  # lo fuerza a cuadrado
        left = min(x0, x1)
        top = min(y0, y1)
        st["box"] = (left, top, side)
        root.destroy()

    canvas.bind("<ButtonPress-1>", press)
    canvas.bind("<B1-Motion>", drag)
    canvas.bind("<ButtonRelease-1>", release)
    root.mainloop()

    if not st["box"] or st["box"][2] < 80:
        raise SystemExit("Seleccion invalida o muy pequena.")
    left, top, side = st["box"]
    return {
        "left": mon["left"] + int(left * fx),
        "top": mon["top"] + int(top * fy),
        "width": int(side * fx),
        "height": int(side * fy),
    }


# ---------- reconocimiento de piezas ----------
def cell_info(cell):
    """Devuelve (ocupada, luminosidad_pieza, vector_silueta)."""
    h, w = cell.shape[:2]
    m0 = int(h * 0.08)
    inner = cell[m0:h - m0, m0:w - m0]
    # color de fondo = el color mas repetido de la casilla (aguanta resaltados
    # y tableros marcados a mano con un par de pixeles de error)
    q = (inner >> 3).astype(np.int32)
    key = (q[..., 0] << 10) | (q[..., 1] << 5) | q[..., 2]
    vals, counts = np.unique(key, return_counts=True)
    top = int(vals[counts.argmax()])
    bg = np.array([(top >> 10) & 31, (top >> 5) & 31, top & 31]) * 8 + 4
    inner = inner.astype(float)
    mask = np.abs(inner - bg).sum(axis=2) > 35
    if mask.mean() < 0.08:
        return False, 0.0, None
    lum = inner.mean(axis=2)[mask].mean()
    vec = np.array(
        Image.fromarray((mask * 255).astype("uint8")).resize((24, 24)), dtype=float
    ).ravel() / 255.0
    return True, lum, vec


class Recognizer:
    def __init__(self, white_bottom=True):
        self.white_bottom = white_bottom
        self.templates = {}   # (tipo, color) -> vector
        self.lum_thr = None

    def sq_cells(self, img):
        S = img.shape[0]
        c = S // 8
        for r in range(8):
            for col in range(8):
                f, rk = (col, 7 - r) if self.white_bottom else (7 - col, r)
                yield chess.square(f, rk), img[r * c:(r + 1) * c, col * c:(col + 1) * c]

    def calibrate(self, img):
        """Devuelve (ok, mensaje)."""
        start = chess.Board()
        acc, lums = {}, {True: [], False: []}
        faltan, sobran = [], []
        for sq, cell in self.sq_cells(img):
            p = start.piece_at(sq)
            occ, lum, vec = cell_info(cell)
            if p is None:
                if occ:
                    sobran.append(chess.square_name(sq))
                continue
            if not occ:
                faltan.append(chess.square_name(sq))
                continue
            acc.setdefault((p.piece_type, p.color), []).append(vec)
            lums[p.color].append(lum)
        if faltan:
            return False, "No veo pieza en: " + ", ".join(faltan[:8])
        if sobran:
            return False, "Veo algo donde no hay pieza en: " + ", ".join(sobran[:8])
        self.templates = {k: np.mean(v, axis=0) for k, v in acc.items()}
        self.lum_thr = (np.mean(lums[True]) + np.mean(lums[False])) / 2
        obs = self.recognize(img)
        mal = []
        for s in chess.SQUARES:
            p = start.piece_at(s)
            if obs[s] != ((p.piece_type, p.color) if p else None):
                mal.append(chess.square_name(s))
        if mal:
            return False, "Confundo piezas en: " + ", ".join(mal[:8])
        return True, ""

    def recognize(self, img):
        obs = [None] * 64
        for sq, cell in self.sq_cells(img):
            occ, lum, vec = cell_info(cell)
            if not occ:
                continue
            color = lum > self.lum_thr
            best, bd = None, 1e9
            for (t, c), tv in self.templates.items():
                if c != color:
                    continue
                d = np.sum((vec - tv) ** 2)
                if d < bd:
                    best, bd = t, d
            obs[sq] = (best, color)
        return obs


# ---------- seguimiento de la partida ----------
def mism(board, obs):
    n = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        exp = None if p is None else (p.piece_type, p.color)
        if exp != obs[sq]:
            n += 1
    return n


def detect_move(board, obs):
    """Busca la jugada legal cuyo resultado se parece mas a lo que se ve."""
    cur = mism(board, obs)
    if cur <= 1:
        return None
    best, bm = None, cur
    for mv in board.legal_moves:
        board.push(mv)
        m = mism(board, obs)
        board.pop()
        if m < bm:
            best, bm = mv, m
    return best if bm <= 2 else None


NOMBRES = {chess.PAWN: "Peón", chess.KNIGHT: "Caballo", chess.BISHOP: "Alfil",
           chess.ROOK: "Torre", chess.QUEEN: "Dama", chess.KING: "Rey"}


def describe_parts(board, mv):
    """(pieza, origen, destino, notas)"""
    p = board.piece_at(mv.from_square)
    notas = []
    if board.is_castling(mv):
        notas.append("Enroque")
    elif board.is_capture(mv):
        notas.append("Captura")
    if mv.promotion:
        notas.append(f"Corona a {NOMBRES[mv.promotion].lower()}")
    return p, chess.square_name(mv.from_square), chess.square_name(mv.to_square), notas


BG, CARD = "#1e1f22", "#2b2d31"
TXT, MUTED = "#f2f3f5", "#949ba4"
ACCENT, WARN, BAD = "#81b64c", "#e6a23c", "#e5534b"
GLYPHS = {chess.PAWN: "♟", chess.KNIGHT: "♞", chess.BISHOP: "♝",
          chess.ROOK: "♜", chess.QUEEN: "♛", chess.KING: "♚"}


def make_btn(parent, text, cmd, bg, fg, hover):
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  activebackground=hover, activeforeground=fg, relief="flat", bd=0,
                  padx=18, pady=9, font=("Segoe UI", 10, "bold"), cursor="hand2")
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


# ---------- app ----------
class Overlay:
    """Capa transparente encima del tablero: resalta origen y destino.
    No intercepta clics y (si Windows lo permite) no aparece en las capturas."""
    KEY = "#ff00ff"

    def __init__(self, root, region, white_bottom):
        self.white_bottom = white_bottom
        self.cell = region["width"] // 8
        self.side = self.cell * 8
        self.region = region
        self.safe = False
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=self.KEY)
        self.win.geometry(f"{self.side}x{self.side}+{region['left']}+{region['top']}")
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", self.KEY)
        self.win.attributes("-alpha", 0.45)
        self.canvas = tk.Canvas(self.win, width=self.side, height=self.side,
                                bg=self.KEY, highlightthickness=0)
        self.canvas.pack()
        self.win.update_idletasks()
        self.excluded = self._click_through()

    def _click_through(self):
        """Clics pasan de largo, no roba el foco y se excluye de las capturas."""
        try:
            u = ctypes.windll.user32
            hwnd = u.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            style = u.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
            # LAYERED | TRANSPARENT | TOOLWINDOW | NOACTIVATE
            u.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20 | 0x80 | 0x08000000)
            return bool(u.SetWindowDisplayAffinity(hwnd, 0x11))  # EXCLUDEFROMCAPTURE
        except Exception:
            return False

    def self_test(self):
        """Comprueba si la capa se cuela en las capturas. Si se cuela, usa solo contorno."""
        try:
            base = grab(self.region).astype(np.int16)
            self.canvas.create_rectangle(0, 0, self.side, self.side, fill="#ff0000", outline="")
            self.win.update()
            time.sleep(0.25)
            now = grab(self.region).astype(np.int16)
            self.canvas.delete("all")
            self.win.update()
            self.safe = self.excluded and float(np.abs(now - base).mean()) < 6
        except Exception:
            self.safe = False
        return self.safe

    def _xy(self, sq):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        col, row = (f, 7 - r) if self.white_bottom else (7 - f, r)
        return col * self.cell, row * self.cell

    def set(self, hint):
        self.canvas.delete("all")
        if not hint:
            return
        a, b = hint
        c = self.cell
        for sq, color in ((a, "#ffc400"), (b, "#00e676")):
            x, y = self._xy(sq)
            if self.safe:
                self.canvas.create_rectangle(x, y, x + c, y + c, fill=color, outline=color, width=3)
            else:
                # solo contorno, pegado al borde: no toca la zona que lee el reconocimiento
                bw = max(2, c // 24)
                self.canvas.create_rectangle(x + bw // 2 + 1, y + bw // 2 + 1,
                                             x + c - bw // 2 - 2, y + c - bw // 2 - 2,
                                             outline=color, width=bw)
        if self.safe:
            xa, ya = self._xy(a)
            xb, yb = self._xy(b)
            self.canvas.create_line(xa + c / 2, ya + c / 2, xb + c / 2, yb + c / 2,
                                    fill="#00b0ff", width=max(4, c // 10), arrow="last",
                                    arrowshape=(c * 0.3, c * 0.3, c * 0.14))


class App:
    def __init__(self, args):
        self.args = args
        self.region = select_region()
        self.rec = Recognizer(white_bottom=not args.negras_abajo)
        self.board = chess.Board()
        kw = {}
        if sys.platform == "win32":
            kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW: Stockfish no abre consola
        self.engine = chess.engine.SimpleEngine.popen_uci(args.engine, **kw)
        self.engine.configure({"Threads": 4, "Hash": 256})
        self.calibrated = False
        self.prev_obs = None
        self.last_small = None
        self.done = False
        self.pending = False
        self.analyzing = False
        self._last = None

        # ---------- ventana ----------
        self.root = tk.Tk()
        self.root.title("Ajedrez Tracker")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"340x400+{max(sw - 370, 0)}+60")

        tk.Label(self.root, text="♞  Ajedrez Tracker", bg=BG, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(pady=(14, 4))

        row = tk.Frame(self.root, bg=BG)
        row.pack()
        self.dot = tk.Label(row, text="●", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self.dot.pack(side="left")
        self.status = tk.Label(row, text="", bg=BG, fg=TXT, font=("Segoe UI", 10))
        self.status.pack(side="left", padx=(5, 0))

        card = tk.Frame(self.root, bg=CARD, height=210)
        card.pack(fill="x", padx=18, pady=14)
        card.pack_propagate(False)
        self.glyph = tk.Label(card, text="♟", bg=CARD, fg="#4e5058",
                              font=("Segoe UI Symbol", 48))
        self.glyph.pack(pady=(10, 0))
        self.name = tk.Label(card, text="", bg=CARD, fg=MUTED,
                             font=("Segoe UI", 9, "bold"))
        self.name.pack()
        self.move = tk.Label(card, text="—", bg=CARD, fg=TXT,
                             font=("Consolas", 28, "bold"))
        self.move.pack(pady=(2, 0))
        self.extra = tk.Label(card, text="", bg=CARD, fg=MUTED, wraplength=280,
                              justify="center", font=("Segoe UI", 10))
        self.extra.pack(pady=(4, 0))

        bar = tk.Frame(self.root, bg=BG)
        bar.pack()
        make_btn(bar, "Calibrar", self.calibrate, ACCENT, "#ffffff", "#6fa03f").pack(side="left", padx=5)
        make_btn(bar, "Salir", self.quit, "#3a3c42", TXT, "#4a4d55").pack(side="left", padx=5)

        self.foot = tk.Label(self.root, text="Mueve esta ventana lejos del tablero",
                             bg=BG, fg="#5d636c", font=("Segoe UI", 8))
        self.foot.pack(pady=(10, 0))

        self.mi_color = not args.negras_abajo  # tu color = el que esta abajo
        self.overlay = Overlay(self.root, self.region, self.mi_color)
        self.root.update()
        if not self.overlay.self_test():
            self.foot.config(text="Resaltado en modo contorno (tu Windows no oculta la capa)")

        self.show(status="Sin calibrar",
                  extra="Pon el tablero en posición inicial y pulsa Calibrar")
        self.render()
        self.root.after(300, self.tick)

    # ---------- vista ----------
    def show(self, **kw):
        base = dict(status="", color=MUTED, glyph="♟", glyph_color="#4e5058",
                    name="", move="—", extra="", extra_color=MUTED, hint=None)
        base.update(kw)
        self.view = base

    def render(self):
        v = self.view
        if v == self._last:
            return
        self._last = dict(v)
        self.dot.config(fg=v["color"])
        self.status.config(text=v["status"])
        self.glyph.config(text=v["glyph"], fg=v["glyph_color"])
        self.name.config(text=v["name"])
        self.move.config(text=v["move"])
        self.extra.config(text=v["extra"], fg=v["extra_color"])
        try:
            self.overlay.set(v["hint"])
        except Exception:
            pass

    # ---------- lógica ----------
    def calibrate(self):
        ok, msg = self.rec.calibrate(grab(self.region))
        if ok:
            self.board = chess.Board()
            self.calibrated = True
            self.prev_obs = None
            self.last_small = None
            self.done = False
            self.pending = False
            self.show(status="Calibrado", color=ACCENT)
            self.analyze()
        else:
            self.calibrated = False
            self.show(status="Falló la calibración", color=BAD,
                      extra=f"{msg}\nRevisa posición inicial y orientación.",
                      extra_color=BAD)
        self.render()

    def analyze(self):
        if self.board.is_game_over():
            self.show(status="Partida terminada", color=MUTED)
            return
        if not self.args.ambos and self.board.turn != self.mi_color:
            self.show(status="Turno del rival", color=MUTED, extra="Esperando su jugada…")
            return
        if self.analyzing:
            self.pending = True
            return
        self.analyzing = True
        self.show(status="Pensando…", color=WARN)
        board = self.board.copy()

        def work():
            try:
                info = self.engine.analyse(board, chess.engine.Limit(time=self.args.tiempo))
                mv = info["pv"][0]
                score = info["score"].pov(board.turn)
                p, a, b, notas = describe_parts(board, mv)
                mate = score.is_mate() and score.mate() > 0
                if mate:
                    notas.insert(0, f"Mate en {score.mate()}")
                if board.fen() == self.board.fen():  # ignora resultados viejos
                    self.show(
                        status=f"Mejor jugada · {'Blancas' if board.turn else 'Negras'}",
                        color=ACCENT,
                        glyph=GLYPHS[p.piece_type],
                        glyph_color="#ffffff" if p.color else "#8b94a3",
                        name=NOMBRES[p.piece_type].upper(),
                        move=f"{a}  →  {b}",
                        extra="  ·  ".join(notas),
                        extra_color=ACCENT if mate else MUTED,
                        hint=(mv.from_square, mv.to_square),
                    )
            except Exception as e:
                self.show(status="Error del motor", color=BAD, extra=str(e), extra_color=BAD)
            self.analyzing = False

        threading.Thread(target=work, daemon=True).start()

    def tick(self):
        try:
            if self.calibrated:
                img = grab(self.region)
                small = img[::4, ::4].astype(np.int16)
                changed = self.last_small is None or np.abs(small - self.last_small).mean() > 0.5
                self.last_small = small
                if changed:
                    self.done = False
                if not self.done:  # solo trabaja si la pantalla cambio
                    obs = self.rec.recognize(img)
                    if obs == self.prev_obs:  # 2 lecturas iguales = animacion terminada
                        self.done = True
                        mv = detect_move(self.board, obs)
                        if mv:
                            self.board.push(mv)
                            self.analyze()
                    self.prev_obs = obs
                if self.pending and not self.analyzing:
                    self.pending = False
                    self.analyze()
            self.render()
        except Exception as e:
            self.show(status="Error", color=BAD, extra=str(e), extra_color=BAD)
            self.render()
        self.root.after(300, self.tick)

    def quit(self):
        try:
            self.engine.quit()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def base_dir():
    if getattr(sys, "frozen", False):  # cuando corre como .exe
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundled_engine():
    """Stockfish empaquetado dentro del .exe (si existe)."""
    base = getattr(sys, "_MEIPASS", base_dir())
    p = os.path.join(base, "stockfish.exe")
    return p if os.path.exists(p) else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", help="ruta al ejecutable de stockfish")
    ap.add_argument("--negras-abajo", action="store_true", help="si las negras estan abajo en pantalla")
    ap.add_argument("--tiempo", type=float, default=0.5, help="segundos de analisis por jugada")
    ap.add_argument("--ambos", action="store_true",
                    help="mostrar sugerencias tambien en el turno del rival")
    args = ap.parse_args()
    sin_argumentos = len(sys.argv) == 1  # doble clic en el .exe

    cfg_path = os.path.join(base_dir(), "config.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    tmp = tk.Tk()
    tmp.withdraw()
    try:
        incluido = bundled_engine()
        if not args.engine:
            args.engine = incluido or cfg.get("engine")
        if not args.engine or not os.path.exists(args.engine):
            messagebox.showinfo("Ajedrez tracker",
                                "Selecciona el archivo de Stockfish (el .exe que descargaste).\n"
                                "Solo te lo pido esta vez.")
            args.engine = filedialog.askopenfilename(
                title="Selecciona stockfish .exe",
                filetypes=[("Ejecutable", "*.exe"), ("Todos", "*.*")])
            if not args.engine:
                sys.exit(0)
        if args.engine != incluido:
            cfg["engine"] = args.engine
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f)
        except Exception:
            pass
        if sin_argumentos:
            blancas = messagebox.askyesno("Orientación",
                                          "¿Tienes las piezas BLANCAS abajo en la pantalla?")
            args.negras_abajo = not blancas
            messagebox.showinfo("Ajedrez tracker",
                                "Ahora arrastra el mouse sobre el tablero, de esquina a esquina.")
    finally:
        tmp.destroy()

    try:
        App(args).run()
    except SystemExit:
        raise
    except Exception as e:
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror("Error", f"{type(e).__name__}: {e}")
        r.destroy()
