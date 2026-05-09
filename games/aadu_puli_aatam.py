"""
Aadu Puli Aatam (Lambs and Tigers) - Traditional Tamil Board Game
=================================================================
3 Tigers vs 15 Lambs on a triangular-rectangular board with 15 intersection points.

Rules:
  - Phase 1 (Placement): Lamb player places lambs one per turn; tigers move.
  - Phase 2 (Movement): After all 15 lambs placed, lambs move along lines.
  - Tigers capture by jumping over an adjacent lamb to an empty point.
  - Tigers win by capturing 5+ lambs. Lambs win by blocking all tiger moves.
"""

import pygame
import sys
import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 700
BOARD_AREA_W = 540
PANEL_X = BOARD_AREA_W + 10
FPS = 60

# Colours
BG_COLOUR = (245, 222, 179)       # warm wheat
LINE_COLOUR = (101, 67, 33)       # dark brown
DOT_COLOUR = (80, 50, 20)
TIGER_COLOUR = (255, 140, 0)      # orange
TIGER_OUTLINE = (180, 90, 0)
LAMB_COLOUR = (255, 255, 255)
LAMB_OUTLINE = (120, 120, 120)
HIGHLIGHT_COLOUR = (0, 200, 100, 150)
SELECT_COLOUR = (0, 150, 255)
TEXT_COLOUR = (60, 30, 10)
PANEL_BG = (222, 195, 155)
BTN_COLOUR = (180, 120, 60)
BTN_HOVER = (200, 140, 80)
BTN_TEXT = (255, 255, 255)
WIN_OVERLAY = (0, 0, 0, 160)

PIECE_RADIUS = 20
DOT_RADIUS = 5
CLICK_RADIUS = 28

TOTAL_LAMBS = 15
CAPTURE_TO_WIN = 5

# ---------------------------------------------------------------------------
# Board geometry – 15 points
# ---------------------------------------------------------------------------
#        0            (apex)
#       / \
#      1   2          (triangle mid)
#     / \ / \
#    3---4---5        (row 0 of rectangle)
#    |\ /|\ /|
#    6---7---8        (row 1)
#    |/ \|/ \|
#    9--10--11        (row 2)
#    |\ /|\ /|
#   12--13--14        (row 3, bottom)

def _build_positions():
    """Return screen coordinates for each of the 15 points."""
    cx = BOARD_AREA_W // 2
    top_y = 60
    row_gap = 100
    col_gap = 100

    positions = {}
    # Triangle
    positions[0] = (cx, top_y)
    positions[1] = (cx - col_gap // 2, top_y + row_gap // 2 + 10)
    positions[2] = (cx + col_gap // 2, top_y + row_gap // 2 + 10)

    # Rectangle rows (rows 0-3, cols 0-2)
    rect_top_y = top_y + row_gap + 20
    for row in range(4):
        for col in range(3):
            idx = 3 + row * 3 + col
            x = cx - col_gap + col * col_gap
            y = rect_top_y + row * row_gap
            positions[idx] = (x, y)

    # Widen triangle to match rectangle width
    positions[1] = (positions[3][0] + (positions[4][0] - positions[3][0]) // 2,
                    (positions[0][1] + positions[3][1]) // 2)
    positions[2] = (positions[4][0] + (positions[5][0] - positions[4][0]) // 2,
                    (positions[0][1] + positions[3][1]) // 2)

    return positions


def _build_adjacency():
    """Return adjacency list and the set of edges (as sorted tuples)."""
    edges = set()

    def add(a, b):
        edges.add((min(a, b), max(a, b)))

    # Triangle
    add(0, 1); add(0, 2); add(1, 2)
    add(1, 3); add(1, 4); add(2, 4); add(2, 5)

    # Rectangle horizontals
    for row in range(4):
        base = 3 + row * 3
        add(base, base + 1)
        add(base + 1, base + 2)

    # Rectangle verticals
    for row in range(3):
        for col in range(3):
            add(3 + row * 3 + col, 3 + (row + 1) * 3 + col)

    # Diagonals inside rectangle (cross pattern alternating)
    # Row 0-1 diagonals: 3-7,5-7,4-6,4-8
    add(3, 7); add(5, 7); add(4, 6); add(4, 8)
    # Row 1-2 diagonals: 6-10,8-10,7-9,7-11
    add(6, 10); add(8, 10); add(7, 9); add(7, 11)
    # Row 2-3 diagonals: 9-13,11-13,10-12,10-14
    add(9, 13); add(11, 13); add(10, 12); add(10, 14)

    # Also add 0-4 connection (apex to center through triangle)
    # Actually the triangle apex connects to 1,2 only; 1,2 connect to row 0.

    adj = {i: set() for i in range(15)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    return adj, edges


def _build_lines():
    """Return list of collinear triples (a, mid, b) for tiger jumps."""
    lines = []

    # Straight horizontal triples in rectangle
    for row in range(4):
        b = 3 + row * 3
        lines.append((b, b + 1, b + 2))

    # Straight vertical triples in rectangle
    for col in range(3):
        for row in range(2):
            a = 3 + row * 3 + col
            b = 3 + (row + 1) * 3 + col
            c = 3 + (row + 2) * 3 + col
            lines.append((a, b, c))

    # Diagonal triples
    # Top-left to bottom-right style
    lines.append((3, 7, 11))
    lines.append((4, 8, 12))  # not valid – 8 and 12 not adjacent; skip
    lines.append((6, 10, 14))
    lines.append((4, 6, 8))   # not collinear in that sense; need to check

    # Let me think about diagonal lines more carefully.
    # The diagonal connections are:
    #   3-7, 7-11  → triple (3,7,11) diagonal ↘
    #   5-7, 7-9   → triple (5,7,9) diagonal ↙
    #   4-6, 6-10  → not connected diagonally, 4-6 is diagonal but 6-10 is diagonal opposite direction
    #   4-8, 8-10  → same issue
    # Actually let me reconsider the diagonal pattern:
    # Row 0→1: 3↘7, 5↙7, 4↙6, 4↘8  (X pattern centered on middle)
    # Row 1→2: 6↘10, 8↙10, 7↙9, 7↘11
    # Row 2→3: 9↘13, 11↙13, 10↙12, 10↘14
    #
    # Collinear diagonal triples:
    #   3→7→11  (top-left going ↘ down-right)
    #   5→7→9   (top-right going ↙ down-left)
    #   4→6→...  4 is col1, 6 is col0 → next would be off-board
    #   4→8→...  4 is col1, 8 is col2 → next would be off-board
    #   Similarly from row 1→2→3:
    #   6→10→14  (col0→col1→col2 going ↘? No. 6=row1col0, 10=row2col1, 14=row3col2) ↘ yes
    #   8→10→12  (row1col2, row2col1, row3col0) ↙ yes
    #   7→9→...  7=row1col1, 9=row2col0 → next row3 would need col-1 → off
    #   7→11→... 7=row1col1, 11=row2col2 → next row3 col3 → off
    #   Also continuing from above:
    #   4→8 and then 8→10? 4=row0col1, 8=row1col2, 10=row2col1 → not same direction
    #
    # So valid diagonal triples in rectangle:
    #   (3, 7, 11)  ↘
    #   (5, 7, 9)   ↙
    #   (6, 10, 14) ↘
    #   (8, 10, 12) ↙

    # Triangle triples:
    #   1-4, 4-... need to check. 0→1→3? 0,1,3 – 0 to 1 connected, 1 to 3 connected.
    #   Are they collinear? 0 is apex, 1 is mid-left, 3 is bottom-left. Yes, collinear!
    #   0→2→5 similarly.
    #   1→2 and 2→? 1 and 2 are horizontally adjacent in triangle row. Extend to... not really.
    #   Also 0→4? Not directly connected. So triangle triples:
    #   (0, 1, 3)
    #   (0, 2, 5)
    #   What about (3, 1, 2)→(1,2) connected, (2,5) connected but not collinear direction.
    #   (1, 4, ?) 1→4 connected, 4 is center of row0. From 1(mid-left) to 4(center)
    #    direction goes to... maybe 8 or 11? Not really a standard line.
    #   Let me just check if 1,2,... nah. (1,2) is horizontal in triangle, extending would go off.
    #   (3,4,5) is horizontal top row – already covered.

    # Rebuild cleanly:
    lines_clean = []

    # Horizontal
    for row in range(4):
        b = 3 + row * 3
        lines_clean.append((b, b + 1, b + 2))

    # Vertical
    for col in range(3):
        for start_row in range(2):
            a = 3 + start_row * 3 + col
            b = a + 3
            c = b + 3
            lines_clean.append((a, b, c))

    # Diagonal ↘ (col increases, row increases)
    lines_clean.append((3, 7, 11))   # r0c0 → r1c1 → r2c2
    lines_clean.append((6, 10, 14))  # r1c0 → r2c1 → r3c2

    # Diagonal ↙ (col decreases, row increases)
    lines_clean.append((5, 7, 9))    # r0c2 → r1c1 → r2c0
    lines_clean.append((8, 10, 12))  # r1c2 → r2c1 → r3c0

    # Triangle diagonals
    lines_clean.append((0, 1, 3))    # apex → mid-left → row0-left
    lines_clean.append((0, 2, 5))    # apex → mid-right → row0-right

    return lines_clean


POSITIONS = _build_positions()
ADJ, EDGES = _build_adjacency()
JUMP_LINES = _build_lines()

# Pre-compute jump map: for each (tiger_pos, adjacent_lamb_pos) → landing pos (if exists)
def _build_jump_map():
    jmap = {}
    for triple in JUMP_LINES:
        a, b, c = triple
        # Tiger at a, lamb at b, land at c
        jmap[(a, b)] = c
        # Tiger at c, lamb at b, land at a
        jmap[(c, b)] = a
    return jmap

JUMP_MAP = _build_jump_map()


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = {i: None for i in range(15)}  # None / 'T' / 'L'
        # Tigers start at triangle vertices
        for t in (0, 1, 2):
            self.board[t] = 'T'
        self.turn = 'L'          # 'L' or 'T'
        self.phase = 'placement' # 'placement' or 'movement'
        self.lambs_to_place = TOTAL_LAMBS
        self.lambs_captured = 0
        self.selected = None     # index of selected piece
        self.valid_moves = []    # list of destination indices
        self.winner = None       # None / 'T' / 'L'

    # ------------------------------------------------------------------
    def tiger_positions(self):
        return [i for i, v in self.board.items() if v == 'T']

    def lamb_positions(self):
        return [i for i, v in self.board.items() if v == 'L']

    def empty_positions(self):
        return [i for i, v in self.board.items() if v is None]

    # ------------------------------------------------------------------
    def get_tiger_moves(self, pos):
        """Return (simple_moves, captures) for a tiger at pos."""
        moves = []
        captures = []
        for nb in ADJ[pos]:
            if self.board[nb] is None:
                moves.append(nb)
            elif self.board[nb] == 'L':
                landing = JUMP_MAP.get((pos, nb))
                if landing is not None and self.board[landing] is None:
                    captures.append((nb, landing))  # (lamb_pos, landing_pos)
        return moves, captures

    def get_lamb_moves(self, pos):
        return [nb for nb in ADJ[pos] if self.board[nb] is None]

    # ------------------------------------------------------------------
    def any_tiger_can_act(self):
        for tp in self.tiger_positions():
            moves, captures = self.get_tiger_moves(tp)
            if moves or captures:
                return True
        return False

    def any_lamb_can_act(self):
        if self.phase == 'placement' and self.lambs_to_place > 0:
            return bool(self.empty_positions())
        for lp in self.lamb_positions():
            if self.get_lamb_moves(lp):
                return True
        return False

    # ------------------------------------------------------------------
    def check_winner(self):
        if self.lambs_captured >= CAPTURE_TO_WIN:
            self.winner = 'T'
        elif not self.any_tiger_can_act():
            self.winner = 'L'

    # ------------------------------------------------------------------
    def select_piece(self, idx):
        """Handle a click on board point idx. Returns True if state changed."""
        if self.winner:
            return False

        # --- Lamb's turn ---
        if self.turn == 'L':
            if self.phase == 'placement':
                if self.board[idx] is None:
                    self.board[idx] = 'L'
                    self.lambs_to_place -= 1
                    if self.lambs_to_place == 0:
                        self.phase = 'movement'
                    self.turn = 'T'
                    self.selected = None
                    self.valid_moves = []
                    self.check_winner()
                    return True
            else:  # movement phase
                if self.selected is None:
                    if self.board[idx] == 'L':
                        moves = self.get_lamb_moves(idx)
                        if moves:
                            self.selected = idx
                            self.valid_moves = moves
                            return True
                else:
                    if idx == self.selected:
                        self.selected = None
                        self.valid_moves = []
                        return True
                    if idx in self.valid_moves:
                        self.board[idx] = 'L'
                        self.board[self.selected] = None
                        self.selected = None
                        self.valid_moves = []
                        self.turn = 'T'
                        self.check_winner()
                        return True
                    # Clicked another own piece
                    if self.board[idx] == 'L':
                        moves = self.get_lamb_moves(idx)
                        if moves:
                            self.selected = idx
                            self.valid_moves = moves
                            return True
                    self.selected = None
                    self.valid_moves = []
                    return True

        # --- Tiger's turn ---
        else:
            if self.selected is None:
                if self.board[idx] == 'T':
                    moves, captures = self.get_tiger_moves(idx)
                    dests = moves + [c[1] for c in captures]
                    if dests:
                        self.selected = idx
                        self.valid_moves = dests
                        return True
            else:
                if idx == self.selected:
                    self.selected = None
                    self.valid_moves = []
                    return True
                if idx in self.valid_moves:
                    moves, captures = self.get_tiger_moves(self.selected)
                    # Check if it's a capture
                    captured_lamb = None
                    for lamb_pos, land in captures:
                        if land == idx:
                            captured_lamb = lamb_pos
                            break
                    self.board[idx] = 'T'
                    self.board[self.selected] = None
                    if captured_lamb is not None:
                        self.board[captured_lamb] = None
                        self.lambs_captured += 1
                    self.selected = None
                    self.valid_moves = []
                    self.turn = 'L'
                    self.check_winner()
                    # After switching to Lamb, check if lambs can act
                    if not self.winner and not self.any_lamb_can_act():
                        # Lambs can't move → skip back to tiger or declare win
                        # (Edge case: all lambs placed but none can move and tigers haven't won)
                        pass
                    return True
                # Clicked another tiger
                if self.board[idx] == 'T':
                    moves, captures = self.get_tiger_moves(idx)
                    dests = moves + [c[1] for c in captures]
                    if dests:
                        self.selected = idx
                        self.valid_moves = dests
                        return True
                self.selected = None
                self.valid_moves = []
                return True

        return False


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def draw_board(surface, state: GameState, new_game_rect: pygame.Rect, mouse_pos):
    surface.fill(BG_COLOUR)

    # --- Draw edges ---
    for a, b in EDGES:
        pygame.draw.line(surface, LINE_COLOUR, POSITIONS[a], POSITIONS[b], 3)

    # --- Draw valid-move highlights ---
    for vm in state.valid_moves:
        pygame.draw.circle(surface, HIGHLIGHT_COLOUR, POSITIONS[vm], PIECE_RADIUS + 4)

    # --- Draw dots & pieces ---
    for idx in range(15):
        px, py = POSITIONS[idx]
        piece = state.board[idx]
        if piece == 'T':
            # Orange circle
            pygame.draw.circle(surface, TIGER_COLOUR, (px, py), PIECE_RADIUS)
            pygame.draw.circle(surface, TIGER_OUTLINE, (px, py), PIECE_RADIUS, 3)
            _draw_text_centered(surface, "T", px, py, 18, (80, 30, 0))
            if idx == state.selected:
                pygame.draw.circle(surface, SELECT_COLOUR, (px, py), PIECE_RADIUS + 5, 3)
        elif piece == 'L':
            pygame.draw.circle(surface, LAMB_COLOUR, (px, py), PIECE_RADIUS)
            pygame.draw.circle(surface, LAMB_OUTLINE, (px, py), PIECE_RADIUS, 3)
            _draw_text_centered(surface, "L", px, py, 18, (100, 100, 100))
            if idx == state.selected:
                pygame.draw.circle(surface, SELECT_COLOUR, (px, py), PIECE_RADIUS + 5, 3)
        else:
            pygame.draw.circle(surface, DOT_COLOUR, (px, py), DOT_RADIUS)

    # --- Info panel ---
    _draw_panel(surface, state, new_game_rect, mouse_pos)


def _draw_text_centered(surface, text, cx, cy, size, colour):
    font = pygame.font.SysFont("segoeuisemibold", size)
    ts = font.render(text, True, colour)
    surface.blit(ts, (cx - ts.get_width() // 2, cy - ts.get_height() // 2))


def _draw_panel(surface, state: GameState, btn_rect: pygame.Rect, mouse_pos):
    panel_rect = pygame.Rect(PANEL_X, 0, WIDTH - PANEL_X, HEIGHT)
    pygame.draw.rect(surface, PANEL_BG, panel_rect)
    pygame.draw.line(surface, LINE_COLOUR, (PANEL_X, 0), (PANEL_X, HEIGHT), 2)

    font_title = pygame.font.SysFont("segoeuisemibold", 22)
    font_body = pygame.font.SysFont("segoeui", 18)
    font_small = pygame.font.SysFont("segoeui", 15)

    x = PANEL_X + 15
    y = 20

    def heading(txt):
        nonlocal y
        ts = font_title.render(txt, True, TEXT_COLOUR)
        surface.blit(ts, (x, y))
        y += ts.get_height() + 8

    def line(txt, font=font_body, colour=TEXT_COLOUR):
        nonlocal y
        ts = font.render(txt, True, colour)
        surface.blit(ts, (x, y))
        y += ts.get_height() + 4

    heading("Aadu Puli Aatam")
    y += 4

    turn_label = "Tiger's Turn" if state.turn == 'T' else "Lamb's Turn"
    turn_col = TIGER_COLOUR if state.turn == 'T' else (100, 100, 100)
    if state.winner:
        turn_label = "Tigers Win!" if state.winner == 'T' else "Lambs Win!"
        turn_col = TIGER_COLOUR if state.winner == 'T' else (0, 150, 0)
    line(turn_label, font_title, turn_col)
    y += 4

    phase_txt = "Placement Phase" if state.phase == 'placement' else "Movement Phase"
    line(f"Phase: {phase_txt}")
    line(f"Lambs to place: {state.lambs_to_place}")
    line(f"Lambs captured: {state.lambs_captured} / {CAPTURE_TO_WIN}")
    lambs_on_board = len(state.lamb_positions())
    line(f"Lambs on board: {lambs_on_board}")
    y += 12

    heading("How to Play")
    instructions = [
        "Lambs (white):",
        "  Place on empty points,",
        "  then move along lines.",
        "",
        "Tigers (orange):",
        "  Move along lines or",
        "  jump over a lamb to",
        "  capture it.",
        "",
        "Tigers win: capture 5 lambs",
        "Lambs win: trap all tigers",
        "",
        "Click piece, then destination.",
        "ESC to quit.",
    ]
    for inst in instructions:
        line(inst, font_small)

    # New Game button
    btn_col = BTN_HOVER if btn_rect.collidepoint(mouse_pos) else BTN_COLOUR
    pygame.draw.rect(surface, btn_col, btn_rect, border_radius=8)
    pygame.draw.rect(surface, LINE_COLOUR, btn_rect, 2, border_radius=8)
    ts = font_title.render("New Game", True, BTN_TEXT)
    surface.blit(ts, (btn_rect.centerx - ts.get_width() // 2,
                       btn_rect.centery - ts.get_height() // 2))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Aadu Puli Aatam - Punarutthaan")
    clock = pygame.time.Clock()

    state = GameState()
    btn_w, btn_h = 160, 44
    new_game_rect = pygame.Rect(PANEL_X + (WIDTH - PANEL_X - btn_w) // 2,
                                HEIGHT - btn_h - 20, btn_w, btn_h)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # New-game button
                if new_game_rect.collidepoint(mx, my):
                    state.reset()
                    continue
                # Board click – find closest point within radius
                clicked_idx = None
                best_dist = CLICK_RADIUS
                for idx, (px, py) in POSITIONS.items():
                    d = math.hypot(mx - px, my - py)
                    if d < best_dist:
                        best_dist = d
                        clicked_idx = idx
                if clicked_idx is not None:
                    state.select_piece(clicked_idx)

        draw_board(screen, state, new_game_rect, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
