"""
Pagade - Indian Ludo / Pachisi
Pygame implementation ported from the original Tkinter version.

Rules:
  - 4 players (Red, Blue, Yellow, Green), each with 4 pieces.
  - Turn order: Red -> Blue -> Yellow -> Green -> Red ...
  - Roll 1-6. A 6 grants an extra roll (max 3 rolls per turn).
  - Triple 6 = lose your turn.
  - Need a 6 to move a piece out of home onto the board.
  - Pieces travel 52 outer squares clockwise, then up a 6-square home column.
  - Landing on an opponent (not on a safe square) captures them (sent home).
  - Safe squares: outer positions 1, 9, 14, 22, 27, 35, 40, 48.
  - Two same-color pieces on a square form a "double" (can't be captured).
  - Piece reaching position 57 (end of home column) is home safe.
  - First player to get all 4 pieces home wins.
"""

import pygame
import sys
import random
import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WINDOW_W, WINDOW_H = 900, 750
BOARD_SIZE = 750
CELL = 50  # pixel size of one grid cell
FPS = 30

# Colours (R, G, B) – warm earthy palette matching Pallankuzhi / Aadu Puli Aatam
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
WARM_CREAM = (255, 245, 230)
PANEL_BG = (222, 195, 155)
GRAY = (180, 160, 130)
DARK_GRAY = (80, 50, 20)
LIGHT_GRAY = (230, 215, 195)
TEXT_COLOR = (60, 30, 10)
BTN_COLOR = (180, 120, 60)
BTN_HOVER = (200, 140, 80)
LINE_COLOR = (101, 67, 33)

RED = (220, 40, 40)
RED_LIGHT = (255, 180, 180)
BLUE = (40, 80, 220)
BLUE_LIGHT = (180, 200, 255)
GREEN = (40, 180, 40)
GREEN_LIGHT = (180, 255, 180)
YELLOW = (220, 200, 0)
YELLOW_LIGHT = (255, 255, 180)

BOARD_BG = (244, 228, 200)
CENTER_COLOR = (210, 170, 90)

PLAYER_COLORS = {"RED": RED, "BLUE": BLUE, "YELLOW": YELLOW, "GREEN": GREEN}
PLAYER_LIGHT = {"RED": RED_LIGHT, "BLUE": BLUE_LIGHT, "YELLOW": YELLOW_LIGHT, "GREEN": GREEN_LIGHT}
TURN_ORDER = ["RED", "BLUE", "YELLOW", "GREEN"]

SAFE_SQUARES = {1, 9, 14, 22, 27, 35, 40, 48}

# ---------------------------------------------------------------------------
# Helper: build the 52 outer-path coordinates (matches original layout)
# ---------------------------------------------------------------------------

def _build_outer_path():
    """Return list of 52 (x, y) top-left pixel coords for the outer loop."""
    box = [None] * 52

    for i in range(6):
        box[i] = (300, 700 - 50 * i)
    for i in range(6, 12):
        box[i] = (250 - 50 * (i - 6), 400)
    box[12] = (0, 350)
    for i in range(13, 19):
        box[i] = (50 * (i - 13), 300)
    for i in range(19, 25):
        box[i] = (300, 250 - 50 * (i - 19))
    box[25] = (350, 0)
    for i in range(26, 32):
        box[i] = (400, 50 * (i - 26))
    for i in range(32, 38):
        box[i] = (450 + 50 * (i - 32), 300)
    box[38] = (700, 350)
    for i in range(39, 45):
        box[i] = (700 - 50 * (i - 39), 400)
    for i in range(45, 51):
        box[i] = (400, 450 + 50 * (i - 45))
    box[51] = (350, 700)

    return box


def _build_color_path(outer, start_idx, home_column_coords):
    """Build 58-element path (indices 0-56 usable, 57 = finish sentinel).

    Indices 0..51 map to outer squares starting at *start_idx*.
    Indices 50..56 are overwritten with the 7 home-column coords.
    Index 57 is the last home-column square (the finish).
    """
    path = [None] * 58
    idx = start_idx
    for i in range(52):
        path[i] = outer[idx]
        idx = (idx + 1) % 52
    # overwrite the last 7 with the home column (indices 50-56)
    for i, coord in enumerate(home_column_coords):
        path[50 + i] = coord
    path[57] = path[56]  # finish sentinel
    return path


OUTER_PATH = _build_outer_path()

# Home columns (7 squares each, leading toward center)
_RED_HOME_COL = [(50 * i, 350) for i in range(7)]
_BLUE_HOME_COL = [(350, 700 - 50 * i) for i in range(7)]
_YELLOW_HOME_COL = [(700 - 50 * i, 350) for i in range(7)]
_GREEN_HOME_COL = [(350, 50 * i) for i in range(7)]

RED_PATH = _build_color_path(OUTER_PATH, 14, _RED_HOME_COL)
BLUE_PATH = _build_color_path(OUTER_PATH, 1, _BLUE_HOME_COL)
YELLOW_PATH = _build_color_path(OUTER_PATH, 40, _YELLOW_HOME_COL)
GREEN_PATH = _build_color_path(OUTER_PATH, 27, _GREEN_HOME_COL)

COLOR_PATHS = {"RED": RED_PATH, "BLUE": BLUE_PATH, "YELLOW": YELLOW_PATH, "GREEN": GREEN_PATH}

# Home-base positions (where pieces sit before entering the board)
HOME_POSITIONS = {
    "RED":    [(100, 100), (200, 100), (100, 200), (200, 200)],
    "BLUE":   [(100, 550), (200, 550), (100, 650), (200, 650)],
    "YELLOW": [(550, 550), (650, 550), (550, 650), (650, 650)],
    "GREEN":  [(550, 100), (650, 100), (550, 200), (650, 200)],
}


# ---------------------------------------------------------------------------
# Piece
# ---------------------------------------------------------------------------

class Piece:
    """A single game piece."""

    def __init__(self, color, index):
        self.color = color
        self.index = index          # 0-3 within color
        self.pos = -1               # -1 = in home base; 0..56 = on path; 57 = finished
        self.double = False
        self.finished = False

    @property
    def pixel_pos(self):
        """Return (cx, cy) centre pixel coordinates."""
        if self.pos == -1:
            x, y = HOME_POSITIONS[self.color][self.index]
            return x + CELL // 2, y + CELL // 2
        path = COLOR_PATHS[self.color]
        x, y = path[self.pos]
        return x + CELL // 2, y + CELL // 2

    def can_move(self, steps):
        if self.finished:
            return False
        if self.pos == -1:
            return steps == 6
        return self.pos + steps <= 57


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class PagadeGame:
    """Core game state."""

    def __init__(self):
        self.pieces = {}
        for color in TURN_ORDER:
            self.pieces[color] = [Piece(color, i) for i in range(4)]

        self.current_player_idx = 0
        self.rolls = []           # dice values available this turn
        self.roll_count = 0       # how many times rolled this turn (max 3)
        self.move_index = 0       # which roll we're consuming
        self.phase = "ROLL"       # ROLL | MOVE | GAME_OVER
        self.winner = None
        self.last_dice = None
        self.message = ""

    # -- properties ----------------------------------------------------------
    @property
    def current_color(self):
        return TURN_ORDER[self.current_player_idx]

    @property
    def current_pieces(self):
        return self.pieces[self.current_color]

    # -- dice ----------------------------------------------------------------
    def roll_dice(self):
        if self.phase != "ROLL":
            return
        value = random.randint(1, 6)
        self.last_dice = value
        self.rolls.append(value)
        self.roll_count += 1

        # Triple six -> lose turn
        if self.roll_count == 3 and all(r == 6 for r in self.rolls):
            self.message = "Triple 6! Turn lost."
            self._next_turn()
            return

        if value == 6 and self.roll_count < 3:
            self.message = f"Rolled {value}! Roll again."
            # stay in ROLL phase
        else:
            # done rolling
            self.phase = "MOVE"
            self.move_index = 0
            self.message = f"Rolled: {', '.join(str(r) for r in self.rolls)}"
            self._auto_skip_if_no_moves()

    # -- movement ------------------------------------------------------------
    def try_move_piece(self, piece):
        """Attempt to move *piece* using the current roll value. Returns True on success."""
        if self.phase != "MOVE":
            return False
        if piece.color != self.current_color:
            return False
        if self.move_index >= len(self.rolls):
            return False

        steps = self.rolls[self.move_index]

        if not piece.can_move(steps):
            return False

        if piece.pos == -1:
            # Move out of home (requires 6)
            piece.pos = 0
            self._handle_capture(piece)
            self._update_doubles(self.current_color)
        else:
            new_pos = piece.pos + steps
            if new_pos == 57:
                piece.pos = 57
                piece.finished = True
            elif new_pos > 57:
                return False
            else:
                piece.pos = new_pos
                if new_pos < 52:
                    self._handle_capture(piece)
                self._update_doubles(self.current_color)

        self.move_index += 1

        # Check win
        if all(p.finished for p in self.current_pieces):
            self.winner = self.current_color
            self.phase = "GAME_OVER"
            self.message = f"{self.current_color} wins!"
            return True

        if self.move_index >= len(self.rolls):
            self._next_turn()
        else:
            self._auto_skip_if_no_moves()

        return True

    # -- capture -------------------------------------------------------------
    def _handle_capture(self, mover):
        """If mover landed on an opponent piece (not safe, not double), send it home."""
        if mover.pos < 0 or mover.pos >= 52:
            return
        mover_path = COLOR_PATHS[mover.color]
        mx, my = mover_path[mover.pos]

        # Check if this is a safe square on the outer path
        for sq in SAFE_SQUARES:
            if OUTER_PATH[sq] == (mx, my):
                return

        for color in TURN_ORDER:
            if color == mover.color:
                continue
            opp_path = COLOR_PATHS[color]
            for p in self.pieces[color]:
                if p.finished or p.pos < 0 or p.pos >= 52:
                    continue
                px, py = opp_path[p.pos]
                if (px, py) == (mx, my) and not p.double:
                    p.pos = -1
                    p.double = False
                    self.message = f"{mover.color} captured {color}!"

    # -- doubles -------------------------------------------------------------
    def _update_doubles(self, color):
        pieces = self.pieces[color]
        for p in pieces:
            p.double = False
        for i in range(len(pieces)):
            for j in range(i + 1, len(pieces)):
                if pieces[i].pos >= 0 and pieces[i].pos == pieces[j].pos and not pieces[i].finished:
                    pieces[i].double = True
                    pieces[j].double = True

    # -- turn management -----------------------------------------------------
    def _next_turn(self):
        self.current_player_idx = (self.current_player_idx + 1) % 4
        self.rolls = []
        self.roll_count = 0
        self.move_index = 0
        self.phase = "ROLL"
        self.last_dice = None
        self.message = f"{self.current_color}'s turn – roll the dice."

    def _auto_skip_if_no_moves(self):
        """If no piece can use the remaining rolls, skip to next turn."""
        if self.phase != "MOVE":
            return
        has_move = False
        for ri in range(self.move_index, len(self.rolls)):
            steps = self.rolls[ri]
            for p in self.current_pieces:
                if p.can_move(steps):
                    has_move = True
                    break
            if has_move:
                break
        if not has_move:
            self.message = "No valid moves. Turn passes."
            self._next_turn()


# ---------------------------------------------------------------------------
# Renderer / UI
# ---------------------------------------------------------------------------

class PagadeUI:
    """Draws board + handles input via Pygame."""

    def __init__(self, screen, game):
        self.screen = screen
        self.game = game
        self.font_large = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.roll_btn = pygame.Rect(770, 140, 110, 45)

    # -- drawing helpers -----------------------------------------------------
    @staticmethod
    def _draw_star(surface, cx, cy, color, radius=10):
        """Draw a small 5-pointed star."""
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            r = radius if i % 2 == 0 else radius * 0.45
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)

    # -- board drawing -------------------------------------------------------
    def draw_board(self):
        self.screen.fill(BOARD_BG)

        # Home areas (colored rectangles)
        home_areas = [
            (RED_LIGHT, 0, 0),       # top-left = RED
            (GREEN_LIGHT, 450, 0),   # top-right = GREEN
            (BLUE_LIGHT, 0, 450),    # bottom-left = BLUE
            (YELLOW_LIGHT, 450, 450),# bottom-right = YELLOW
        ]
        for clr, hx, hy in home_areas:
            pygame.draw.rect(self.screen, clr, (hx, hy, 300, 300))
            pygame.draw.rect(self.screen, LINE_COLOR, (hx, hy, 300, 300), 2)

        # Draw white path squares with grid
        for (x, y) in OUTER_PATH:
            rect = pygame.Rect(x, y, CELL, CELL)
            pygame.draw.rect(self.screen, WARM_CREAM, rect)
            pygame.draw.rect(self.screen, GRAY, rect, 1)

        # Colored home columns
        for color, coords in [("RED", _RED_HOME_COL), ("BLUE", _BLUE_HOME_COL),
                               ("YELLOW", _YELLOW_HOME_COL), ("GREEN", _GREEN_HOME_COL)]:
            for (x, y) in coords:
                rect = pygame.Rect(x, y, CELL, CELL)
                pygame.draw.rect(self.screen, PLAYER_LIGHT[color], rect)
                pygame.draw.rect(self.screen, PLAYER_COLORS[color], rect, 1)

        # Color the start squares
        start_info = [
            ("RED", 14), ("BLUE", 1), ("YELLOW", 40), ("GREEN", 27)
        ]
        for color, idx in start_info:
            x, y = OUTER_PATH[idx]
            rect = pygame.Rect(x, y, CELL, CELL)
            pygame.draw.rect(self.screen, PLAYER_LIGHT[color], rect)
            pygame.draw.rect(self.screen, PLAYER_COLORS[color], rect, 2)

        # Safe squares - draw star
        for sq in SAFE_SQUARES:
            x, y = OUTER_PATH[sq]
            self._draw_star(self.screen, x + CELL // 2, y + CELL // 2, DARK_GRAY, 11)

        # Centre area
        center_rect = pygame.Rect(300, 300, 150, 150)
        pygame.draw.rect(self.screen, CENTER_COLOR, center_rect)
        pygame.draw.rect(self.screen, LINE_COLOR, center_rect, 2)
        # triangles pointing inward
        tri_info = [
            (RED, [(300, 300), (300, 450), (375, 375)]),
            (BLUE, [(300, 450), (450, 450), (375, 375)]),
            (YELLOW, [(450, 450), (450, 300), (375, 375)]),
            (GREEN, [(450, 300), (300, 300), (375, 375)]),
        ]
        for clr, pts in tri_info:
            pygame.draw.polygon(self.screen, clr, pts)
            pygame.draw.polygon(self.screen, LINE_COLOR, pts, 1)

        # Home base inner boxes (where pieces start)
        for color in TURN_ORDER:
            for (hx, hy) in HOME_POSITIONS[color]:
                inner = pygame.Rect(hx + 10, hy + 10, 30, 30)
                pygame.draw.rect(self.screen, WARM_CREAM, inner)
                pygame.draw.rect(self.screen, PLAYER_COLORS[color], inner, 2)

    # -- pieces --------------------------------------------------------------
    def draw_pieces(self):
        for color in TURN_ORDER:
            for piece in self.game.pieces[color]:
                if piece.finished:
                    continue
                cx, cy = piece.pixel_pos
                base_color = PLAYER_COLORS[color]
                radius = 16 if piece.double else 14
                pygame.draw.circle(self.screen, base_color, (cx, cy), radius)
                pygame.draw.circle(self.screen, LINE_COLOR, (cx, cy), radius, 2)
                if piece.double:
                    pygame.draw.circle(self.screen, WARM_CREAM, (cx, cy), 6, 1)

    # -- right panel ---------------------------------------------------------
    def draw_panel(self):
        panel_rect = pygame.Rect(750, 0, 150, WINDOW_H)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, LINE_COLOR, (750, 0), (750, WINDOW_H), 2)

        # Current player
        color = self.game.current_color
        txt = self.font_large.render(f"{color}'s", True, PLAYER_COLORS[color])
        self.screen.blit(txt, (760, 20))
        txt2 = self.font_large.render("Turn", True, PLAYER_COLORS[color])
        self.screen.blit(txt2, (760, 50))

        # Roll button
        if self.game.phase == "ROLL":
            btn_color = BTN_COLOR
        else:
            btn_color = GRAY
        pygame.draw.rect(self.screen, btn_color, self.roll_btn, border_radius=8)
        pygame.draw.rect(self.screen, LINE_COLOR, self.roll_btn, 2, border_radius=8)
        btn_txt = self.font_med.render("ROLL", True, WHITE if self.game.phase == "ROLL" else DARK_GRAY)
        self.screen.blit(btn_txt, (self.roll_btn.x + 30, self.roll_btn.y + 10))

        # Dice results
        y_off = 200
        for i, val in enumerate(self.game.rolls):
            dstr = f"Roll {i + 1}: {val}"
            surf = self.font_med.render(dstr, True, TEXT_COLOR)
            self.screen.blit(surf, (765, y_off + i * 30))

        # Message
        if self.game.message:
            words = self.game.message.split()
            lines, cur = [], ""
            for w in words:
                test = cur + " " + w if cur else w
                if len(test) > 16:
                    lines.append(cur)
                    cur = w
                else:
                    cur = test
            if cur:
                lines.append(cur)
            for i, line in enumerate(lines):
                surf = self.font_small.render(line, True, TEXT_COLOR)
                self.screen.blit(surf, (760, 320 + i * 20))

        # Instructions
        instructions = [
            "How to play:",
            "1. Click ROLL",
            "2. Click a piece",
            "   to move it",
            "3. Need 6 to",
            "   leave home",
            "4. Land on foe",
            "   to capture",
            "",
            "ESC to quit",
        ]
        for i, line in enumerate(instructions):
            surf = self.font_small.render(line, True, DARK_GRAY)
            self.screen.blit(surf, (758, 440 + i * 20))

        # Winner overlay
        if self.game.phase == "GAME_OVER":
            overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0, 0))
            wtxt = self.font_large.render(f"{self.game.winner} WINS!", True, PLAYER_COLORS[self.game.winner])
            rect = wtxt.get_rect(center=(375, 375))
            bg = pygame.Rect(rect.x - 20, rect.y - 15, rect.w + 40, rect.h + 30)
            pygame.draw.rect(self.screen, WARM_CREAM, bg, border_radius=10)
            pygame.draw.rect(self.screen, LINE_COLOR, bg, 3, border_radius=10)
            self.screen.blit(wtxt, rect)

    # -- input ---------------------------------------------------------------
    def handle_click(self, mx, my):
        game = self.game

        # Roll button
        if self.roll_btn.collidepoint(mx, my) and game.phase == "ROLL":
            game.roll_dice()
            return

        # Piece selection
        if game.phase == "MOVE":
            best_piece = None
            best_dist = 999
            for piece in game.current_pieces:
                if piece.finished:
                    continue
                cx, cy = piece.pixel_pos
                dist = math.hypot(mx - cx, my - cy)
                if dist < 25 and dist < best_dist:
                    best_dist = dist
                    best_piece = piece
            if best_piece is not None:
                game.try_move_piece(best_piece)

    # -- main draw -----------------------------------------------------------
    def draw(self):
        self.draw_board()
        self.draw_pieces()
        self.draw_panel()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_game():
    """Entry point – run the Pagade game. Returns when the player quits."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Pagade - Punarutthaan")
    clock = pygame.time.Clock()

    game = PagadeGame()
    ui = PagadeUI(screen, game)
    game.message = "RED's turn – roll the dice."

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ui.handle_click(*event.pos)

        ui.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    run_game()
