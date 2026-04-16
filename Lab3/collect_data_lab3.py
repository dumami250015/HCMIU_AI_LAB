"""
Collect performance data for Greedy Best-First Search and A* Search.
Suppresses all debug output.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Suppress all print output from the agent's debug prints
import builtins
_original_print = builtins.print
def silent_print(*args, **kwargs):
    pass

from lab3.vacuum import VacuumEnvironment
from lab3.myvacuumagent import MyVacuumAgent

FIXED_SEED = 1337
GRID_SIZES = [(5, 5), (10, 10), (15, 15), (20, 20)]


def run_experiment(width, height, algorithm, dirt_bias, wall_bias):
    logs = []
    def log(msg):
        logs.append(str(msg))

    # Suppress debug prints during simulation
    builtins.print = silent_print

    venv = VacuumEnvironment(width, height, dirt_bias, wall_bias, FIXED_SEED)
    agent = MyVacuumAgent(width, height, log)
    agent.current_algorithm = algorithm

    venv.add_thing(agent)

    max_steps = width * height * 100
    for _ in range(max_steps):
        if agent.terminated:
            break
        venv.step()

    # Restore print
    builtins.print = _original_print

    return {
        "algorithm": algorithm,
        "grid": f"{width}x{height}",
        "nodes_explored": agent.nodes_explored,
        "steps": agent.steps,
        "score": agent.score,
        "cleaned": agent.cleaned,
        "terminated": agent.terminated,
    }


def run_suite(dirt_bias, wall_bias):
    print(f"\n{'='*110}")
    print(f"WALL BIAS = {wall_bias}, DIRT BIAS = {dirt_bias}, SEED = {FIXED_SEED}")
    print(f"{'='*110}")

    greedy_results = []
    astar_results = []

    for w, h in GRID_SIZES:
        greedy_result = run_experiment(w, h, "Greedy", dirt_bias, wall_bias)
        greedy_results.append(greedy_result)
        astar_result = run_experiment(w, h, "A*", dirt_bias, wall_bias)
        astar_results.append(astar_result)

    print(f"\n{'':15} | {'Greedy Best-First Search':^45} | {'A* Search':^45}")
    print(f"{'Environment':15} | {'#nodes':>8} {'Steps':>8} {'Score':>8} {'Cleaned':>8} {'Done?':>6} | {'#nodes':>8} {'Steps':>8} {'Score':>8} {'Cleaned':>8} {'Done?':>6}")
    print("-" * 110)

    for g, a in zip(greedy_results, astar_results):
        g_done = "Yes" if g["terminated"] else "No*"
        a_done = "Yes" if a["terminated"] else "No*"
        print(f"{g['grid']:15} | {g['nodes_explored']:>8} {g['steps']:>8} {g['score']:>8} {g['cleaned']:>8} {g_done:>6} | {a['nodes_explored']:>8} {a['steps']:>8} {a['score']:>8} {a['cleaned']:>8} {a_done:>6}")

    print("=" * 110)
    if any(not r["terminated"] for r in greedy_results + astar_results):
        print("* = Agent did not finish (hit iteration limit)")


def main():
    run_suite(dirt_bias=0.5, wall_bias=0.0)
    run_suite(dirt_bias=0.5, wall_bias=0.2)


if __name__ == "__main__":
    main()
