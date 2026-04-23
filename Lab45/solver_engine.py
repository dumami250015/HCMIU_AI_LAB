"""
Instrumented solver engine for GUI visualization.
Wraps the existing CSP/search logic and emits step-by-step events.
"""

import threading
import queue
import time
from copy import deepcopy
from csp import csp
from util import squares, rows, cols, digits


class SolverEngine:
    """
    Runs a Sudoku solver in a background thread, pushing visual step events
    into a queue that the GUI consumes at its own pace.
    """

    def __init__(self, grid_string, algorithm="ac3+backtracking"):
        """
        grid_string: 81-char string of digits (0 = empty)
        algorithm: one of 'backtracking', 'ac3', 'ac3+backtracking'
        """
        self.grid_string = grid_string
        self.algorithm = algorithm

        # Step queue for GUI consumption
        self._steps = queue.Queue()

        # Threading controls
        self._pause_event = threading.Event()
        self._pause_event.set()  # starts unpaused
        self._step_event = threading.Event()
        self._cancel = False
        self._thread = None

        # Metrics
        self.nodes_explored = 0
        self.guesses_made = 0
        self.backtracks = 0
        self.start_time = 0
        self.elapsed_time = 0
        self.is_done = False
        self.solved = False

    def start(self):
        """Launch the solver in a background thread."""
        self._cancel = False
        self.is_done = False
        self.nodes_explored = 0
        self.guesses_made = 0
        self.backtracks = 0
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Main solver thread entry point."""
        try:
            puzzle = csp(grid=self.grid_string)
            # Record original clues
            original_clues = {}
            for var in squares:
                if len(puzzle.values[var]) == 1:
                    original_clues[var] = puzzle.values[var]
            self._emit("init", clues=original_clues,
                       domains={v: puzzle.values[v] for v in squares})

            if self.algorithm == "ac3":
                consistent = self._ac3(puzzle)
                if consistent:
                    # Check if fully solved
                    solved_vals = {}
                    all_solved = True
                    for var in squares:
                        if len(puzzle.values[var]) == 1:
                            solved_vals[var] = puzzle.values[var]
                        else:
                            all_solved = False
                    self.solved = all_solved
                    self._emit("done", solved=all_solved, values=dict(puzzle.values))
                else:
                    self.solved = False
                    self._emit("done", solved=False, values=dict(puzzle.values))

            elif self.algorithm == "backtracking":
                assignment = {}
                for var in squares:
                    if len(puzzle.values[var]) == 1:
                        assignment[var] = puzzle.values[var]
                result = self._backtrack(assignment, puzzle, original_clues)
                self.solved = result != "FAILURE"
                if self.solved:
                    self._emit("done", solved=True, values=result)
                else:
                    self._emit("done", solved=False, values=dict(puzzle.values))

            elif self.algorithm == "ac3+backtracking":
                consistent = self._ac3(puzzle)
                if not consistent:
                    self.solved = False
                    self._emit("done", solved=False, values=dict(puzzle.values))
                else:
                    # Check if AC3 already solved it
                    all_solved = all(len(puzzle.values[v]) == 1 for v in squares)
                    if all_solved:
                        self.solved = True
                        self._emit("done", solved=True, values=dict(puzzle.values))
                    else:
                        # Continue with backtracking
                        assignment = {}
                        for var in squares:
                            if len(puzzle.values[var]) == 1:
                                assignment[var] = puzzle.values[var]
                        result = self._backtrack(assignment, puzzle, original_clues)
                        self.solved = result != "FAILURE"
                        if self.solved:
                            self._emit("done", solved=True, values=result)
                        else:
                            self._emit("done", solved=False, values=dict(puzzle.values))

        except Exception as e:
            self._emit("error", message=str(e))

        self.elapsed_time = time.time() - self.start_time
        self.is_done = True

    def _emit(self, step_type, **data):
        """Push a step event and respect pause/step controls."""
        if self._cancel:
            return
        data["type"] = step_type
        data["metrics"] = self.get_metrics()
        self._steps.put(data)
        # Wait if paused (but let 'done' and 'init' through immediately)
        if step_type not in ("done", "init", "error"):
            self._wait_if_paused()

    def _wait_if_paused(self):
        """Block the solver thread while paused, unless stepping."""
        while not self._pause_event.is_set() and not self._cancel:
            # Wait for either resume or a single step
            if self._step_event.wait(timeout=0.05):
                self._step_event.clear()
                return
        # Small yield to let GUI consume steps
        time.sleep(0.001)

    # ── AC-3 (instrumented) ──────────────────────────────────────────

    def _ac3(self, puzzle):
        """Instrumented AC-3 algorithm."""
        q = list(puzzle.constraints)
        while q and not self._cancel:
            (xi, xj) = q.pop(0)
            if self._revise(puzzle, xi, xj):
                if len(puzzle.values[xi]) == 0:
                    return False
                if len(puzzle.values[xi]) == 1:
                    self._emit("ac3_assign", cell=xi,
                               value=puzzle.values[xi],
                               domains={v: puzzle.values[v] for v in squares})
                for peer in puzzle.peers[xi]:
                    if peer != xj:
                        q.append((peer, xi))
        return True

    def _revise(self, puzzle, xi, xj):
        """Instrumented Revise for AC-3."""
        revised = False
        for value in list(puzzle.values[xi]):
            if not any(v != value for v in puzzle.values[xj]):
                old_domain = puzzle.values[xi]
                puzzle.values[xi] = puzzle.values[xi].replace(value, '')
                revised = True
                self.nodes_explored += 1
                self._emit("ac3_reduce", cell=xi,
                           domain=puzzle.values[xi],
                           removed=value,
                           domains={v: puzzle.values[v] for v in squares})
        return revised

    # ── Backtracking (instrumented) ──────────────────────────────────

    def _backtrack(self, assignment, puzzle, original_clues):
        """Instrumented recursive backtracking."""
        if self._cancel:
            return "FAILURE"

        if set(assignment.keys()) == set(squares):
            return assignment

        self.nodes_explored += 1

        # MRV heuristic
        unassigned = {s: len(puzzle.values[s]) for s in puzzle.values
                      if s not in assignment}
        var = min(unassigned, key=unassigned.get)

        for value in puzzle.values[var]:
            if self._cancel:
                return "FAILURE"

            # Check consistency
            consistent = True
            for neighbor in puzzle.peers[var]:
                if neighbor in assignment and assignment[neighbor] == value:
                    consistent = False
                    break

            if not consistent:
                self._emit("conflict", cell=var, value=value,
                           domains={v: puzzle.values[v] for v in squares})
                continue

            # Make a guess
            self.guesses_made += 1
            assignment[var] = value
            saved_values = deepcopy(puzzle.values)

            source = "guess"
            if var in original_clues:
                source = "clue"
            self._emit("guess", cell=var, value=value, source=source,
                       domains={v: puzzle.values[v] for v in squares})

            # Forward checking (inference)
            inferences = self._inference(assignment, {}, puzzle, var, value)
            if inferences != "FAILURE":
                result = self._backtrack(assignment, puzzle, original_clues)
                if result != "FAILURE":
                    return result

            # Backtrack
            del assignment[var]
            puzzle.values = saved_values
            self.backtracks += 1
            self._emit("backtrack", cell=var, value=value,
                       domains={v: puzzle.values[v] for v in squares})

        return "FAILURE"

    def _inference(self, assignment, inferences, puzzle, var, value):
        """Instrumented forward checking."""
        inferences[var] = value

        for neighbor in puzzle.peers[var]:
            if neighbor not in assignment and value in puzzle.values[neighbor]:
                if len(puzzle.values[neighbor]) == 1:
                    return "FAILURE"

                remaining = puzzle.values[neighbor] = \
                    puzzle.values[neighbor].replace(value, "")

                if len(remaining) == 1:
                    self._emit("ac3_assign", cell=neighbor,
                               value=remaining,
                               domains={v: puzzle.values[v] for v in squares})
                    flag = self._inference(assignment, inferences,
                                           puzzle, neighbor, remaining)
                    if flag == "FAILURE":
                        return "FAILURE"

        return inferences

    # ── Public API ───────────────────────────────────────────────────

    def get_next_step(self):
        """Non-blocking: get next step or None."""
        try:
            return self._steps.get_nowait()
        except queue.Empty:
            return None

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def step_one(self):
        self._step_event.set()

    def cancel(self):
        self._cancel = True
        self._pause_event.set()  # unblock thread so it can exit

    def get_metrics(self):
        elapsed = self.elapsed_time if self.is_done else (
            time.time() - self.start_time if self.start_time else 0)
        return {
            "time": elapsed,
            "nodes": self.nodes_explored,
            "guesses": self.guesses_made,
            "backtracks": self.backtracks,
        }
