"""Reusable Pygame UI components for the Sudoku GUI."""
import pygame

# ── Colors ──
BG_DARK = (15, 15, 26)
PANEL_BG = (26, 26, 46, 200)
CELL_BG = (30, 30, 55)
CELL_HOVER = (40, 40, 70)
CELL_SELECT = (60, 60, 100)
GRID_LINE = (50, 50, 80)
BOX_LINE = (100, 100, 180)
TEXT_WHITE = (230, 230, 240)
TEXT_DIM = (140, 140, 160)
TEXT_LABEL = (180, 180, 200)
ACCENT = (100, 140, 255)
ACCENT_HOVER = (130, 165, 255)
CLR_CLUE = (255, 255, 255)
CLR_AC3 = (80, 220, 130)
CLR_GUESS = (80, 160, 255)
CLR_CONFLICT = (255, 70, 70)
CLR_PENCIL = (110, 110, 140)
BTN_BG = (40, 40, 70)
BTN_HOVER = (55, 55, 90)
BTN_ACTIVE = (70, 100, 200)
DROPDOWN_BG = (35, 35, 60)
SLIDER_TRACK = (50, 50, 80)
SLIDER_FILL = (80, 130, 240)
SLIDER_KNOB = (130, 170, 255)
GREEN_DIM = (30, 80, 50)
BLUE_DIM = (30, 50, 90)
RED_DIM = (90, 30, 30)

def draw_rounded_rect(surf, color, rect, radius=8, alpha=None):
    if alpha and len(color) < 4:
        color = (*color, alpha)
    if len(color) == 4:
        tmp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(tmp, color, (0, 0, rect[2], rect[3]), border_radius=radius)
        surf.blit(tmp, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)


class Button:
    def __init__(self, x, y, w, h, text, font, color=BTN_BG, hover_color=BTN_HOVER, text_color=TEXT_WHITE, icon=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.icon = icon
        self.hovered = False
        self.enabled = True
        self.active = False

    def draw(self, surf):
        c = BTN_ACTIVE if self.active else (self.hover_color if self.hovered else self.color)
        if not self.enabled:
            c = (30, 30, 45)
        draw_rounded_rect(surf, c, self.rect, 6)
        pygame.draw.rect(surf, ACCENT if self.hovered and self.enabled else GRID_LINE,
                         self.rect, 1, border_radius=6)
        label = self.icon + " " + self.text if self.icon else self.text
        tc = self.text_color if self.enabled else TEXT_DIM
        ts = self.font.render(label, True, tc)
        surf.blit(ts, (self.rect.centerx - ts.get_width()//2,
                        self.rect.centery - ts.get_height()//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.enabled:
                return True
        return False


class Dropdown:
    def __init__(self, x, y, w, h, options, font, label=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options if options else ["—"]
        self.selected = 0
        self.font = font
        self.label = label
        self.open = False
        self.hovered_idx = -1
        self.max_visible = 8
        self.scroll_offset = 0

    @property
    def value(self):
        if 0 <= self.selected < len(self.options):
            return self.options[self.selected]
        return ""

    def get_list_rect(self):
        """Return the bounding rect of the open dropdown list (for hit testing)."""
        n = min(len(self.options), self.max_visible)
        list_h = n * self.rect.h
        return pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.w, list_h)

    def draw_base(self, surf):
        """Draw only the main box + label (no list overlay)."""
        if self.label:
            ls = self.font.render(self.label, True, TEXT_LABEL)
            surf.blit(ls, (self.rect.x, self.rect.y - 20))
        # Main box
        c = BTN_HOVER if self.open else BTN_BG
        draw_rounded_rect(surf, c, self.rect, 6)
        pygame.draw.rect(surf, ACCENT if self.open else GRID_LINE, self.rect, 1, border_radius=6)
        ts = self.font.render(self.value, True, TEXT_WHITE)
        surf.blit(ts, (self.rect.x + 10, self.rect.centery - ts.get_height()//2))
        # Arrow
        ax = self.rect.right - 20
        ay = self.rect.centery
        if self.open:
            pygame.draw.polygon(surf, ACCENT, [(ax-5, ay+3), (ax+5, ay+3), (ax, ay-4)])
        else:
            pygame.draw.polygon(surf, TEXT_DIM, [(ax-5, ay-3), (ax+5, ay-3), (ax, ay+4)])

    def draw_list(self, surf):
        """Draw only the dropdown list overlay. Call AFTER all other UI."""
        if not self.open:
            return
        n = min(len(self.options), self.max_visible)
        list_h = n * self.rect.h
        scrollbar_w = 8 if len(self.options) > self.max_visible else 0
        lr = pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.w, list_h)
        # Shadow
        shadow = pygame.Surface((lr.w + 6, lr.h + 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 60))
        surf.blit(shadow, (lr.x - 3, lr.y - 1))
        # Background
        draw_rounded_rect(surf, (30, 30, 55, 250), lr, 6)
        pygame.draw.rect(surf, ACCENT, lr, 1, border_radius=6)
        # Items
        start = self.scroll_offset
        item_w = lr.w - 4 - scrollbar_w
        for i in range(n):
            opt_idx = start + i
            if opt_idx >= len(self.options):
                break
            iy = lr.y + i * self.rect.h
            ir = pygame.Rect(lr.x + 2, iy, item_w, self.rect.h)
            if opt_idx == self.hovered_idx:
                draw_rounded_rect(surf, (60, 60, 100, 200), ir, 4)
            color = ACCENT if opt_idx == self.selected else TEXT_WHITE
            ts = self.font.render(self.options[opt_idx], True, color)
            surf.blit(ts, (ir.x + 10, ir.centery - ts.get_height()//2))
        # Scrollbar
        if scrollbar_w > 0:
            total = len(self.options)
            max_scroll = max(1, total - self.max_visible)
            sb_x = lr.right - scrollbar_w - 3
            sb_track_y = lr.y + 4
            sb_track_h = lr.h - 8
            # Track
            pygame.draw.rect(surf, (50, 50, 80), (sb_x, sb_track_y, scrollbar_w, sb_track_h),
                             border_radius=4)
            # Thumb
            thumb_h = max(20, int(sb_track_h * self.max_visible / total))
            thumb_y = sb_track_y + int((sb_track_h - thumb_h) * self.scroll_offset / max_scroll)
            pygame.draw.rect(surf, SLIDER_KNOB, (sb_x, thumb_y, scrollbar_w, thumb_h),
                             border_radius=4)

    def draw(self, surf):
        """Convenience: draw base + list together (for simple usage)."""
        self.draw_base(surf)
        self.draw_list(surf)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check list click FIRST (before main box)
            if self.open:
                lr = self.get_list_rect()
                if lr.collidepoint(event.pos):
                    row = (event.pos[1] - lr.y) // self.rect.h
                    idx = self.scroll_offset + row
                    if 0 <= idx < len(self.options):
                        self.selected = idx
                        self.open = False
                        self.scroll_offset = 0
                        return True
                # Click outside list — close
                if not self.rect.collidepoint(event.pos):
                    self.open = False
                    self.scroll_offset = 0
                    return False
            # Toggle on main box click
            if self.rect.collidepoint(event.pos):
                self.open = not self.open
                if self.open:
                    # Ensure selected item is visible
                    if self.selected >= self.max_visible:
                        self.scroll_offset = min(self.selected,
                                                  len(self.options) - self.max_visible)
                    else:
                        self.scroll_offset = 0
                return False

        if event.type == pygame.MOUSEMOTION and self.open:
            lr = self.get_list_rect()
            if lr.collidepoint(event.pos):
                row = (event.pos[1] - lr.y) // self.rect.h
                self.hovered_idx = self.scroll_offset + row
            else:
                self.hovered_idx = -1

        # Scroll with mouse wheel
        if event.type == pygame.MOUSEWHEEL and self.open:
            max_scroll = max(0, len(self.options) - self.max_visible)
            self.scroll_offset = max(0, min(max_scroll, self.scroll_offset - event.y))

        return False


class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, val, font, label=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = val
        self.font = font
        self.label = label
        self.dragging = False

    @property
    def ratio(self):
        return (self.val - self.min_val) / (self.max_val - self.min_val)

    def draw(self, surf):
        if self.label:
            ls = self.font.render(self.label, True, TEXT_LABEL)
            surf.blit(ls, (self.rect.x, self.rect.y - 20))
        # Track
        ty = self.rect.centery
        pygame.draw.line(surf, SLIDER_TRACK, (self.rect.x, ty), (self.rect.right, ty), 4)
        # Fill
        fx = self.rect.x + int(self.ratio * self.rect.w)
        pygame.draw.line(surf, SLIDER_FILL, (self.rect.x, ty), (fx, ty), 4)
        # Knob
        pygame.draw.circle(surf, SLIDER_KNOB, (fx, ty), 8)
        pygame.draw.circle(surf, TEXT_WHITE, (fx, ty), 4)
        # Value label
        vs = self.font.render(f"{int(self.val)}ms", True, TEXT_DIM)
        surf.blit(vs, (self.rect.right + 8, ty - vs.get_height()//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            knob_x = self.rect.x + int(self.ratio * self.rect.w)
            if abs(event.pos[0] - knob_x) < 15 and abs(event.pos[1] - self.rect.centery) < 15:
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            r = (event.pos[0] - self.rect.x) / self.rect.w
            r = max(0, min(1, r))
            self.val = self.min_val + r * (self.max_val - self.min_val)
