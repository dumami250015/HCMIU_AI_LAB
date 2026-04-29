# 🧩 Sudoku Solving Agent

An AI-powered Sudoku solver built as a **Constraint Satisfaction Problem (CSP)** using **AC-3** constraint propagation and **Backtracking Search** with MRV heuristic and Forward Checking. Includes an interactive Pygame GUI for step-by-step visualization.

## 📋 Prerequisites

- **Python** 3.8 or higher
- **Pygame** library

## ⚙️ Installation

1. **Clone or download** this project to your local machine.

2. **Install dependencies**:

   ```bash
   pip install pygame
   ```

   > No other external libraries are required — the solver uses only Python standard library modules (`argparse`, `time`, `copy`, `threading`, `queue`).

## 🚀 How to Run

### Interactive GUI

Launch the graphical interface for visual, step-by-step solving:

```bash
python gui.py
```

**GUI Controls:**

| Control | Action |
|---------|--------|
| **Puzzle File** dropdown | Select a puzzle dataset (`euler` or `magictour`) |
| **Puzzle #** dropdown | Pick an individual puzzle or "Solve All" |
| **Algorithm** dropdown | Choose `AC-3 + Backtracking`, `Backtracking Only`, or `AC-3 Only` |
| **Solve** button | Start solving the selected puzzle |
| **Pause / Resume** button | Pause or resume the animation |
| **Step** button | Advance one step at a time (while paused) |
| **Reset** button | Reload the current puzzle |
| **Clear** button | Clear the entire board |
| **Speed slider** | Adjust animation delay (5–500 ms per step) |

### Command-Line Batch Solver

Solve all puzzles in a file and write results to `output.txt`:

```bash
python sudoku.py --inputFile data/euler.txt
```

```bash
python sudoku.py --inputFile data/magictour.txt
```

### Benchmark

Run the performance benchmark script to collect per-puzzle timing statistics:

```bash
python benchmark.py
```

## 📁 Project Structure

```
Lab45/
├── gui.py              # Interactive Pygame GUI application
├── sudoku.py           # Command-line batch solver entry point
├── search.py           # Core algorithms: AC-3, Backtracking, MRV, Forward Checking
├── csp.py              # CSP class: variables, domains, constraints, peers
├── util.py             # Constants (rows, cols, digits, squares) and utilities
├── solver_engine.py    # Instrumented solver engine for GUI visualization
├── ui_components.py    # Reusable Pygame UI widgets (Button, Dropdown, Slider)
├── benchmark.py        # Performance benchmarking script
├── data/
│   ├── euler.txt       # 50 Project Euler puzzles
│   └── magictour.txt   # 95 Magic Tour puzzles
├── EulerSolutions.txt  # Solved output for Euler puzzles
├── MagicTourSolutions.txt  # Solved output for Magic Tour puzzles
├── REPORT.md           # Detailed lab report with algorithm analysis
└── README.md           # This file
```

## 🧠 Algorithms

| Algorithm | Description |
|-----------|-------------|
| **AC-3** | Arc Consistency preprocessing — prunes infeasible values from variable domains before search |
| **Backtracking Search** | Depth-first search with recursive assignment and domain restoration on failure |
| **MRV Heuristic** | Minimum Remaining Values — selects the most constrained variable first (fail-first) |
| **Forward Checking** | After each assignment, propagates constraints to peers and recursively reduces singleton domains |

## 📊 Input Format

Each puzzle is an **81-character string** where:
- Digits `1`–`9` represent given clues
- `0` represents an empty cell

Cells are read **left-to-right, top-to-bottom** (row A1–A9, then B1–B9, ..., I1–I9).

**Example:**
```
003020600900305001001806400008102900700000008006708200002609500800203009005010300
```

## 📝 Output Format

Solved puzzles are written as 81-character strings in the same format:
```
483921657967345821251876493548132976729564138136798245372689514814253769695417382
```
