"""
Benchmark script to collect per-puzzle statistics for the report.
"""
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csp import csp as CSP
from search import Backtracking_Search, AC3
from util import squares
from copy import deepcopy

def count_clues(grid_str):
    return sum(1 for c in grid_str[:81] if c != '0')

def benchmark_dataset(filename, label):
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    fpath = os.path.join(data_dir, filename)
    with open(fpath) as f:
        puzzles = [line.strip() for line in f if line.strip() and len(line.strip()) >= 81]

    print(f"\n{'='*70}")
    print(f"  BENCHMARK: {label} ({len(puzzles)} puzzles)")
    print(f"{'='*70}")
    print(f"{'#':>4} | {'Clues':>5} | {'Time (s)':>10} | {'Status':>8}")
    print(f"{'-'*4}-+-{'-'*5}-+-{'-'*10}-+-{'-'*8}")

    times = []
    clues_list = []
    solved_count = 0
    total_start = time.time()

    for i, grid in enumerate(puzzles):
        clues = count_clues(grid)
        clues_list.append(clues)
        start = time.time()
        puzzle = CSP(grid=grid)
        result = Backtracking_Search(puzzle)
        elapsed = time.time() - start
        times.append(elapsed)

        if result != "FAILURE":
            fully_solved = all(len(result[var]) == 1 for var in squares)
            if fully_solved:
                solved_count += 1
                status = "OK"
            else:
                status = "PARTIAL"
        else:
            status = "FAIL"

        print(f"{i+1:>4} | {clues:>5} | {elapsed:>10.4f} | {status:>8}")

    total_time = time.time() - total_start

    print(f"\n{'='*70}")
    print(f"  SUMMARY: {label}")
    print(f"{'='*70}")
    print(f"  Total puzzles:      {len(puzzles)}")
    print(f"  Solved:             {solved_count}/{len(puzzles)} ({100*solved_count/len(puzzles):.1f}%)")
    print(f"  Total time:         {total_time:.4f} s")
    print(f"  Average time:       {sum(times)/len(times):.4f} s")
    print(f"  Min time:           {min(times):.4f} s")
    print(f"  Max time:           {max(times):.4f} s")
    print(f"  Median time:        {sorted(times)[len(times)//2]:.4f} s")
    print(f"  Avg clues:          {sum(clues_list)/len(clues_list):.1f}")
    print(f"  Min clues:          {min(clues_list)}")
    print(f"  Max clues:          {max(clues_list)}")

    # Distribution of times
    fast = sum(1 for t in times if t < 0.05)
    medium = sum(1 for t in times if 0.05 <= t < 0.5)
    slow = sum(1 for t in times if 0.5 <= t < 2.0)
    very_slow = sum(1 for t in times if t >= 2.0)
    print(f"\n  Time distribution:")
    print(f"    < 50ms:           {fast} puzzles")
    print(f"    50-500ms:         {medium} puzzles")
    print(f"    500ms-2s:         {slow} puzzles")
    print(f"    > 2s:             {very_slow} puzzles")

    return times, clues_list, solved_count

if __name__ == "__main__":
    t1, c1, s1 = benchmark_dataset("euler.txt", "Project Euler")
    t2, c2, s2 = benchmark_dataset("magictour.txt", "Magic Tour")

    print(f"\n{'='*70}")
    print(f"  COMPARISON")
    print(f"{'='*70}")
    print(f"  {'Metric':<25} | {'Euler':>12} | {'Magic Tour':>12}")
    print(f"  {'-'*25}-+-{'-'*12}-+-{'-'*12}")
    print(f"  {'Puzzles':<25} | {len(t1):>12} | {len(t2):>12}")
    print(f"  {'Solved':<25} | {s1:>12} | {s2:>12}")
    print(f"  {'Avg Time (s)':<25} | {sum(t1)/len(t1):>12.4f} | {sum(t2)/len(t2):>12.4f}")
    print(f"  {'Min Time (s)':<25} | {min(t1):>12.4f} | {min(t2):>12.4f}")
    print(f"  {'Max Time (s)':<25} | {max(t1):>12.4f} | {max(t2):>12.4f}")
    print(f"  {'Avg Clues':<25} | {sum(c1)/len(c1):>12.1f} | {sum(c2)/len(c2):>12.1f}")
