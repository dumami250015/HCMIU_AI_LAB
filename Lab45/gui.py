"""
Sudoku AI Solver — Pygame Desktop GUI
Run: python gui.py
"""
import pygame
import sys
import os
import time
import math
import threading
from copy import deepcopy
from solver_engine import SolverEngine
from ui_components import *
from csp import csp as CSP
from util import squares, digits

# ── Constants ──
WIN_W, WIN_H = 1100, 720
GRID_SIZE = 585
CELL_SIZE = GRID_SIZE // 9
GRID_X, GRID_Y = 30, 100
PANEL_X = GRID_X + GRID_SIZE + 30
PANEL_W = WIN_W - PANEL_X - 20
FPS = 60


class SudokuGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Sudoku AI Solver")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("segoeui", 28, bold=True)
        self.font_cell = pygame.font.SysFont("segoeui", 32, bold=True)
        self.font_pencil = pygame.font.SysFont("segoeui", 11)
        self.font_ui = pygame.font.SysFont("segoeui", 14)
        self.font_btn = pygame.font.SysFont("segoeui", 13, bold=True)
        self.font_metric_val = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font_metric_lbl = pygame.font.SysFont("segoeui", 12)
        self.font_status = pygame.font.SysFont("segoeui", 15, bold=True)

        # Board state
        self.cells = {}  # "A1" -> {"value": "", "domain": "123456789", "state": "empty"}
        self.original_clues = {}
        self.selected_cell = None
        self._init_empty_board()

        # Puzzle data
        self.puzzle_files = self._scan_puzzle_files()
        self.current_puzzles = []
        self.current_grid = ""

        # Solver
        self.engine = None
        self.solving = False
        self.paused = False
        self.status = "Ready"
        self.step_timer = 0

        # Batch solving state
        self.batch_mode = False
        self.batch_thread = None
        self.batch_progress = 0
        self.batch_total = 0
        self.batch_solved = 0
        self.batch_done = False
        self.batch_output_file = ""

        # Animation state
        self.cell_animations = {}  # cell -> {"color": (r,g,b), "alpha": 255, "time": t}

        # ── Build UI ──
        px = PANEL_X
        pw = PANEL_W

        # Puzzle loader
        file_names = [os.path.splitext(f)[0] for f in self.puzzle_files] if self.puzzle_files else ["No files"]
        self.dd_file = Dropdown(px, 160, pw - 10, 32, file_names, self.font_ui, "Puzzle File")
        self.dd_puzzle = Dropdown(px, 225, pw - 10, 32, ["Load a file first"], self.font_ui, "Puzzle #")

        # Algorithm selector
        self.dd_algo = Dropdown(px, 300, pw - 10, 32,
                                ["AC-3 + Backtracking", "Backtracking Only", "AC-3 Only"],
                                self.font_ui, "Algorithm")

        # Speed slider
        self.slider_speed = Slider(px, 385, pw - 70, 20, 5, 500, 80, self.font_ui, "Step Delay")

        # Buttons
        bw = (pw - 20) // 3
        by = 420
        self.btn_solve = Button(px, by, bw, 36, "Solve", self.font_btn, color=(30, 70, 50), hover_color=(40, 100, 65))
        self.btn_pause = Button(px + bw + 5, by, bw, 36, "Pause", self.font_btn)
        self.btn_step = Button(px + 2*(bw+5), by, bw, 36, "Step", self.font_btn)

        bw2 = (pw - 10) // 2
        by2 = by + 44
        self.btn_reset = Button(px, by2, bw2, 34, "Reset", self.font_btn)
        self.btn_clear = Button(px + bw2 + 10, by2, bw2, 34, "Clear", self.font_btn,
                                color=(70, 30, 30), hover_color=(100, 40, 40))

        self.all_buttons = [self.btn_solve, self.btn_pause, self.btn_step,
                            self.btn_reset, self.btn_clear]
        self.all_dropdowns = [self.dd_file, self.dd_puzzle, self.dd_algo]

        # Load first file if available
        if self.puzzle_files:
            self._load_puzzle_file(0)

        self.metrics = {"time": 0, "nodes": 0, "guesses": 0, "backtracks": 0}

    # ── Init ──

    def _init_empty_board(self):
        from util import rows, cols
        for r in rows:
            for c in cols:
                key = r + c
                self.cells[key] = {"value": "", "domain": "123456789", "state": "empty"}

    def _scan_puzzle_files(self):
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        if not os.path.isdir(data_dir):
            return []
        return sorted([f for f in os.listdir(data_dir) if f.endswith(".txt")])

    def _get_solve_all_label(self, filename):
        """Return the 'Solve All' label based on filename."""
        base = os.path.splitext(filename)[0].lower()
        if "euler" in base:
            return "Solve All Euler Puzzles"
        elif "magic" in base:
            return "Solve All Magic Tour Puzzles"
        return f"Solve All ({base})"

    def _get_output_filename(self, filename):
        """Return the output filename for batch solving."""
        base = os.path.splitext(filename)[0].lower()
        if "euler" in base:
            return "EulerSolutions.txt"
        elif "magic" in base:
            return "MagicTourSolutions.txt"
        return f"{os.path.splitext(filename)[0]}Solutions.txt"

    def _load_puzzle_file(self, idx):
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        fpath = os.path.join(data_dir, self.puzzle_files[idx])
        with open(fpath) as f:
            self.current_puzzles = [line.strip() for line in f if line.strip() and len(line.strip()) >= 81]
        # Build options: "Solve All" first, then individual puzzles
        solve_all_label = self._get_solve_all_label(self.puzzle_files[idx])
        opts = [solve_all_label] + [f"Puzzle #{i+1}" for i in range(len(self.current_puzzles))]
        self.dd_puzzle.options = opts if self.current_puzzles else ["No puzzles"]
        self.dd_puzzle.selected = 1  # default to Puzzle #1
        if self.current_puzzles:
            self._load_puzzle(1)  # load first individual puzzle

    def _load_puzzle(self, idx):
        """Load puzzle. idx=0 is 'Solve All', idx>=1 is individual puzzle."""
        self.batch_done = False
        if idx == 0:
            # 'Solve All' selected — show empty board with status
            self._stop_solver()
            self.current_grid = ""
            self._init_empty_board()
            self.original_clues.clear()
            self.cell_animations.clear()
            self.status = f"Ready to solve all {len(self.current_puzzles)} puzzles"
            self.metrics = {"time": 0, "nodes": 0, "guesses": 0, "backtracks": 0}
            return
        puzzle_idx = idx - 1  # offset by 1 due to 'Solve All' at index 0
        if puzzle_idx >= len(self.current_puzzles):
            return
        grid = self.current_puzzles[puzzle_idx]
        self.current_grid = grid
        self._stop_solver()
        from util import rows, cols
        i = 0
        self.original_clues = {}
        for r in rows:
            for c in cols:
                key = r + c
                ch = grid[i] if i < len(grid) else '0'
                if ch != '0':
                    self.cells[key] = {"value": ch, "domain": ch, "state": "clue"}
                    self.original_clues[key] = ch
                else:
                    self.cells[key] = {"value": "", "domain": "123456789", "state": "empty"}
                i += 1
        self.cell_animations.clear()
        self.status = "Puzzle loaded"
        self.metrics = {"time": 0, "nodes": 0, "guesses": 0, "backtracks": 0}

    def _clear_board(self):
        self._stop_solver()
        from util import rows, cols
        for r in rows:
            for c in cols:
                self.cells[r+c] = {"value": "", "domain": "123456789", "state": "empty"}
        self.original_clues.clear()
        self.cell_animations.clear()
        self.current_grid = ""
        self.status = "Board cleared"
        self.metrics = {"time": 0, "nodes": 0, "guesses": 0, "backtracks": 0}

    def _reset_board(self):
        if self.batch_mode:
            self._stop_batch()
            self.status = "Batch cancelled"
            return
        if self.current_grid:
            idx = self.dd_puzzle.selected
            self._load_puzzle(idx)
            self.status = "Board reset"

    # ── Solver controls ──

    def _get_algo_key(self):
        v = self.dd_algo.value
        if "AC-3 + Back" in v: return "ac3+backtracking"
        if "Backtracking" in v: return "backtracking"
        return "ac3"

    def _build_grid_string(self):
        if self.current_grid:
            return self.current_grid
        from util import rows, cols
        s = ""
        for r in rows:
            for c in cols:
                v = self.cells[r+c]["value"]
                s += v if v else "0"
        return s

    def _start_solver(self):
        # Check if 'Solve All' is selected
        if self.dd_puzzle.selected == 0 and self.current_puzzles:
            self._start_batch_solve()
            return
        self._stop_solver()
        grid = self._build_grid_string()
        if len(grid) < 81:
            self.status = "Invalid puzzle"
            return
        algo = self._get_algo_key()
        self.engine = SolverEngine(grid, algo)
        # Reset cell states (keep clues)
        from util import rows, cols
        for r in rows:
            for c in cols:
                key = r+c
                if self.cells[key]["state"] != "clue":
                    self.cells[key]["value"] = ""
                    self.cells[key]["state"] = "empty"
                    self.cells[key]["domain"] = "123456789"
        self.cell_animations.clear()
        self.engine.start()
        self.solving = True
        self.paused = False
        self.step_timer = 0
        self.status = f"Solving ({self.dd_algo.value})..."
        self.btn_pause.text = "Pause"

    # ── Batch solving ──

    def _start_batch_solve(self):
        self._stop_solver()
        self._stop_batch()
        self.batch_mode = True
        self.batch_done = False
        self.batch_progress = 0
        self.batch_total = len(self.current_puzzles)
        self.batch_solved = 0
        self.solving = True
        file_idx = self.dd_file.selected
        self.batch_output_file = self._get_output_filename(self.puzzle_files[file_idx])
        algo = self._get_algo_key()
        self.metrics = {"time": 0, "nodes": 0, "guesses": 0, "backtracks": 0}
        self.status = f"Batch: 0/{self.batch_total}..."

        def batch_worker():
            from search import Backtracking_Search, AC3
            solutions = []
            start_t = time.time()
            total_nodes = 0
            total_guesses = 0
            total_bt = 0
            for i, grid in enumerate(self.current_puzzles):
                if not self.batch_mode:
                    break
                puzzle = CSP(grid=grid)
                if algo == "ac3":
                    AC3(puzzle)
                    result = puzzle.values
                elif algo == "backtracking":
                    result = Backtracking_Search(puzzle)
                else:  # ac3+backtracking
                    result = Backtracking_Search(puzzle)

                if result != "FAILURE":
                    # Check if truly fully solved (all cells have exactly 1 value)
                    fully_solved = all(len(result[var]) == 1 for var in squares)
                    if fully_solved:
                        sol = ""
                        for var in squares:
                            sol += result[var]
                        solutions.append(sol)
                        self.batch_solved += 1
                    else:
                        solutions.append("0" * 81)
                else:
                    solutions.append("0" * 81)
                self.batch_progress = i + 1
                self.metrics["time"] = time.time() - start_t
                self.status = f"Batch: {self.batch_progress}/{self.batch_total} ({self.batch_solved} solved)"

            # Write output file
            if self.batch_mode:
                out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.batch_output_file)
                with open(out_path, "w") as f:
                    for sol in solutions:
                        f.write(sol + "\n")
                self.metrics["time"] = time.time() - start_t
                self.status = f"Done! {self.batch_solved}/{self.batch_total} solved \u2192 {self.batch_output_file}"
            self.batch_done = True
            self.solving = False

        self.batch_thread = threading.Thread(target=batch_worker, daemon=True)
        self.batch_thread.start()

    def _stop_batch(self):
        self.batch_mode = False
        if self.batch_thread and self.batch_thread.is_alive():
            self.batch_thread.join(timeout=1)
        self.batch_thread = None

    def _stop_solver(self):
        if self.engine:
            self.engine.cancel()
            self.engine = None
        if self.batch_mode:
            self._stop_batch()
        self.solving = False
        self.paused = False

    def _toggle_pause(self):
        if not self.solving or not self.engine:
            return
        if self.paused:
            self.engine.resume()
            self.paused = False
            self.btn_pause.text = "Pause"
            self.status = "Resumed..."
        else:
            self.engine.pause()
            self.paused = True
            self.btn_pause.text = "Resume"
            self.status = "Paused"

    def _step_forward(self):
        if self.solving and self.engine and self.paused:
            self.engine.step_one()
            self._consume_step()

    # ── Step consumption ──

    def _consume_step(self):
        if not self.engine:
            return
        step = self.engine.get_next_step()
        if not step:
            return
        t = step["type"]
        if "metrics" in step:
            self.metrics = step["metrics"]

        if t == "init":
            # Apply initial domains
            domains = step.get("domains", {})
            for cell, dom in domains.items():
                if self.cells[cell]["state"] != "clue":
                    self.cells[cell]["domain"] = dom

        elif t == "ac3_reduce":
            cell = step["cell"]
            dom = step.get("domain", "")
            if self.cells[cell]["state"] != "clue":
                self.cells[cell]["domain"] = dom
                if len(dom) == 0:
                    self.cells[cell]["state"] = "conflict"
                    self._add_animation(cell, CLR_CONFLICT)
            # Update all domains
            self._apply_domains(step.get("domains"))

        elif t == "ac3_assign":
            cell = step["cell"]
            val = step.get("value", "")
            if self.cells[cell]["state"] != "clue":
                self.cells[cell]["value"] = val
                self.cells[cell]["domain"] = val
                self.cells[cell]["state"] = "ac3"
                self._add_animation(cell, CLR_AC3)
            self._apply_domains(step.get("domains"))

        elif t == "guess":
            cell = step["cell"]
            val = step.get("value", "")
            if self.cells[cell]["state"] != "clue":
                self.cells[cell]["value"] = val
                self.cells[cell]["domain"] = val
                self.cells[cell]["state"] = "guess"
                self._add_animation(cell, CLR_GUESS)
            self._apply_domains(step.get("domains"))

        elif t == "conflict":
            cell = step["cell"]
            if self.cells[cell]["state"] != "clue":
                self._add_animation(cell, CLR_CONFLICT)

        elif t == "backtrack":
            cell = step["cell"]
            if self.cells[cell]["state"] != "clue":
                self.cells[cell]["value"] = ""
                self.cells[cell]["state"] = "empty"
                self._add_animation(cell, CLR_CONFLICT)
            self._apply_domains(step.get("domains"))

        elif t == "done":
            self.solving = False
            if step.get("solved"):
                vals = step.get("values", {})
                for cell, val in vals.items():
                    if len(val) == 1:
                        self.cells[cell]["value"] = val
                        self.cells[cell]["domain"] = val
                        if self.cells[cell]["state"] == "empty":
                            self.cells[cell]["state"] = "ac3"
                self.status = "Solved!"
            else:
                self.status = "Could not fully solve"
            self.metrics = self.engine.get_metrics()

    def _apply_domains(self, domains):
        if not domains:
            return
        for cell, dom in domains.items():
            if self.cells[cell]["state"] not in ("clue",):
                self.cells[cell]["domain"] = dom
                # Auto-assign if domain reduced to 1 and no value yet
                if len(dom) == 1 and not self.cells[cell]["value"]:
                    self.cells[cell]["value"] = dom

    def _add_animation(self, cell, color):
        self.cell_animations[cell] = {"color": color, "alpha": 200, "time": time.time()}

    # ── Drawing ──

    def _draw_bg(self):
        self.screen.fill(BG_DARK)
        # Subtle gradient overlay
        for i in range(0, WIN_H, 2):
            a = max(0, 15 - i * 15 // WIN_H)
            if a > 0:
                s = pygame.Surface((WIN_W, 2), pygame.SRCALPHA)
                s.fill((100, 140, 255, a))
                self.screen.blit(s, (0, i))

    def _draw_title(self):
        ts = self.font_title.render("SUDOKU AI SOLVER", True, TEXT_WHITE)
        self.screen.blit(ts, (GRID_X, 20))
        # Subtitle
        sub = self.font_ui.render("Interactive Constraint Satisfaction Problem Visualizer", True, TEXT_DIM)
        self.screen.blit(sub, (GRID_X, 55))
        # Accent line
        pygame.draw.line(self.screen, ACCENT, (GRID_X, 80), (WIN_W - 20, 80), 2)

    def _draw_grid(self):
        # Grid background
        draw_rounded_rect(self.screen, (20, 20, 40), (GRID_X-4, GRID_Y-4, GRID_SIZE+8, GRID_SIZE+8), 10)

        from util import rows, cols
        now = time.time()

        for ri, r in enumerate(rows):
            for ci, c in enumerate(cols):
                key = r + c
                cell = self.cells[key]
                x = GRID_X + ci * CELL_SIZE
                y = GRID_Y + ri * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                # Cell background
                bg = CELL_BG
                if key == self.selected_cell:
                    bg = CELL_SELECT

                # Animation background tint
                if key in self.cell_animations:
                    anim = self.cell_animations[key]
                    elapsed = now - anim["time"]
                    fade = max(0, 1.0 - elapsed / 1.2)
                    if fade <= 0:
                        del self.cell_animations[key]
                    else:
                        ac = anim["color"]
                        bg = (int(bg[0] + (ac[0]-bg[0]) * fade * 0.4),
                              int(bg[1] + (ac[1]-bg[1]) * fade * 0.4),
                              int(bg[2] + (ac[2]-bg[2]) * fade * 0.4))

                # State-based persistent tint
                state = cell["state"]
                if state == "ac3" and key not in self.cell_animations:
                    bg = (bg[0]//2 + GREEN_DIM[0], bg[1]//2 + GREEN_DIM[1], bg[2]//2 + GREEN_DIM[2])
                elif state == "guess" and key not in self.cell_animations:
                    bg = (bg[0]//2 + BLUE_DIM[0], bg[1]//2 + BLUE_DIM[1], bg[2]//2 + BLUE_DIM[2])

                pygame.draw.rect(self.screen, bg, rect)

                # Cell content
                val = cell["value"]
                dom = cell["domain"]

                if val:
                    # Draw the digit
                    if state == "clue":
                        tc = CLR_CLUE
                    elif state == "ac3":
                        tc = CLR_AC3
                    elif state == "guess":
                        tc = CLR_GUESS
                    else:
                        tc = TEXT_WHITE
                    ts = self.font_cell.render(val, True, tc)
                    self.screen.blit(ts, (rect.centerx - ts.get_width()//2,
                                          rect.centery - ts.get_height()//2))
                elif dom and len(dom) > 1:
                    # Draw pencil marks in 3x3 sub-grid
                    pw = CELL_SIZE // 3
                    ph = CELL_SIZE // 3
                    for d in dom:
                        di = int(d) - 1  # 0-8
                        pr = di // 3
                        pc = di % 3
                        px_pos = x + pc * pw + pw // 2
                        py_pos = y + pr * ph + ph // 2
                        ps = self.font_pencil.render(d, True, CLR_PENCIL)
                        self.screen.blit(ps, (px_pos - ps.get_width()//2,
                                              py_pos - ps.get_height()//2))

        # Grid lines
        for i in range(10):
            thickness = 3 if i % 3 == 0 else 1
            color = BOX_LINE if i % 3 == 0 else GRID_LINE
            # Horizontal
            pygame.draw.line(self.screen, color,
                             (GRID_X, GRID_Y + i * CELL_SIZE),
                             (GRID_X + GRID_SIZE, GRID_Y + i * CELL_SIZE), thickness)
            # Vertical
            pygame.draw.line(self.screen, color,
                             (GRID_X + i * CELL_SIZE, GRID_Y),
                             (GRID_X + i * CELL_SIZE, GRID_Y + GRID_SIZE), thickness)

        # Selection highlight
        if self.selected_cell:
            from util import rows, cols
            ri = rows.index(self.selected_cell[0])
            ci = cols.index(self.selected_cell[1])
            sr = pygame.Rect(GRID_X + ci*CELL_SIZE, GRID_Y + ri*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, ACCENT, sr, 3, border_radius=2)

    def _draw_panel(self):
        px = PANEL_X
        # Panel background
        draw_rounded_rect(self.screen, (20, 20, 40, 180),
                          (px - 10, GRID_Y - 5, PANEL_W + 20, GRID_SIZE + 10), 12)

        # Dropdowns — draw base boxes first
        self.dd_file.draw_base(self.screen)
        self.dd_puzzle.draw_base(self.screen)
        self.dd_algo.draw_base(self.screen)

        # Speed slider
        self.slider_speed.draw(self.screen)

        # Buttons
        for btn in self.all_buttons:
            btn.draw(self.screen)

        # ── Metrics panel ──
        my = 520
        draw_rounded_rect(self.screen, (18, 18, 35, 200),
                          (px - 5, my, PANEL_W + 10, 168), 10)
        # Title
        mt = self.font_btn.render("METRICS", True, ACCENT)
        self.screen.blit(mt, (px + 5, my + 8))
        pygame.draw.line(self.screen, GRID_LINE, (px, my + 28), (px + PANEL_W, my + 28), 1)

        if self.batch_mode or self.batch_done:
            # Batch metrics
            items = [
                ("Time", f"{self.metrics['time']:.3f}s"),
                ("Progress", f"{self.batch_progress}/{self.batch_total}"),
                ("Solved", str(self.batch_solved)),
                ("Output", self.batch_output_file),
            ]
            for i, (lbl, val) in enumerate(items):
                yy = my + 36 + i * 26
                ls = self.font_metric_lbl.render(lbl, True, TEXT_DIM)
                self.screen.blit(ls, (px + 8, yy + 2))
                vs = self.font_metric_val.render(val, True, TEXT_WHITE)
                self.screen.blit(vs, (px + PANEL_W - vs.get_width() - 5, yy))
            # Progress bar
            bar_y = my + 36 + 4 * 26
            bar_w = PANEL_W - 10
            bar_h = 8
            pygame.draw.rect(self.screen, SLIDER_TRACK, (px + 5, bar_y, bar_w, bar_h), border_radius=4)
            if self.batch_total > 0:
                fill_w = int(bar_w * self.batch_progress / self.batch_total)
                pygame.draw.rect(self.screen, CLR_AC3, (px + 5, bar_y, fill_w, bar_h), border_radius=4)
        else:
            # Normal metrics
            items = [
                ("Time", f"{self.metrics['time']:.3f}s"),
                ("Nodes Explored", str(self.metrics['nodes'])),
                ("Guesses Made", str(self.metrics['guesses'])),
                ("Backtracks", str(self.metrics['backtracks'])),
            ]
            for i, (lbl, val) in enumerate(items):
                yy = my + 36 + i * 26
                ls = self.font_metric_lbl.render(lbl, True, TEXT_DIM)
                self.screen.blit(ls, (px + 8, yy + 2))
                vs = self.font_metric_val.render(val, True, TEXT_WHITE)
                self.screen.blit(vs, (px + PANEL_W - vs.get_width() - 5, yy))

        # Status bar
        sy = my + 140
        pygame.draw.line(self.screen, GRID_LINE, (px, sy), (px + PANEL_W, sy), 1)
        if "Solved" in self.status or "Done" in self.status:
            sc = CLR_AC3
        elif "Solving" in self.status or "Batch" in self.status:
            sc = ACCENT
        else:
            sc = TEXT_DIM
        ss = self.font_status.render(self.status, True, sc)
        self.screen.blit(ss, (px + 8, sy + 5))

    def _draw_legend(self):
        lx = GRID_X
        ly = GRID_Y + GRID_SIZE + 12
        items = [
            (CLR_CLUE, "Clue"), (CLR_AC3, "AC-3"), (CLR_GUESS, "Guess"), (CLR_CONFLICT, "Conflict")
        ]
        for i, (color, label) in enumerate(items):
            x = lx + i * 130
            pygame.draw.rect(self.screen, color, (x, ly + 2, 12, 12), border_radius=2)
            ts = self.font_ui.render(label, True, TEXT_DIM)
            self.screen.blit(ts, (x + 18, ly))

    # ── Event handling ──

    def _handle_grid_click(self, pos):
        if self.solving:
            return
        mx, my = pos
        if GRID_X <= mx < GRID_X + GRID_SIZE and GRID_Y <= my < GRID_Y + GRID_SIZE:
            ci = (mx - GRID_X) // CELL_SIZE
            ri = (my - GRID_Y) // CELL_SIZE
            from util import rows, cols
            key = rows[ri] + cols[ci]
            if self.cells[key]["state"] != "clue":
                self.selected_cell = key
            else:
                self.selected_cell = key  # allow selecting clues too (just won't edit)
        else:
            self.selected_cell = None

    def _handle_key_input(self, event):
        if not self.selected_cell or self.solving:
            return
        cell = self.cells[self.selected_cell]
        if cell["state"] == "clue":
            return
        if event.key in range(pygame.K_1, pygame.K_9 + 1):
            digit = str(event.key - pygame.K_0)
            cell["value"] = digit
            cell["domain"] = digit
            cell["state"] = "empty"
        elif event.key in range(pygame.K_KP1, pygame.K_KP9 + 1):
            digit = str(event.key - pygame.K_KP0)
            cell["value"] = digit
            cell["domain"] = digit
            cell["state"] = "empty"
        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0):
            cell["value"] = ""
            cell["domain"] = "123456789"
            cell["state"] = "empty"

    # ── Main loop ──

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)

            # Consume solver steps based on speed
            if self.solving and self.engine and not self.paused:
                self.step_timer += dt
                delay = self.slider_speed.val
                while self.step_timer >= delay:
                    self.step_timer -= delay
                    self._consume_step()
                # Update metrics in real time
                if self.engine:
                    self.metrics = self.engine.get_metrics()

            # Check if engine is done
            if self.engine and self.engine.is_done and self.solving:
                # Drain remaining steps
                while True:
                    s = self.engine.get_next_step()
                    if not s:
                        break
                    step_data = s
                    if "metrics" in step_data:
                        self.metrics = step_data["metrics"]
                    # Process the step
                    t = step_data["type"]
                    if t == "done":
                        self.solving = False
                        if step_data.get("solved"):
                            vals = step_data.get("values", {})
                            for cell, val in vals.items():
                                if len(val) == 1:
                                    self.cells[cell]["value"] = val
                                    self.cells[cell]["domain"] = val
                                    if self.cells[cell]["state"] == "empty":
                                        self.cells[cell]["state"] = "ac3"
                            self.status = "Solved!"
                        else:
                            self.status = "Could not fully solve"
                        self.metrics = self.engine.get_metrics()

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._stop_solver()
                    running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._stop_solver()
                        running = False
                        break
                    self._handle_key_input(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_grid_click(event.pos)

                # ── UI event handling ──
                open_dd = None
                for dd in self.all_dropdowns:
                    if dd.open:
                        open_dd = dd
                        break

                event_consumed = False

                # If a dropdown is open, give it priority for all clicks
                if open_dd:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        result = open_dd.handle_event(event)
                        if result:  # item was selected
                            if open_dd is self.dd_file:
                                self._load_puzzle_file(open_dd.selected)
                            elif open_dd is self.dd_puzzle:
                                self._load_puzzle(open_dd.selected)
                        event_consumed = True
                    elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
                        open_dd.handle_event(event)
                        event_consumed = True

                if not event_consumed:
                    # Handle dropdown toggles (clicking the main box)
                    for dd in self.all_dropdowns:
                        if dd.handle_event(event):
                            if dd is self.dd_file:
                                self._load_puzzle_file(dd.selected)
                            elif dd is self.dd_puzzle:
                                self._load_puzzle(dd.selected)
                            break
                        # If this dropdown just opened, close all others
                        if dd.open:
                            for other in self.all_dropdowns:
                                if other is not dd:
                                    other.open = False
                                    other.scroll_offset = 0

                    # Slider and buttons
                    self.slider_speed.handle_event(event)
                    if self.btn_solve.handle_event(event):
                        self._start_solver()
                    if self.btn_pause.handle_event(event):
                        self._toggle_pause()
                    if self.btn_step.handle_event(event):
                        self._step_forward()
                    if self.btn_reset.handle_event(event):
                        self._reset_board()
                    if self.btn_clear.handle_event(event):
                        self._clear_board()

                # Always let slider track drags and buttons track hover
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                    self.slider_speed.handle_event(event)
                    for btn in self.all_buttons:
                        btn.handle_event(event)

            # Update button states
            self.btn_solve.enabled = not self.solving
            self.btn_pause.enabled = self.solving
            self.btn_step.enabled = self.solving and self.paused
            self.btn_reset.enabled = not self.solving and bool(self.current_grid)
            self.btn_clear.enabled = not self.solving
            self.btn_pause.active = self.paused

            # Draw
            self._draw_bg()
            self._draw_title()
            self._draw_grid()
            self._draw_legend()
            self._draw_panel()

            # Draw open dropdown list LAST (on top of everything)
            for dd in self.all_dropdowns:
                dd.draw_list(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = SudokuGUI()
    app.run()
