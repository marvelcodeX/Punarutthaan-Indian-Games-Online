"""
Pallankuzhi - Traditional South Indian Mancala Game
Part of Punarutthaan - Ancient Indian Games collection
"""

import pygame
import sys
import random
import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 900, 600
FPS = 60

# Colours
BG_COLOR = (244, 228, 200)
BOARD_COLOR = (139, 90, 43)
BOARD_BORDER = (90, 55, 20)
PIT_P1 = (210, 160, 90)
PIT_P2 = (185, 140, 80)
PIT_HIGHLIGHT = (255, 220, 100)
PIT_BORDER = (80, 50, 15)
SHELL_COLOR = (60, 40, 20)
TEXT_COLOR = (50, 30, 10)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCORE_P1_COLOR = (180, 80, 30)
SCORE_P2_COLOR = (50, 100, 150)
BUTTON_COLOR = (139, 90, 43)
BUTTON_HOVER = (170, 120, 60)
BUTTON_TEXT = (255, 255, 255)
WIN_OVERLAY = (0, 0, 0, 160)

NUM_PITS_PER_ROW = 7
INITIAL_SHELLS = 6
TOTAL_SHELLS = NUM_PITS_PER_ROW * 2 * INITIAL_SHELLS  # 84

PIT_RADIUS = 34
PIT_SPACING_X = 100
PIT_SPACING_Y = 140
BOARD_MARGIN_X = 100
BOARD_TOP = 170

# Animation
ANIM_DELAY_MS = 120  # ms between shell drops


# ---------------------------------------------------------------------------
# Game Logic
# ---------------------------------------------------------------------------
class PallankuzhiGame:
    """Core game state and rules for Pallankuzhi."""

    def __init__(self):
        self.reset()

    def reset(self):
        # pits[0..6]  = Player 1 (bottom, human) left-to-right
        # pits[7..13] = Player 2 (top, bot) left-to-right
        self.pits = [INITIAL_SHELLS] * (NUM_PITS_PER_ROW * 2)
        self.scores = [0, 0]
        self.current_player = 0  # 0 = human, 1 = bot
        self.game_over = False
        self.winner = None  # 0, 1, or -1 (draw)

    # ----- helpers -----
    def player_pits(self, player):
        """Return index range for a player's pits."""
        if player == 0:
            return range(0, NUM_PITS_PER_ROW)
        return range(NUM_PITS_PER_ROW, NUM_PITS_PER_ROW * 2)

    def has_shells(self, player):
        return any(self.pits[i] > 0 for i in self.player_pits(player))

    def next_pit(self, idx):
        """Counter-clockwise traversal.
        Bottom row (P1): left-to-right 0->6
        Then top row (P2): right-to-left 13->7
        Then wrap back to 0.
        """
        order = list(range(NUM_PITS_PER_ROW)) + list(
            range(NUM_PITS_PER_ROW * 2 - 1, NUM_PITS_PER_ROW - 1, -1)
        )
        pos = order.index(idx)
        return order[(pos + 1) % len(order)]

    def prev_pit(self, idx):
        """Previous pit in counter-clockwise order (for chain captures)."""
        order = list(range(NUM_PITS_PER_ROW)) + list(
            range(NUM_PITS_PER_ROW * 2 - 1, NUM_PITS_PER_ROW - 1, -1)
        )
        pos = order.index(idx)
        return order[(pos - 1) % len(order)]

    # ----- core move (returns list of animation steps) -----
    def execute_move(self, pit_idx):
        """Execute a full turn starting from *pit_idx*.
        Returns a list of (action, data) tuples for animation:
            ('pickup', pit_idx)
            ('drop', pit_idx, new_count)
            ('capture', pit_idx, captured_count)
            ('continue', pit_idx)  -- picked up again from landing pit
        """
        steps = []
        hand = self.pits[pit_idx]
        self.pits[pit_idx] = 0
        steps.append(("pickup", pit_idx))

        current = pit_idx
        while hand > 0:
            current = self.next_pit(current)
            self.pits[current] += 1
            hand -= 1
            steps.append(("drop", current, self.pits[current]))

        # Landing pit logic
        landing = current
        if self.pits[landing] == 1:
            # Was empty before drop (now 1) -> turn ends
            steps.append(("end_turn", landing))
        else:
            # Check for captures (even count 2 or 4)
            captured_any = self._chain_capture(landing, steps)
            if not captured_any:
                # Odd count and > 1 -> pick up and continue sowing
                if self.pits[landing] > 1:
                    hand = self.pits[landing]
                    self.pits[landing] = 0
                    steps.append(("continue", landing))
                    current = landing
                    while hand > 0:
                        current = self.next_pit(current)
                        self.pits[current] += 1
                        hand -= 1
                        steps.append(("drop", current, self.pits[current]))
                    # Recurse landing logic via loop
                    self._resolve_landing(current, steps)

        self._check_round_end()
        return steps

    def _resolve_landing(self, landing, steps):
        """Resolve the landing after a continue-sow."""
        if self.pits[landing] == 1:
            steps.append(("end_turn", landing))
            return
        captured_any = self._chain_capture(landing, steps)
        if not captured_any and self.pits[landing] > 1:
            hand = self.pits[landing]
            self.pits[landing] = 0
            steps.append(("continue", landing))
            current = landing
            while hand > 0:
                current = self.next_pit(current)
                self.pits[current] += 1
                hand -= 1
                steps.append(("drop", current, self.pits[current]))
            self._resolve_landing(current, steps)

    def _chain_capture(self, pit_idx, steps):
        """Capture shells from pit_idx backwards while count is 2 or 4.
        Returns True if at least one capture occurred."""
        captured = False
        current = pit_idx
        while self.pits[current] in (2, 4):
            amount = self.pits[current]
            self.pits[current] = 0
            self.scores[self.current_player] += amount
            steps.append(("capture", current, amount))
            captured = True
            current = self.prev_pit(current)
        return captured

    def _check_round_end(self):
        """If either player's row is empty, end the round."""
        for player in (0, 1):
            if not self.has_shells(player):
                other = 1 - player
                for i in self.player_pits(other):
                    self.scores[other] += self.pits[i]
                    self.pits[i] = 0
                self.game_over = True
                if self.scores[0] > self.scores[1]:
                    self.winner = 0
                elif self.scores[1] > self.scores[0]:
                    self.winner = 1
                else:
                    self.winner = -1
                return

    def switch_turn(self):
        self.current_player = 1 - self.current_player
        if not self.has_shells(self.current_player):
            self._check_round_end()


# ---------------------------------------------------------------------------
# Bot AI
# ---------------------------------------------------------------------------
class Bot:
    """Simple AI for Pallankuzhi."""

    @staticmethod
    def choose_pit(game: PallankuzhiGame):
        valid = [i for i in game.player_pits(1) if game.pits[i] > 0]
        if not valid:
            return None

        best_score = -1
        best_pits = []
        for pit in valid:
            score = Bot._simulate(game, pit)
            if score > best_score:
                best_score = score
                best_pits = [pit]
            elif score == best_score:
                best_pits.append(pit)

        # Small random factor
        if len(best_pits) > 1:
            return random.choice(best_pits)
        return best_pits[0]

    @staticmethod
    def _simulate(game: PallankuzhiGame, pit_idx):
        """Simulate a move and return captured shells."""
        saved_pits = game.pits[:]
        saved_scores = game.scores[:]
        saved_over = game.game_over

        game.execute_move(pit_idx)
        captured = game.scores[1] - saved_scores[1]
        # Add small bonus for pits with more shells to break ties
        bonus = saved_pits[pit_idx] * 0.01 + random.random() * 0.005

        # Restore state
        game.pits = saved_pits
        game.scores = saved_scores
        game.game_over = saved_over

        return captured + bonus


# ---------------------------------------------------------------------------
# Pygame Renderer / Main Loop
# ---------------------------------------------------------------------------
class PallankuzhiUI:
    """Pygame front-end for Pallankuzhi."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pallankuzhi - Punarutthaan")
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("Times New Roman", 44, bold=True)
        self.font_medium = pygame.font.SysFont("Times New Roman", 26)
        self.font_small = pygame.font.SysFont("Times New Roman", 20)
        self.font_count = pygame.font.SysFont("Times New Roman", 22, bold=True)
        self.font_score = pygame.font.SysFont("Times New Roman", 30, bold=True)

        self.game = PallankuzhiGame()
        self.bot = Bot()
        self.animating = False
        self.anim_steps = []
        self.anim_index = 0
        self.last_anim_time = 0
        self.highlighted_pit = -1

        # Precompute pit screen positions
        self._compute_pit_positions()

    def _compute_pit_positions(self):
        """Calculate screen (x, y) for each pit index."""
        self.pit_positions = {}
        start_x = BOARD_MARGIN_X + 55
        # Bottom row (Player 1): indices 0-6, left to right
        for i in range(NUM_PITS_PER_ROW):
            x = start_x + i * PIT_SPACING_X
            y = BOARD_TOP + PIT_SPACING_Y + 30
            self.pit_positions[i] = (x, y)
        # Top row (Player 2): indices 7-13, left to right
        # But visually mirrored: pit 7 is rightmost, pit 13 is leftmost
        for i in range(NUM_PITS_PER_ROW):
            x = start_x + (NUM_PITS_PER_ROW - 1 - i) * PIT_SPACING_X
            y = BOARD_TOP + 30
            self.pit_positions[NUM_PITS_PER_ROW + i] = (x, y)

    def _new_game_button_rect(self):
        return pygame.Rect(WIDTH // 2 - 70, HEIGHT - 50, 140, 36)

    def run(self):
        running = True
        bot_delay_start = 0
        bot_waiting = False
        BOT_THINK_DELAY = 500  # ms

        while running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._handle_click(event.pos):
                        pass  # click handled

            # Animate steps
            if self.animating:
                now = pygame.time.get_ticks()
                if now - self.last_anim_time >= ANIM_DELAY_MS:
                    self._advance_animation()
                    self.last_anim_time = now

            # Bot turn
            if (
                not self.animating
                and not self.game.game_over
                and self.game.current_player == 1
            ):
                if not bot_waiting:
                    bot_waiting = True
                    bot_delay_start = pygame.time.get_ticks()
                elif pygame.time.get_ticks() - bot_delay_start >= BOT_THINK_DELAY:
                    bot_waiting = False
                    pit = self.bot.choose_pit(self.game)
                    if pit is not None:
                        self._start_move(pit)

            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_click(self, pos):
        # New Game button
        btn = self._new_game_button_rect()
        if btn.collidepoint(pos):
            self.game.reset()
            self.animating = False
            self.highlighted_pit = -1
            return True

        if self.animating or self.game.game_over or self.game.current_player != 0:
            return False

        # Check pit clicks (player 1 only)
        for i in self.game.player_pits(0):
            px, py = self.pit_positions[i]
            if math.hypot(pos[0] - px, pos[1] - py) <= PIT_RADIUS:
                if self.game.pits[i] > 0:
                    self._start_move(i)
                    return True
        return False

    def _start_move(self, pit_idx):
        self.anim_steps = self.game.execute_move(pit_idx)
        self.anim_index = 0
        self.animating = True
        self.last_anim_time = pygame.time.get_ticks()
        self.highlighted_pit = pit_idx

    def _advance_animation(self):
        if self.anim_index < len(self.anim_steps):
            step = self.anim_steps[self.anim_index]
            action = step[0]
            if action in ("drop", "capture"):
                self.highlighted_pit = step[1]
            elif action == "pickup":
                self.highlighted_pit = step[1]
            elif action == "continue":
                self.highlighted_pit = step[1]
            self.anim_index += 1
        else:
            self.animating = False
            self.highlighted_pit = -1
            if not self.game.game_over:
                self.game.switch_turn()

    # ----- drawing -----
    def _draw(self):
        self.screen.fill(BG_COLOR)
        self._draw_title()
        self._draw_board()
        self._draw_scores()
        self._draw_turn_indicator()
        self._draw_new_game_button()
        if self.game.game_over:
            self._draw_game_over()

    def _draw_title(self):
        title = self.font_large.render("Pallankuzhi", True, TEXT_COLOR)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 10))

    def _draw_board(self):
        # Board background
        board_rect = pygame.Rect(
            BOARD_MARGIN_X - 20,
            BOARD_TOP - 30,
            NUM_PITS_PER_ROW * PIT_SPACING_X + 50,
            PIT_SPACING_Y + 2 * 30 + 60,
        )
        pygame.draw.rect(self.screen, BOARD_BORDER, board_rect, border_radius=18)
        inner = board_rect.inflate(-10, -10)
        pygame.draw.rect(self.screen, BOARD_COLOR, inner, border_radius=14)

        # Draw pits
        for idx in range(NUM_PITS_PER_ROW * 2):
            self._draw_pit(idx)

    def _draw_pit(self, idx):
        x, y = self.pit_positions[idx]
        count = self.game.pits[idx]
        is_p1 = idx < NUM_PITS_PER_ROW
        base_color = PIT_P1 if is_p1 else PIT_P2

        # Highlight
        if idx == self.highlighted_pit and self.animating:
            color = PIT_HIGHLIGHT
        else:
            color = base_color

        # Outer ring
        pygame.draw.circle(self.screen, PIT_BORDER, (x, y), PIT_RADIUS + 3)
        pygame.draw.circle(self.screen, color, (x, y), PIT_RADIUS)

        # Draw shell dots (up to 12 visual)
        if count > 0:
            self._draw_shells_in_pit(x, y, count)

        # Count label
        label = self.font_count.render(str(count), True, TEXT_COLOR)
        self.screen.blit(label, (x - label.get_width() // 2, y + PIT_RADIUS + 6))

    def _draw_shells_in_pit(self, cx, cy, count):
        """Draw small circles inside a pit to represent shells."""
        show = min(count, 12)
        if show <= 6:
            r = 14
        else:
            r = 20
        dot_r = 4
        for k in range(show):
            angle = 2 * math.pi * k / show - math.pi / 2
            dx = int(r * math.cos(angle))
            dy = int(r * math.sin(angle))
            pygame.draw.circle(self.screen, SHELL_COLOR, (cx + dx, cy + dy), dot_r)

    def _draw_scores(self):
        # Player 1 score (bottom)
        p1 = self.font_score.render(
            f"Player 1 (You): {self.game.scores[0]}", True, SCORE_P1_COLOR
        )
        self.screen.blit(p1, (30, HEIGHT - 90))

        # Player 2 score (top)
        p2 = self.font_score.render(
            f"Player 2 (Bot): {self.game.scores[1]}", True, SCORE_P2_COLOR
        )
        self.screen.blit(p2, (WIDTH - p2.get_width() - 30, 65))

    def _draw_turn_indicator(self):
        if self.game.game_over:
            return
        if self.game.current_player == 0:
            txt = "Your Turn - pick a pit!"
            color = SCORE_P1_COLOR
            pos_y = HEIGHT - 130
        else:
            txt = "Bot is thinking..."
            color = SCORE_P2_COLOR
            pos_y = 100
        surf = self.font_medium.render(txt, True, color)
        self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, pos_y))

    def _draw_new_game_button(self):
        btn = self._new_game_button_rect()
        mx, my = pygame.mouse.get_pos()
        hover = btn.collidepoint(mx, my)
        color = BUTTON_HOVER if hover else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, btn, border_radius=8)
        label = self.font_small.render("New Game", True, BUTTON_TEXT)
        self.screen.blit(
            label,
            (btn.x + btn.width // 2 - label.get_width() // 2,
             btn.y + btn.height // 2 - label.get_height() // 2),
        )

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(WIN_OVERLAY)
        self.screen.blit(overlay, (0, 0))

        if self.game.winner == 0:
            msg = "You Win!"
        elif self.game.winner == 1:
            msg = "Bot Wins!"
        else:
            msg = "It's a Draw!"

        text = self.font_large.render(msg, True, WHITE)
        self.screen.blit(
            text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 50)
        )

        score_txt = self.font_medium.render(
            f"You: {self.game.scores[0]}   Bot: {self.game.scores[1]}",
            True,
            WHITE,
        )
        self.screen.blit(
            score_txt,
            (WIDTH // 2 - score_txt.get_width() // 2, HEIGHT // 2 + 20),
        )

        hint = self.font_small.render(
            "Press New Game to play again  |  ESC to quit", True, WHITE
        )
        self.screen.blit(
            hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 70)
        )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
def main():
    ui = PallankuzhiUI()
    ui.run()


if __name__ == "__main__":
    main()
