import tkinter as tk
from tkinter import messagebox, ttk
from heapq import heappush, heappop
from collections import deque
import random

NORMAL_COST = 1
WAIT_COST = 0
ION_COST = 9
SOLAR_RECHARGE = 2

THEME = {
    "Empty": {"bg": "#1e293b", "fg": "#64748b", "icon": ""},
    "Wall": {"bg": "#334155", "fg": "#cbd5e1", "icon": "🧱"},
    "IonStorm": {"bg": "#0e7490", "fg": "#67e8f9", "icon": "⚡"},
    "SolarRecharge": {"bg": "#78350f", "fg": "#fcd34d", "icon": "☀️"},
    "Start": {"bg": "#065f46", "fg": "#6ee7b7", "icon": "🚀"},
    "Goal": {"bg": "#7f1d1d", "fg": "#fca5a5", "icon": "⚛️"},
    "Path": {"bg": "#581c87", "fg": "#d8b4fe", "icon": "👣"}
}

class ChronosState:
    def __init__(self, x, y, t, energy, solar_mask):
        self.x = x
        self.y = y
        self.t = t
        self.energy = energy
        self.solar_mask = solar_mask

    def __eq__(self, other):
        return (self.x, self.y, self.t, self.energy, self.solar_mask) == \
               (other.x, other.y, other.t, other.energy, other.solar_mask)

    def __hash__(self):
        return hash((self.x, self.y, self.t, self.energy, self.solar_mask))

class ChronosProblem:
    def __init__(self, grid, N, T, max_energy):
        self.grid = grid
        self.N = N
        self.T = T
        self.max_energy = max_energy
        self.solars = []
        for x in range(N):
            for y in range(N):
                if grid[x][y] == "SolarRecharge":
                    self.solars.append((x, y))

    def get_start_state(self):
        return ChronosState(0, 0, 0, self.max_energy, 0)

    def is_goal_state(self, state):
        return state.x == self.N - 1 and state.y == self.N - 1 and state.energy >= 0

    def blocked(self, x, y, t):
        if (x, y) == (0, 0) or (x, y) == (self.N - 1, self.N - 1):
            return False
        return (((x + 1) * (y + 1) + t) % 3) == 0

    def solar_index(self, x, y):
        try:
            return self.solars.index((x, y))
        except ValueError:
            return -1

    def get_successors(self, state):
        successors = []
        directions = [("North", -1, 0), ("South", 1, 0), ("West", 0, -1), ("East", 0, 1), ("Wait", 0, 0)]
        next_t = (state.t + 1) % self.T

        for action, dx, dy in directions:
            nx, ny = state.x + dx, state.y + dy
            if not (0 <= nx < self.N and 0 <= ny < self.N):
                continue
            if self.grid[nx][ny] == "Wall":
                continue
            if self.blocked(nx, ny, next_t):
                continue

            energy = state.energy
            if action == "Wait":
                if self.grid[state.x][state.y] == "IonStorm":
                    energy -= 1
                else:
                    energy -= WAIT_COST
            elif self.grid[nx][ny] == "IonStorm":
                energy -= ION_COST
            else:
                energy -= NORMAL_COST

            if energy < 0:
                continue

            mask = state.solar_mask
            index = self.solar_index(nx, ny)
            if index != -1 and not (mask & (1 << index)):
                energy = min(self.max_energy, energy + SOLAR_RECHARGE)
                mask |= 1 << index

            successors.append((ChronosState(nx, ny, next_t, energy, mask), action))
        return successors

def global_reachability_check(grid, N, T, max_energy):
    problem = ChronosProblem(grid, N, T, max_energy)
    start = problem.get_start_state()
    queue = deque([start])
    visited = {start}
    while queue:
        state = queue.popleft()
        if problem.is_goal_state(state):
            return True
        for successor, _ in problem.get_successors(state):
            if successor not in visited:
                visited.add(successor)
                queue.append(successor)
    return False

def get_neighbors(x, y, N):
    neighbors = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < N and 0 <= ny < N:
            neighbors.append((nx, ny))
    return neighbors

def forward_check(assignment, domains, var, value, N, max_walls, max_solars):
    new_domains = {v: list(d) for v, d in domains.items()}
    new_domains[var] = [value]
    current_walls = sum(1 for v, val in assignment.items() if val == "Wall") + (1 if value == "Wall" else 0)
    current_solars = sum(1 for v, val in assignment.items() if val == "SolarRecharge") + (1 if value == "SolarRecharge" else 0)
    unassigned_count = (N * N) - len(assignment) - 1

    if current_walls > max_walls or (current_walls + unassigned_count < max_walls):
        return None
    if current_solars > max_solars or (current_solars + unassigned_count < max_solars):
        return None

    vx, vy = var
    if value == "SolarRecharge":
        for nx, ny in get_neighbors(vx, vy, N):
            if (nx, ny) in assignment:
                if assignment[(nx, ny)] == "IonStorm":
                    return None
            else:
                if "IonStorm" in new_domains[(nx, ny)]:
                    new_domains[(nx, ny)] = [v for v in new_domains[(nx, ny)] if v != "IonStorm"]
                    if not new_domains[(nx, ny)]:
                        return None
    elif value == "IonStorm":
        for nx, ny in get_neighbors(vx, vy, N):
            if (nx, ny) in assignment:
                if assignment[(nx, ny)] == "SolarRecharge":
                    return None
            else:
                if "SolarRecharge" in new_domains[(nx, ny)]:
                    new_domains[(nx, ny)] = [v for v in new_domains[(nx, ny)] if v != "SolarRecharge"]
                    if not new_domains[(nx, ny)]:
                        return None
    return new_domains

def select_unassigned_variable(assignment, domains, N):
    unassigned = [v for v in domains if v not in assignment]
    if not unassigned:
        return None
    min_domain_size = min(len(domains[v]) for v in unassigned)
    mrv_candidates = [v for v in unassigned if len(domains[v]) == min_domain_size]
    if len(mrv_candidates) == 1:
        return mrv_candidates[0]
    return max(mrv_candidates, key=lambda var: sum(1 for nx, ny in get_neighbors(var[0], var[1], N) if (nx, ny) not in assignment))

def backtracking_search(assignment, domains, N, T, max_energy, max_walls, max_solars, recursion_depth=[0]):
    recursion_depth[0] += 1
    if recursion_depth[0] > 15000:
        return None

    if len(assignment) == N * N:
        grid = [["" for _ in range(N)] for _ in range(N)]
        for (x, y), val in assignment.items():
            grid[x][y] = val
        if global_reachability_check(grid, N, T, max_energy):
            return grid
        return None

    var = select_unassigned_variable(assignment, domains, N)
    if not var:
        return None

    domain_values = list(domains[var])
    random.shuffle(domain_values)

    for value in domain_values:
        new_domains = forward_check(assignment, domains, var, value, N, max_walls, max_solars)
        if new_domains is not None:
            assignment[var] = value
            result = backtracking_search(assignment, new_domains, N, T, max_energy, max_walls, max_solars, recursion_depth)
            if result is not None:
                return result
            del assignment[var]
    return None

def generate_reactor_floor(N, T, max_energy):
    max_walls = int(0.15 * (N ** 2))
    max_solars = 3
    domains = {(x, y): ["Empty", "Wall", "IonStorm", "SolarRecharge"] for x in range(N) for y in range(N)}
    assignment = {(0, 0): "Empty", (N - 1, N - 1): "Empty"}
    domains[(0, 0)] = ["Empty"]
    domains[(N - 1, N - 1)] = ["Empty"]
    
    depth_tracker = [0]
    grid = backtracking_search(assignment, domains, N, T, max_energy, max_walls, max_solars, depth_tracker)
    
    if grid is None:
        grid = backtracking_search(assignment, domains, N, T, max_energy, max_walls=max(2, int(0.10 * (N ** 2))), max_solars=2, recursion_depth=[0])
        
    return grid

def reconstruct_path(parent, goal):
    path = []
    while goal in parent:
        goal, action = parent[goal]
        path.append(action)
    path.reverse()
    return path

def run_search_algorithm(problem, algo_name):
    start = problem.get_start_state()
    if algo_name == "BFS":
        queue = deque([start])
        visited = {start}
        parent = {}
        while queue:
            state = queue.popleft()
            if problem.is_goal_state(state):
                return reconstruct_path(parent, state), "Success (Time-Optimal)"
            for successor, action in problem.get_successors(state):
                if successor not in visited:
                    visited.add(successor)
                    parent[successor] = (state, action)
                    queue.append(successor)
        return None, "No path found"

    elif algo_name == "UCS":
        queue = [(0, 0, start)]
        best_cost = {start: 0}
        parent = {}
        counter = 0
        while queue:
            cost, _, state = heappop(queue)
            if cost != best_cost.get(state):
                continue
            if problem.is_goal_state(state):
                return reconstruct_path(parent, state), f"Success | Energy Cost: {cost}"
            for successor, action in problem.get_successors(state):
                if action != "Wait" and problem.grid[successor.x][successor.y] == "IonStorm":
                    step_cost = ION_COST
                elif action != "Wait":
                    step_cost = NORMAL_COST
                else:
                    step_cost = 1 if problem.grid[state.x][state.y] == "IonStorm" else WAIT_COST
                
                new_cost = cost + step_cost
                if new_cost < best_cost.get(successor, float("inf")):
                    best_cost[successor] = new_cost
                    parent[successor] = (state, action)
                    counter += 1
                    heappush(queue, (new_cost, counter, successor))
        return None, "No path found"

    elif algo_name == "A* Search":
        def h(st): return abs(st.x - (problem.N - 1)) + abs(st.y - (problem.N - 1))
        queue = [(h(start), 0, 0, start)]
        g_cost = {start: 0}
        parent = {}
        closed = set()
        counter = 0
        while queue:
            f, cost, _, state = heappop(queue)
            if state in closed:
                continue
            if problem.is_goal_state(state):
                return reconstruct_path(parent, state), f"Success | Energy Cost: {cost}"
            closed.add(state)
            for successor, action in problem.get_successors(state):
                if action != "Wait" and problem.grid[successor.x][successor.y] == "IonStorm":
                    step_cost = ION_COST
                elif action == "Wait" and problem.grid[state.x][state.y] == "IonStorm":
                    step_cost = 1
                else:
                    step_cost = NORMAL_COST if action != "Wait" else WAIT_COST

                new_cost = cost + step_cost
                if new_cost < g_cost.get(successor, float("inf")):
                    g_cost[successor] = new_cost
                    parent[successor] = (state, action)
                    counter += 1
                    heappush(queue, (new_cost + h(successor), new_cost, counter, successor))
        return None, "No path found"

class ChronosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chronos-Grid: Reactor Facility Control Panel")
        self.root.geometry("950x850")
        self.root.configure(bg="#0f172a")

        self.current_grid = None
        self.N_val = 6
        self.T_val = 3
        self.E_val = 15

        self.setup_ui()

    def setup_ui(self):
        header = tk.Label(self.root, text="CHRONOS-GRID FACILITY DASHBOARD", font=("Helvetica", 16, "bold"), fg="#f8fafc", bg="#0f172a")
        header.pack(pady=8)

        control_frame = tk.Frame(self.root, bg="#1e293b", padx=15, pady=12, relief="raised", bd=2)
        control_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(control_frame, text="Grid Size (N):", fg="#cbd5e1", bg="#1e293b", font=("Helvetica", 9)).grid(row=0, column=0, sticky="w", padx=4)
        self.n_entry = tk.Entry(control_frame, width=4)
        self.n_entry.insert(0, "6")
        self.n_entry.grid(row=0, column=1, padx=4)

        tk.Label(control_frame, text="Cycle (T):", fg="#cbd5e1", bg="#1e293b", font=("Helvetica", 9)).grid(row=0, column=2, sticky="w", padx=4)
        self.t_entry = tk.Entry(control_frame, width=4)
        self.t_entry.insert(0, "3")
        self.t_entry.grid(row=0, column=3, padx=4)

        tk.Label(control_frame, text="Max Energy:", fg="#cbd5e1", bg="#1e293b", font=("Helvetica", 9)).grid(row=0, column=4, sticky="w", padx=4)
        self.e_entry = tk.Entry(control_frame, width=4)
        self.e_entry.insert(0, "15")
        self.e_entry.grid(row=0, column=5, padx=4)

        gen_btn = tk.Button(control_frame, text="1. Generate Grid 🧱", bg="#f59e0b", fg="#000000", font=("Helvetica", 9, "bold"), command=self.generate_grid_action)
        gen_btn.grid(row=0, column=6, padx=10)

        algo_label = tk.Label(control_frame, text="Run Search:", fg="#cbd5e1", bg="#1e293b", font=("Helvetica", 9, "bold"))
        algo_label.grid(row=1, column=0, sticky="w", padx=4, pady=10)

        bfs_btn = tk.Button(control_frame, text="BFS 🚀", bg="#38bdf8", fg="#000000", font=("Helvetica", 9, "bold"), width=10, command=lambda: self.run_search_action("BFS"))
        bfs_btn.grid(row=1, column=1, columnspan=2, padx=2, pady=10)

        ucs_btn = tk.Button(control_frame, text="UCS 🛡️", bg="#34d399", fg="#000000", font=("Helvetica", 9, "bold"), width=10, command=lambda: self.run_search_action("UCS"))
        ucs_btn.grid(row=1, column=3, columnspan=2, padx=2, pady=10)

        astar_btn = tk.Button(control_frame, text="A* Search ⭐", bg="#a78bfa", fg="#000000", font=("Helvetica", 9, "bold"), width=10, command=lambda: self.run_search_action("A* Search"))
        astar_btn.grid(row=1, column=5, columnspan=2, padx=2, pady=10)

        legend_frame = tk.Frame(self.root, bg="#0f172a")
        legend_frame.pack(fill="x", padx=20, pady=4)
        
        self.create_legend_item(legend_frame, "Start 🚀", "#065f46")
        self.create_legend_item(legend_frame, "Core ⚛️", "#7f1d1d")
        self.create_legend_item(legend_frame, "Wall 🧱", "#334155")
        self.create_legend_item(legend_frame, "Storm ⚡", "#0e7490")
        self.create_legend_item(legend_frame, "Solar ☀️", "#78350f")
        self.create_legend_item(legend_frame, "Path 👣", "#581c87")

        self.canvas_frame = tk.Frame(self.root, bg="#0f172a")
        self.canvas_frame.pack(pady=2)
        self.canvas = tk.Canvas(self.canvas_frame, width=380, height=380, bg="#1e293b", highlightthickness=0)
        self.canvas.pack()

        log_frame = tk.Frame(self.root, bg="#1e293b", padx=10, pady=5, relief="sunken", bd=1)
        log_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(log_frame, text="Simulation Log & Action Trace:", fg="#38bdf8", bg="#1e293b", font=("Helvetica", 9, "bold")).pack(anchor="w")
        
        self.log_text = tk.Text(log_frame, height=4, bg="#0f172a", fg="#cbd5e1", font=("Consolas", 9), wrap="word", highlightthickness=0)
        self.log_text.pack(fill="x", pady=4)
        self.log_text.insert("1.0", "System ready. Generate a grid and select an algorithm button above.")
        self.log_text.config(state="disabled")

        self.status_var = tk.StringVar(value="Status: Ready.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, fg="#cbd5e1", bg="#1e293b", font=("Helvetica", 9), anchor="w", padx=10, relief="sunken")
        status_bar.pack(fill="x", padx=20, pady=5)

    def create_legend_item(self, parent, text, color):
        f = tk.Frame(parent, bg="#0f172a")
        f.pack(side="left", padx=6)
        lbl_box = tk.Label(f, bg=color, width=2, height=1)
        lbl_box.pack(side="left", padx=2)
        lbl_text = tk.Label(f, text=text, fg="#cbd5e1", bg="#0f172a", font=("Helvetica", 8, "bold"))
        lbl_text.pack(side="left")

    def generate_grid_action(self):
        try:
            self.N_val = int(self.n_entry.get())
            self.T_val = int(self.t_entry.get())
            self.E_val = int(self.e_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers for N, T, and Emax.")
            return

        self.status_var.set("Status: Running CSP Backtracking & Forward Checking...")
        self.root.update_idletasks()

        final_grid = generate_reactor_floor(self.N_val, self.T_val, self.E_val)
        if final_grid is None:
            messagebox.showwarning("Failed", "Could not generate a valid grid meeting quotas. Try again.")
            self.status_var.set("Status: Generation failed.")
            return

        self.current_grid = final_grid
        self.status_var.set("Status: Animating Facility Layout...")
        
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert("1.0", f"CSP Solver successfully mapped {self.N_val}x{self.N_val} facility. Rendering...")
        self.log_text.config(state="disabled")

        cells_to_reveal = []
        for x in range(self.N_val):
            for y in range(self.N_val):
                if (x, y) != (0, 0) and (x, y) != (self.N_val - 1, self.N_val - 1):
                    cells_to_reveal.append((x, y))
        
        partial_grid = [["" for _ in range(self.N_val)] for _ in range(self.N_val)]
        partial_grid[0][0] = final_grid[0][0]
        partial_grid[self.N_val - 1][self.N_val - 1] = final_grid[self.N_val - 1][self.N_val - 1]

        def reveal_next_cell(index):
            if index < len(cells_to_reveal):
                x, y = cells_to_reveal[index]
                partial_grid[x][y] = final_grid[x][y]
                self.draw_grid(partial_grid)
                self.root.after(30, lambda: reveal_next_cell(index + 1))
            else:
                self.draw_grid(final_grid)
                self.status_var.set("Status: Grid generated & rendered successfully! Ready for search.")

        reveal_next_cell(0)

    def draw_grid(self, grid, path_coords=None):
        self.canvas.delete("all")
        N = len(grid)
        canvas_size = 380
        cell_size = canvas_size / N

        for x in range(N):
            for y in range(N):
                cell_type = grid[x][y]
                style = THEME.get(cell_type, THEME["Empty"])
                
                bg_color = style["bg"]
                icon = style["icon"]

                if (x, y) == (0, 0):
                    bg_color = THEME["Start"]["bg"]
                    icon = THEME["Start"]["icon"]
                elif (x, y) == (N - 1, N - 1):
                    bg_color = THEME["Goal"]["bg"]
                    icon = THEME["Goal"]["icon"]
                
                if path_coords and (x, y) in path_coords and (x, y) != (0, 0) and (x, y) != (N - 1, N - 1):
                    bg_color = THEME["Path"]["bg"]
                    icon = THEME["Path"]["icon"]

                self.canvas.create_rectangle(
                    y * cell_size + 2, x * cell_size + 2,
                    (y + 1) * cell_size - 2, (x + 1) * cell_size - 2,
                    fill=bg_color, outline="#0f172a", width=2
                )
                
                if icon:
                    self.canvas.create_text(
                        y * cell_size + cell_size / 2,
                        x * cell_size + cell_size / 2,
                        text=icon,
                        fill="#ffffff",
                        font=("Helvetica", int(cell_size / 2.5), "bold")
                    )

    def run_search_action(self, algo):
        if self.current_grid is None:
            messagebox.showwarning("Warning", "Please generate a reactor floor first!")
            return

        self.status_var.set(f"Status: Executing {algo} search...")
        self.root.update_idletasks()

        problem = ChronosProblem(self.current_grid, self.N_val, self.T_val, self.E_val)
        path, message = run_search_algorithm(problem, algo)

        if path is None:
            self.status_var.set(f"Status: {message}")
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", f"[{algo}] Result: {message}")
            self.log_text.config(state="disabled")
            return

        full_coords = []
        curr_x, curr_y = 0, 0
        full_coords.append((curr_x, curr_y))
        
        for action in path:
            if action == "North": curr_x -= 1
            elif action == "South": curr_x += 1
            elif action == "West": curr_y -= 1
            elif action == "East": curr_y += 1
            full_coords.append((curr_x, curr_y))

        self.status_var.set(f"Status: Animating {algo} path...")
        
        anim_path_coords = set()
        
        def animate_step(index):
            if index < len(full_coords):
                anim_path_coords.add(full_coords[index])
                self.draw_grid(self.current_grid, anim_path_coords)
                self.root.after(150, lambda: animate_step(index + 1))
            else:
                self.status_var.set(f"Status: {message} | Steps: {len(path)}")
                log_output = f"[{algo}] {message}\nActions Sequence: {path}"
                self.log_text.config(state="normal")
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert("1.0", log_output)
                self.log_text.config(state="disabled")

        animate_step(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChronosGUI(root)
    root.mainloop()