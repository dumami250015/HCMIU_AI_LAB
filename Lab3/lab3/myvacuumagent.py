import heapq
from lab3.vacuum import *

DEBUG_OPT_DENSEWORLDMAP = False

AGENT_STATE_UNKNOWN = 0
AGENT_STATE_WALL = 1
AGENT_STATE_CLEAR = 2
AGENT_STATE_DIRT = 3
AGENT_STATE_HOME = 4

AGENT_DIRECTION_NORTH = 0
AGENT_DIRECTION_EAST = 1
AGENT_DIRECTION_SOUTH = 2
AGENT_DIRECTION_WEST = 3

def direction_to_string(cdr):
    cdr %= 4
    return  "NORTH" if cdr == AGENT_DIRECTION_NORTH else\
            "EAST"  if cdr == AGENT_DIRECTION_EAST else\
            "SOUTH" if cdr == AGENT_DIRECTION_SOUTH else\
            "WEST" #if dir == AGENT_DIRECTION_WEST

"""
Internal state of a vacuum agent
"""
class MyAgentState:

    def __init__(self, width, height):

        # Initialize perceived world state
        self.world = [[AGENT_STATE_UNKNOWN for _ in range(height)] for _ in range(width)]
        self.world[1][1] = AGENT_STATE_HOME

        # Agent internal state
        self.last_action = ACTION_NOP
        self.direction = AGENT_DIRECTION_EAST
        self.pos_x = 1
        self.pos_y = 1

        # Metadata
        self.world_width = width
        self.world_height = height
        print(width, height)

    """
    Update perceived agent location
    """
    def update_position(self, bump):
        if self.last_action != ACTION_FORWARD:
            return
        if bump:
            return  # do NOT move into wall

        if self.direction == AGENT_DIRECTION_EAST:
            self.pos_x += 1
        elif self.direction == AGENT_DIRECTION_SOUTH:
            self.pos_y += 1
        elif self.direction == AGENT_DIRECTION_WEST:
            self.pos_x -= 1
        elif self.direction == AGENT_DIRECTION_NORTH:
            self.pos_y -= 1

    """
    Update perceived or inferred information about a part of the world
    """
    def update_world(self, x, y, info):
        if 0 <= x < self.world_width and 0 <= y < self.world_height:
            self.world[x][y] = info

    """
    Dumps a map of the world as the agent knows it
    """
    def print_world_debug(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y] == AGENT_STATE_UNKNOWN:
                    print("?" if DEBUG_OPT_DENSEWORLDMAP else " ? ", end="")
                elif self.world[x][y] == AGENT_STATE_WALL:
                    print("#" if DEBUG_OPT_DENSEWORLDMAP else " # ", end="")
                elif self.world[x][y] == AGENT_STATE_CLEAR:
                    print("." if DEBUG_OPT_DENSEWORLDMAP else " . ", end="")
                elif self.world[x][y] == AGENT_STATE_DIRT:
                    print("D" if DEBUG_OPT_DENSEWORLDMAP else " D ", end="")
                elif self.world[x][y] == AGENT_STATE_HOME:
                    print("H" if DEBUG_OPT_DENSEWORLDMAP else " H ", end="")

            print() # Newline
        print() # Delimiter post-print


"""
Vacuum agent
"""
class MyVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)

        self.initial_random_actions = 10
        self.iteration_counter = world_width * world_height * 10
        self.state = MyAgentState(world_width, world_height)
        self.log = log

        #add new params for Lab3
        self.route = []  # acts like stack
        self.home_pos = (1, 1)
        self.steps = 0
        self.cleaned = 0
        self.score = -1000
        self.terminated = False
        
        # NOTE: You can change this to "BFS", "DFS", "Greedy", or "A*"
        self.current_algorithm = "A*" 
        self.nodes_explored = 0

    def update_score(self, action, shutdown=False):
        if self.terminated:
            return # prevent ANY further scoring

        if shutdown:
            self.score += 1000
            self.terminated = True  # lock system
        elif action == ACTION_SUCK:
            self.score += 100
        else:
            self.score -= 1

    def move_to_random_start_position(self, bump):
        action = random()

        self.initial_random_actions -= 1
        self.state.update_position(bump)

        if action < 0.1666666:   # 1/6 chance
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            self.update_score(ACTION_TURN_LEFT)
            return ACTION_TURN_LEFT
        elif action < 0.3333333: # 1/6 chance
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            self.update_score(ACTION_TURN_RIGHT)
            return ACTION_TURN_RIGHT
        else:                    # 4/6 chance
            self.state.last_action = ACTION_FORWARD
            self.update_score(ACTION_FORWARD)
            return ACTION_FORWARD

    # ---------------- SEARCH ALGORITHMS ---------------- #

    def bfs(self, return_home=False):
        start = (self.state.pos_x, self.state.pos_y)
        queue = [(start, [])]
        visited = set()
        visited.add(start)

        while queue:
            current, path = queue.pop(0) # FIFO queue for Breadth-First Search
            cx, cy = current
            self.nodes_explored += 1

            if not return_home:
                if self.state.world[cx][cy] == AGENT_STATE_UNKNOWN:
                    self.route = path
                    return
            else:
                if current == self.home_pos:
                    self.route = path
                    return

            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.state.world_width and 0 <= ny < self.state.world_height:
                    if (nx, ny) not in visited:
                        if self.state.world[nx][ny] != AGENT_STATE_WALL:
                            visited.add((nx, ny))
                            queue.append(((nx, ny), path + [(nx, ny)]))
        self.route = []

    def dfs(self, return_home=False):
        start = (self.state.pos_x, self.state.pos_y)
        stack = [(start, [])]
        visited = set()

        while stack:
            current, path = stack.pop() # LIFO stack for Depth-First Search
            cx, cy = current

            if current in visited:
                continue
            visited.add(current)
            self.nodes_explored += 1

            if not return_home:
                if self.state.world[cx][cy] == AGENT_STATE_UNKNOWN:
                    self.route = path
                    return
            else:
                if current == self.home_pos:
                    self.route = path
                    return

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.state.world_width and 0 <= ny < self.state.world_height:
                    if (nx, ny) not in visited:
                        if self.state.world[nx][ny] != AGENT_STATE_WALL:
                            stack.append(((nx, ny), path + [(nx, ny)]))
                            
        self.route = []
        
    def get_unknown_tiles(self):
        """Helper to collect all currently unknown tiles for heuristics"""
        unknowns = []
        for x in range(self.state.world_width):
            for y in range(self.state.world_height):
                if self.state.world[x][y] == AGENT_STATE_UNKNOWN:
                    unknowns.append((x, y))
        return unknowns

    def best_first_search(self, return_home=False):
        """Greedy Best-First Search evaluating nodes solely based on h(n)"""
        start = (self.state.pos_x, self.state.pos_y)
        unknowns = [] if return_home else self.get_unknown_tiles()

        # Heuristic h(n)
        def h(cx, cy):
            if return_home:
                hx, hy = self.home_pos
                return abs(cx - hx) + abs(cy - hy)
            else:
                if not unknowns: return 0
                return min(abs(cx - ux) + abs(cy - uy) for ux, uy in unknowns)

        # Queue stores tuples of (h_score, current_position, path_to_get_there)
        queue = []
        heapq.heappush(queue, (h(start[0], start[1]), start, []))
        visited = set([start])

        while queue:
            current_h, current, path = heapq.heappop(queue)
            cx, cy = current
            self.nodes_explored += 1

            # Goal Check
            if not return_home:
                if self.state.world[cx][cy] == AGENT_STATE_UNKNOWN:
                    self.route = path
                    return
            else:
                if current == self.home_pos:
                    self.route = path
                    return

            # Explore 4 directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                
                if 0 <= nx < self.state.world_width and 0 <= ny < self.state.world_height:
                    if (nx, ny) not in visited and self.state.world[nx][ny] != AGENT_STATE_WALL:
                        visited.add((nx, ny))
                        next_h = h(nx, ny)
                        heapq.heappush(queue, (next_h, (nx, ny), path + [(nx, ny)]))
                        
        self.route = []

    def a_star_search(self, return_home=False):
        """A* Search evaluating nodes based on f(n) = g(n) + h(n)"""
        start = (self.state.pos_x, self.state.pos_y)
        unknowns = [] if return_home else self.get_unknown_tiles()

        # Heuristic h(n)
        def h(cx, cy):
            if return_home:
                hx, hy = self.home_pos
                return abs(cx - hx) + abs(cy - hy)
            else:
                if not unknowns: return 0
                return min(abs(cx - ux) + abs(cy - uy) for ux, uy in unknowns)

        # Queue stores tuples of (f_score, g_score, current_position, path_to_get_there)
        queue = []
        g_start = 0
        h_start = h(start[0], start[1])
        heapq.heappush(queue, (g_start + h_start, g_start, start, []))
        
        # Track the best (lowest) g_cost to reach a specific cell
        g_costs = {start: 0}

        while queue:
            f, g, current, path = heapq.heappop(queue)
            cx, cy = current

            # Skip if we already found a better path to this node
            if g > g_costs.get(current, float('inf')):
                continue

            self.nodes_explored += 1

            # Goal Check
            if not return_home:
                if self.state.world[cx][cy] == AGENT_STATE_UNKNOWN:
                    self.route = path
                    return
            else:
                if current == self.home_pos:
                    self.route = path
                    return

            # Explore 4 directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                
                if 0 <= nx < self.state.world_width and 0 <= ny < self.state.world_height:
                    if self.state.world[nx][ny] != AGENT_STATE_WALL:
                        new_g = g + 1
                        
                        if new_g < g_costs.get((nx, ny), float('inf')):
                            g_costs[(nx, ny)] = new_g
                            next_h = h(nx, ny)
                            heapq.heappush(queue, (new_g + next_h, new_g, (nx, ny), path + [(nx, ny)]))
                            
        self.route = []

    # ---------------- EXECUTION LOGIC ---------------- #

    def move_to(self, target):
        cx, cy = self.state.pos_x, self.state.pos_y
        tx, ty = target
        dx = tx - cx
        dy = ty - cy
        # Determine target direction
        if abs(dx) > abs(dy):
            target_dir = AGENT_DIRECTION_EAST if dx > 0 else AGENT_DIRECTION_WEST
        else:
            target_dir = AGENT_DIRECTION_SOUTH if dy > 0 else AGENT_DIRECTION_NORTH
        # Compute turn
        turn = (target_dir - self.state.direction) % 4

        if turn == 1 or turn == 2:
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            self.update_score(ACTION_TURN_RIGHT)
            return ACTION_TURN_RIGHT

        elif turn == 3:
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            self.update_score(ACTION_TURN_LEFT)
            return ACTION_TURN_LEFT

        else:
            self.state.last_action = ACTION_FORWARD
            self.update_score(ACTION_FORWARD)
            self.route.pop(0)
            return ACTION_FORWARD

    def execute(self, percept):
        ###########################
        # DO NOT MODIFY THIS CODE #
        ###########################

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Move agent to a randomly chosen initial position
        if self.initial_random_actions > 0:
            self.log("Moving to random start position ({} steps left)".format(self.initial_random_actions))
            self.steps += 1
            return self.move_to_random_start_position(bump)

        # Finalize randomization by properly updating position (without subsequently changing it)
        elif self.initial_random_actions == 0:
            self.initial_random_actions -= 1
            self.state.update_position(bump)
            self.state.last_action = ACTION_SUCK
            self.steps += 1
            self.log("Processing percepts after position randomization")
            return ACTION_SUCK

        if self.terminated:
            return ACTION_NOP

        ########################
        # START MODIFYING HERE #
        ########################
        self.steps += 1
        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log("Performance: {}".format(self.performance))
                self.update_score(ACTION_NOP)
            return ACTION_NOP

        self.log("Position: ({}, {})\t\tDirection: {}".format(self.state.pos_x, self.state.pos_y,
                                                              direction_to_string(self.state.direction)))

        self.iteration_counter -= 1
        # Track position of agent
        self.state.update_position(bump)
        if bump:
            # Get an xy-offset pair based on where the agent is facing
            offset = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.state.direction]

            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(self.state.pos_x + offset[0], self.state.pos_y + offset[1], AGENT_STATE_WALL)

        # Update perceived state of current tile
        if dirt:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_DIRT)
        else:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_CLEAR)
        # Debug
        self.state.print_world_debug()

        # Save home position
        if home:
            self.home_pos = (self.state.pos_x, self.state.pos_y)

        # Decide action
        # ---- CLEAN ----
        if dirt:
            self.log("DIRT -> SUCK")
            self.state.last_action = ACTION_SUCK
            self.cleaned += 1
            self.update_score(ACTION_SUCK)
            return ACTION_SUCK

        # ---- PLAN ----
        if not self.route:
            
            # Use Dynamic Algorithms based on user setting
            if self.current_algorithm == "BFS":
                self.bfs(return_home=False)
            elif self.current_algorithm == "DFS":
                self.dfs(return_home=False)
            elif self.current_algorithm == "Greedy":
                self.best_first_search(return_home=False)
            elif self.current_algorithm == "A*":
                self.a_star_search(return_home=False)

            # if no unknown → return home
            if not self.route:
                if (self.state.pos_x, self.state.pos_y) == self.home_pos:
                    self.log("FINISHED: cleaned entire map and returned home")
                    self.state.print_world_debug()
                    self.update_score(ACTION_NOP, shutdown=True)
                    
                    # ---- SUMMARY ----
                    self.log("==============================")
                    self.log("AGENT FINISHED! SUMMARY:")
                    self.log(f"- Algorithm: {self.current_algorithm}")
                    self.log(f"- Grid size: {self.state.world_width} x {self.state.world_height}")
                    self.log(f"- Score: {self.score}")
                    self.log(f"- Steps: {self.steps}")
                    self.log(f"- Nodes explored: {self.nodes_explored}")
                    is_optimal = "Yes" if self.current_algorithm in ["BFS", "A*"] else "No"
                    self.log(f"- Is optimal or not?: {is_optimal}")
                    self.log("==============================")
                    
                    return ACTION_NOP

                self.log("Returning home...")
                
                # Dynamic return to home
                if self.current_algorithm == "BFS":
                    self.bfs(return_home=True)
                elif self.current_algorithm == "DFS":
                    self.dfs(return_home=True)
                elif self.current_algorithm == "Greedy":
                    self.best_first_search(return_home=True)
                elif self.current_algorithm == "A*":
                    self.a_star_search(return_home=True)


        # ---- EXECUTE PLAN ----
        if self.route:
            return self.move_to(self.route[0])

        if self.terminated:
            return ACTION_NOP