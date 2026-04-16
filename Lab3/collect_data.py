"""
Collect performance data for BFS and DFS. Suppresses all debug output.
"""
import sys, os, io
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

    if algorithm == "DFS":
        agent.bfs = agent.dfs

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
    print(f"\n{'='*100}")
    print(f"WALL BIAS = {wall_bias}, DIRT BIAS = {dirt_bias}, SEED = {FIXED_SEED}")
    print(f"{'='*100}")

    bfs_results = []
    dfs_results = []

    for w, h in GRID_SIZES:
        bfs_result = run_experiment(w, h, "BFS", dirt_bias, wall_bias)
        bfs_results.append(bfs_result)
        dfs_result = run_experiment(w, h, "DFS", dirt_bias, wall_bias)
        dfs_results.append(dfs_result)

    print(f"\n{'':15} | {'Breadth-First Search':^40} | {'Depth-First Search':^40}")
    print(f"{'Environment':15} | {'#nodes':>8} {'Steps':>8} {'Score':>8} {'Optimal?':>10} | {'#nodes':>8} {'Steps':>8} {'Score':>8} {'Optimal?':>10}")
    print("-" * 100)

    for bfs, dfs in zip(bfs_results, dfs_results):
        bfs_fin = "" if bfs["terminated"] else "*"
        dfs_fin = "" if dfs["terminated"] else "*"
        print(f"{bfs['grid']:15} | {bfs['nodes_explored']:>8} {bfs['steps']:>7}{bfs_fin} {bfs['score']:>8} {'Yes':>10} | {dfs['nodes_explored']:>8} {dfs['steps']:>7}{dfs_fin} {dfs['score']:>8} {'No':>10}")

    print("=" * 100)
    if any(not r["terminated"] for r in bfs_results + dfs_results):
        print("* = Agent did not finish (hit iteration limit)")


def main():
    run_suite(dirt_bias=0.5, wall_bias=0.0)
    run_suite(dirt_bias=0.5, wall_bias=0.2)


if __name__ == "__main__":
    main()
