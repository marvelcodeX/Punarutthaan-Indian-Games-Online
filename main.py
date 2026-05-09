import pygame
import subprocess
import os
import sys

# ---------------------------------------------------------------------------
# Path setup — resolve all paths relative to this script's location
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ---------------------------------------------------------------------------
# Initialize Pygame
# ---------------------------------------------------------------------------
pygame.init()

WIDTH, HEIGHT = 1100, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Punarutthaan - Ancient Indian Games")

# ---------------------------------------------------------------------------
# Color palette — warm, earthy tones
# ---------------------------------------------------------------------------
BG_COLOR = (62, 39, 35)        # Dark brown  #3E2723
CARD_COLOR = (78, 52, 46)      # Slightly lighter brown for cards
BUTTON_COLOR = (215, 204, 200) # Warm cream  #D7CCC8
BUTTON_HOVER = (255, 179, 0)   # Accent gold #FFB300
TEXT_DARK = (62, 39, 35)       # Dark brown text on light buttons
TEXT_LIGHT = (239, 235, 233)   # Light text on dark background
LINK_COLOR = (255, 179, 0)     # Gold links
LINK_HOVER = (255, 214, 100)   # Lighter gold on hover
DIVIDER_COLOR = (93, 64, 55)   # Subtle divider

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
font_title = pygame.font.SysFont("Georgia", 56, bold=True)
font_subtitle = pygame.font.SysFont("Georgia", 22, italic=True)
font_button = pygame.font.SysFont("Georgia", 22, bold=True)
font_link = pygame.font.SysFont("Georgia", 16)
font_hint = pygame.font.SysFont("Georgia", 15, italic=True)

# ---------------------------------------------------------------------------
# Load images from assets/ folder
# ---------------------------------------------------------------------------
def load_asset(filename):
    """Load an image from the assets directory."""
    return pygame.image.load(os.path.join(ASSETS_DIR, filename))

background = pygame.transform.scale(load_asset("background2.jpg"), (WIDTH, HEIGHT))

# Thumbnail images for game cards (scaled to 80x80)
THUMB_SIZE = (80, 80)
thumbnails = {
    "Pallankuzhi": pygame.transform.scale(load_asset("pallankuzhi.jpg"), THUMB_SIZE),
    "Pagade": pygame.transform.scale(load_asset("pagade.jpg"), THUMB_SIZE),
    "Aadu Puli Aatam": pygame.transform.scale(load_asset("tiger_and_lambs.jpg"), THUMB_SIZE),
}

# ---------------------------------------------------------------------------
# Text content for rules & history pages
# ---------------------------------------------------------------------------
GAME_INFO = {
    "pallankuzhi_rules": {
        "title": "Pallankuzhi - Rules",
        "lines": [
            "Pallankuzhi is a traditional mancala game from South India,",
            "played on a board with 14 pits (2 rows of 7).",
            "",
            "Setup:",
            "• Each pit starts with 6 cowrie shells (84 total)",
            "• Bottom row belongs to Player 1, top row to Player 2",
            "",
            "Gameplay:",
            "• Pick up all shells from one of your pits",
            "• Drop them one by one counter-clockwise into subsequent pits",
            "• If the last shell makes a pit have 2 or 4 shells, capture them",
            "• Continue capturing backwards if adjacent pits also have 2 or 4",
            "• If the last shell lands in an empty pit, your turn ends",
            "• If the pit count becomes odd, your turn ends",
            "",
            "Winning:",
            "• When one side is empty, the other player captures their",
            "  remaining shells",
            "• The player with more shells wins!",
        ],
    },
    "pallankuzhi_history": {
        "title": "Pallankuzhi - History",
        "lines": [
            "Pallankuzhi is one of the oldest known board games, belonging",
            "to the mancala family of pit-and-seed games that originated",
            "thousands of years ago.",
            "",
            "Origins:",
            "The game has been played in Tamil Nadu and other parts of",
            "South India for centuries. Archaeological evidence suggests",
            "mancala-type games existed in ancient Mesopotamia and Africa,",
            "with the Indian variant developing its own unique rules.",
            "",
            "Cultural Significance:",
            "• Traditionally played by women and children during festivals",
            "  and leisure time",
            "• The name comes from Tamil: 'Pallam' (pit) + 'Kuzhi' (hole)",
            "• Often carved into temple steps and stone floors across",
            "  South India",
            "• Used as a tool for teaching arithmetic and strategic thinking",
            "",
            "The game spread across Southeast Asia through trade routes,",
            "with variations found in Sri Lanka (Olinda Keliya), Malaysia",
            "(Congkak), and Indonesia (Dakon).",
            "",
            "Pallankuzhi remains a beloved household game in Tamil Nadu,",
            "often played during Pongal and other festivals.",
        ],
    },
    "pagade_rules": {
        "title": "Pagade - Rules",
        "lines": [
            "Pagade is the South Indian version of the ancient game",
            "Pachisi, also known as Chaupar. It is considered the ancestor",
            "of modern Ludo.",
            "",
            "Setup:",
            "• Cross-shaped board with 4 colored home areas",
            "• 4 players (Red, Blue, Yellow, Green), each with 4 pieces",
            "• Pieces start in their colored home area",
            "",
            "Gameplay:",
            "• Roll a dice (1-6). Rolling a 6 gives an extra roll",
            "  (max 3 per turn)",
            "• Three 6s in a row = lose your turn",
            "• A 6 is needed to move a piece out of home onto the board",
            "• Pieces move clockwise around the 52 outer squares",
            "• After completing the loop, pieces enter their home column",
            "  (6 squares)",
            "",
            "Capturing:",
            "• Land on an opponent's piece to send it back home",
            "• Safe squares (marked with stars) protect pieces from capture",
            "• Two same-colored pieces on one square form a 'double'",
            "  — cannot be captured",
            "",
            "Winning:",
            "• Move all 4 pieces through the board and up the home column",
            "• First player to get all pieces home wins!",
        ],
    },
    "pagade_history": {
        "title": "Pagade - History",
        "lines": [
            "Pagade, derived from the ancient game of Pachisi, is one of",
            "India's most historically significant board games, with roots",
            "dating back over 1,500 years.",
            "",
            "Royal Origins:",
            "The game finds mention in the Mahabharata, where a similar",
            "dice game played a pivotal role in the epic's narrative.",
            "Emperor Akbar famously played life-sized Pachisi in his court",
            "at Fatehpur Sikri, using servants as living game pieces.",
            "",
            "The Name:",
            "'Pagade' comes from the Kannada/Tamil word for the game. It",
            "is known by many names across India — Pachisi in Hindi,",
            "Chaupar in Rajasthan, and Thayam in parts of Tamil Nadu.",
            "",
            "Evolution:",
            "• The British adapted Pachisi into 'Ludo' in 1896,",
            "  simplifying the rules",
            "• The original Indian version uses cowrie shells instead",
            "  of dice",
            "• Traditional boards were made of cloth, embroidered with",
            "  silk thread",
            "• The cross-shaped board represents the cosmic mandala in",
            "  Hindu tradition",
            "",
            "Cultural Impact:",
            "Pagade represents the Indian philosophy of fate (dice) versus",
            "strategy (movement choices). It remains one of the most",
            "widely played traditional games across South India.",
        ],
    },
    "aadu_puli_aatam_rules": {
        "title": "Aadu Puli Aatam - Rules",
        "lines": [
            "Aadu Puli Aatam (Goats and Tigers) is an asymmetric strategy",
            "game from Tamil Nadu where three tigers face fifteen lambs.",
            "",
            "Setup:",
            "• Board with 15 intersection points connected by lines",
            "• 3 tigers start on the triangle vertices at the top",
            "• 15 lambs are placed one at a time during the game",
            "",
            "Phase 1 — Placement:",
            "• Lamb player places one lamb per turn on any empty point",
            "• Tiger player moves one tiger per turn along a line to an",
            "  adjacent empty point",
            "• Tigers can capture during this phase",
            "",
            "Phase 2 — Movement:",
            "• After all 15 lambs are placed, lamb player moves lambs",
            "  along lines",
            "• Both sides move one piece per turn to an adjacent empty",
            "  point",
            "",
            "Tiger Captures:",
            "• A tiger jumps over an adjacent lamb to an empty point",
            "  beyond it",
            "• The jumped lamb is removed from the board",
            "• Tigers can only jump along connected lines",
            "",
            "Winning:",
            "• Tigers win by capturing 5 or more lambs",
            "• Lambs win by blocking all tigers so none can move",
        ],
    },
    "aadu_puli_aatam_history": {
        "title": "Aadu Puli Aatam - History",
        "lines": [
            "Aadu Puli Aatam, meaning 'Goat-Tiger Game' in Tamil, is an",
            "ancient strategic board game that has been played in South",
            "India for centuries.",
            "",
            "Origins:",
            "The game is believed to have originated in Tamil Nadu, with",
            "boards carved into the stone floors and steps of temples",
            "dating back to the Chola dynasty (9th-13th century CE).",
            "Similar carved boards have been found at the Virupaksha",
            "Temple in Hampi.",
            "",
            "Variations Across India:",
            "• Known as 'Pulijudam' in Andhra Pradesh",
            "• Called 'Adu Huli' in Karnataka",
            "• Similar to 'Bagh Chal' from Nepal (national game)",
            "• Related games exist in Sri Lanka, Thailand, and",
            "  Southeast Asia",
            "",
            "Strategic Depth:",
            "The game is a classic example of asymmetric warfare — the",
            "tigers are powerful but few, while the lambs are weak",
            "individually but strong in numbers. This mirrors the",
            "guerrilla warfare strategies documented in ancient Tamil",
            "Sangam literature.",
            "",
            "Cultural Significance:",
            "• Often played on kolam (rangoli) patterns drawn on",
            "  the ground",
            "• Used to teach children strategic thinking and planning",
            "• The game appears in Tamil folklore and proverbs",
            "• It demonstrates the principle that unity and coordination",
            "  can overcome individual strength",
            "",
            "The game continues to be popular in rural Tamil Nadu, played",
            "on boards scratched into the earth during village gatherings.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Game definitions — each entry drives one card on the menu
# ---------------------------------------------------------------------------
GAMES = [
    {
        "name": "Pallankuzhi",
        "script": os.path.join("games", "pallankuzhi.py"),
        "thumb": "Pallankuzhi",
        "rules_text_key": "pallankuzhi_rules",
        "history_text_key": "pallankuzhi_history",
    },
    {
        "name": "Pagade",
        "script": os.path.join("games", "pagade.py"),
        "thumb": "Pagade",
        "rules_text_key": "pagade_rules",
        "history_text_key": "pagade_history",
    },
    {
        "name": "Aadu Puli Aatam",
        "script": os.path.join("games", "aadu_puli_aatam.py"),
        "thumb": "Aadu Puli Aatam",
        "rules_text_key": "aadu_puli_aatam_rules",
        "history_text_key": "aadu_puli_aatam_history",
    },
]

# ---------------------------------------------------------------------------
# Layout constants for game cards
# ---------------------------------------------------------------------------
CARD_WIDTH = 300
CARD_HEIGHT = 200
CARD_GAP = 40
CARD_TOP_Y = 300
TOTAL_CARDS_W = len(GAMES) * CARD_WIDTH + (len(GAMES) - 1) * CARD_GAP
CARD_START_X = (WIDTH - TOTAL_CARDS_W) // 2

BUTTON_W = 220
BUTTON_H = 44
BUTTON_RADIUS = 8


# ---------------------------------------------------------------------------
# Helper: draw centered text and return its rect (useful for click detection)
# ---------------------------------------------------------------------------
def draw_text(surface, text, font, color, center_x, center_y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(center_x, center_y))
    surface.blit(rendered, rect)
    return rect


# ---------------------------------------------------------------------------
# Helper: draw a rounded button with hover effect; returns its rect
# ---------------------------------------------------------------------------
def draw_button(surface, text, center_x, center_y, width, height, mouse_pos):
    rect = pygame.Rect(0, 0, width, height)
    rect.center = (center_x, center_y)
    hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_HOVER if hovered else BUTTON_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=BUTTON_RADIUS)
    txt_color = TEXT_DARK
    draw_text(surface, text, font_button, txt_color, center_x, center_y)
    return rect


# ---------------------------------------------------------------------------
# Helper: draw a clickable link with hover effect; returns its rect
# ---------------------------------------------------------------------------
def draw_link(surface, text, center_x, center_y, mouse_pos):
    rendered = font_link.render(text, True, LINK_COLOR)
    rect = rendered.get_rect(center=(center_x, center_y))
    hovered = rect.collidepoint(mouse_pos)
    color = LINK_HOVER if hovered else LINK_COLOR
    rendered = font_link.render(text, True, color)
    if hovered:
        # Underline on hover
        underline_y = rect.bottom + 1
        pygame.draw.line(surface, color, (rect.left, underline_y), (rect.right, underline_y), 1)
    surface.blit(rendered, rect)
    return rect


# ---------------------------------------------------------------------------
# launch_game — single function that handles all three games
# ---------------------------------------------------------------------------
def launch_game(game_entry):
    """Launch a game subprocess from the project root."""
    game_path = os.path.join(BASE_DIR, game_entry["script"])
    print(f"Launching: {game_path}")
    if os.path.isfile(game_path):
        subprocess.run(["python", game_path], cwd=BASE_DIR)
    else:
        print(f"File not found: {game_path}")


# ---------------------------------------------------------------------------
# display_info — show formatted text content for rules/history pages
# ---------------------------------------------------------------------------
def display_info(info_key):
    """Display a scrollable text page for rules or history content."""
    info = GAME_INFO[info_key]
    title = info["title"]
    lines = info["lines"]

    font_info_title = pygame.font.SysFont("Georgia", 36, bold=True)
    font_info_body = pygame.font.SysFont("Georgia", 18)
    font_info_hint = pygame.font.SysFont("Georgia", 14, italic=True)

    # Panel dimensions
    panel_w, panel_h = 900, 620
    panel_x = (WIDTH - panel_w) // 2
    panel_y = (HEIGHT - panel_h) // 2
    margin_x = 40
    title_area_h = 70
    hint_area_h = 35
    body_top = panel_y + title_area_h
    body_bottom = panel_y + panel_h - hint_area_h
    body_h = body_bottom - body_top

    # Pre-render all body lines
    line_height = 26
    rendered_lines = []
    for line in lines:
        if line == "":
            rendered_lines.append(None)
        else:
            rendered_lines.append(font_info_body.render(line, True, TEXT_LIGHT))
    total_content_h = len(rendered_lines) * line_height

    scroll_y = 0
    max_scroll = max(0, total_content_h - body_h)

    running = True
    while running:
        screen.fill(BG_COLOR)

        # Draw content panel with rounded corners
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, CARD_COLOR, panel_rect, border_radius=16)
        pygame.draw.rect(screen, DIVIDER_COLOR, panel_rect, width=1, border_radius=16)

        # Title
        title_surf = font_info_title.render(title, True, BUTTON_HOVER)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, panel_y + 30))
        screen.blit(title_surf, title_rect)

        # Gold divider under title
        div_y = panel_y + 55
        pygame.draw.line(
            screen, BUTTON_HOVER,
            (panel_x + margin_x, div_y),
            (panel_x + panel_w - margin_x, div_y), 2,
        )

        # Clip body text to the body area
        body_clip = pygame.Rect(panel_x + margin_x, body_top, panel_w - 2 * margin_x, body_h)
        screen.set_clip(body_clip)

        for idx, surf in enumerate(rendered_lines):
            y = body_top + idx * line_height - scroll_y
            if surf is not None:
                screen.blit(surf, (panel_x + margin_x, y))

        screen.set_clip(None)

        # Scroll indicators
        if scroll_y > 0:
            pygame.draw.polygon(
                screen, BUTTON_HOVER,
                [(WIDTH // 2 - 8, body_top + 2), (WIDTH // 2 + 8, body_top + 2), (WIDTH // 2, body_top - 6)],
            )
        if scroll_y < max_scroll:
            pygame.draw.polygon(
                screen, BUTTON_HOVER,
                [(WIDTH // 2 - 8, body_bottom - 2), (WIDTH // 2 + 8, body_bottom - 2), (WIDTH // 2, body_bottom + 6)],
            )

        # ESC hint at bottom of panel
        hint_surf = font_info_hint.render("Press ESC to go back  |  Arrow keys / mouse wheel to scroll", True, TEXT_LIGHT)
        hint_rect = hint_surf.get_rect(center=(WIDTH // 2, panel_y + panel_h - 18))
        screen.blit(hint_surf, hint_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_DOWN:
                    scroll_y = min(scroll_y + line_height * 3, max_scroll)
                elif event.key == pygame.K_UP:
                    scroll_y = max(scroll_y - line_height * 3, 0)
            if event.type == pygame.MOUSEWHEEL:
                scroll_y = max(0, min(scroll_y - event.y * line_height * 3, max_scroll))


# ---------------------------------------------------------------------------
# main_menu — the main event loop drawing three game cards
# ---------------------------------------------------------------------------
def main_menu():
    clock = pygame.time.Clock()
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(background, (0, 0))

        # Semi-transparent overlay so text is readable over the background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((62, 39, 35, 180))
        screen.blit(overlay, (0, 0))

        # --- Title ---
        draw_text(screen, "PUNARUTTHAAN", font_title, BUTTON_HOVER, WIDTH // 2, 80)
        draw_text(screen, "Gateway to Ancient Indian Games", font_subtitle, TEXT_LIGHT, WIDTH // 2, 135)

        # Decorative divider line
        line_y = 170
        pygame.draw.line(screen, DIVIDER_COLOR, (WIDTH // 2 - 200, line_y), (WIDTH // 2 + 200, line_y), 2)

        # --- Game cards ---
        card_rects = []  # store (rect, game_entry) for click detection
        btn_rects = []
        link_rects = []

        for i, game in enumerate(GAMES):
            cx = CARD_START_X + i * (CARD_WIDTH + CARD_GAP) + CARD_WIDTH // 2
            card_rect = pygame.Rect(
                cx - CARD_WIDTH // 2, CARD_TOP_Y - 20, CARD_WIDTH, CARD_HEIGHT
            )

            # Card background with rounded corners
            pygame.draw.rect(screen, CARD_COLOR, card_rect, border_radius=12)
            pygame.draw.rect(screen, DIVIDER_COLOR, card_rect, width=1, border_radius=12)

            # Thumbnail centered at top of card
            thumb = thumbnails[game["thumb"]]
            thumb_rect = thumb.get_rect(center=(cx, CARD_TOP_Y + 25))
            screen.blit(thumb, thumb_rect)

            # Game play button
            btn_y = CARD_TOP_Y + 90
            btn_rect = draw_button(screen, game["name"], cx, btn_y, BUTTON_W, BUTTON_H, mouse_pos)
            btn_rects.append((btn_rect, game))

            # Rules and History links side by side
            link_y = CARD_TOP_Y + 140
            rules_rect = draw_link(screen, "Rules", cx - 50, link_y, mouse_pos)
            history_rect = draw_link(screen, "History", cx + 50, link_y, mouse_pos)
            link_rects.append((rules_rect, game["rules_text_key"]))
            link_rects.append((history_rect, game["history_text_key"]))

        # --- Footer hint ---
        draw_text(
            screen, "Click a game to play  |  Rules & History below each card",
            font_hint, TEXT_LIGHT, WIDTH // 2, HEIGHT - 30,
        )

        pygame.display.flip()
        clock.tick(60)

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check game buttons
                for btn_rect, game in btn_rects:
                    if btn_rect.collidepoint(event.pos):
                        launch_game(game)
                        break
                # Check info links
                for link_rect, key in link_rects:
                    if link_rect.collidepoint(event.pos):
                        display_info(key)
                        break

    pygame.quit()


if __name__ == "__main__":
    main_menu()
