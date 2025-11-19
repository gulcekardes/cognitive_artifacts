import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from collections import defaultdict
from pysat.solvers import Minisat22


z = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0)]   
p = [(0, 0, 0), (0, 1, 0), (0, 1, 1), (1, 1, 0)]   
t = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (0, 2, 0)]   
b = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 1, 1)]    
a = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 1, 0)]   
l = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0)]    
v = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]             

pieces = [z, p, t, b, a, l, v]
colors = ["blue", "red", "purple", "brown", "yellow", "orange", "green"]

rotate_x = lambda cubelets: [(x, z, -y) for (x, y, z) in cubelets]
rotate_y = lambda cubelets: [(z, y, -x) for (x, y, z) in cubelets]
rotate_z = lambda cubelets: [(-y, x, z) for (x, y, z) in cubelets]
identity  = lambda cubelets: cubelets

def generate_rotations(piece):
    """Generate all unique rotations of a piece (ignoring reflections)."""
    orientations = []
    for f_a in [identity, rotate_x, rotate_y, rotate_z]:
        for f_b in [identity, rotate_x, rotate_y, rotate_z]:
            for f_c in [identity, rotate_x, rotate_y, rotate_z]:
                for f_d in [identity, rotate_x, rotate_y, rotate_z]:
                    for f_e in [identity, rotate_x, rotate_y, rotate_z]:
                        rot_piece = f_a(f_b(f_c(f_d(f_e(piece)))))
                        rot_piece_sorted = sorted(rot_piece)
                        min_x, min_y, min_z = rot_piece_sorted[0]
                        trans_rot_piece = tuple((x - min_x, y - min_y, z - min_z)
                                                 for (x, y, z) in rot_piece_sorted)
                        if trans_rot_piece not in orientations:
                            orientations.append(trans_rot_piece)
    return orientations

orientations = [generate_rotations(piece) for piece in pieces]
coordinates = [(x, y, z) for x in range(3) for y in range(3) for z in range(3)]

def generate_placements():
    """
    Enumerate every valid placement.
    
    A placement is a tuple (piece, adjusted_orientation), where adjusted_orientation is
    a tuple of cube cells that the piece occupies when placed.
    
    Each placement is assigned a unique Boolean variable number.
    
    In addition, we record a name for each variable of the form P_{xyzi}:
      - (x,y,z) is the anchor coordinate (converted to 1-indexed),
      - i is the piece number (from 1 to 7).
      
    Returns:
      - placements: dict mapping (piece, adjusted_orientation) -> variable id
      - placements_by_piece: dict mapping piece index -> set of variable ids
      - placements_by_cell: dict mapping cube cell -> set of variable ids
      - var_names: dict mapping variable id -> variable name (like P_{1213})
      - num_vars: total number of variables (placements)
    """
    placements = {}  # mapping (piece, adjusted_orientation) -> variable id
    placements_by_piece = {i: set() for i in range(7)}
    placements_by_cell = defaultdict(set)
    var_names = {}  # mapping variable id -> name string (like P_{xyzi})
    var_counter = 1

    for anchor in coordinates:
        for piece in range(7):
            for orient in orientations[piece]:
                for base in orient:
                    adjusted = tuple(sorted(
                        ((anchor[0] + o[0] - base[0],
                          anchor[1] + o[1] - base[1],
                          anchor[2] + o[2] - base[2])
                         for o in orient)
                    ))
                    if all(0 <= cell[0] < 3 and 0 <= cell[1] < 3 and 0 <= cell[2] < 3 for cell in adjusted):
                        placement_key = (piece, adjusted)
                        if placement_key not in placements:
                            placements[placement_key] = var_counter
                            # Use the current anchor (converted to 1-indexed) and piece id+1
                            ax, ay, az = anchor[0] + 1, anchor[1] + 1, anchor[2] + 1
                            var_names[var_counter] = f"P_{{{ax}{ay}{az}{piece+1}}}"
                            var_counter += 1
                        var = placements[placement_key]
                        placements_by_piece[piece].add(var)
                        for cell in adjusted:
                            placements_by_cell[cell].add(var)
    return placements, placements_by_piece, placements_by_cell, var_names, var_counter - 1

def exactly_one(variables):
    """
    Produce CNF clauses for the "exactly one" constraint:
      - At least one literal is true.
      - At most one literal is true (pairwise).
    Returns a list of clauses.
    """
    clauses = []
    # Convert to list to preserve order (although order is not important logically)
    variables = list(variables)
    if not variables:
        return clauses
    clauses.append(variables)  # at least one clause
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            clauses.append([-variables[i], -variables[j]])
    return clauses

def generate_sat_instance():
    placements, placements_by_piece, placements_by_cell, var_names, num_vars = generate_placements()
    clauses = []
    # Constraint: Each piece is placed exactly once.
    for piece in placements_by_piece:
        piece_vars = list(placements_by_piece[piece])
        clauses.extend(exactly_one(piece_vars))
    # Constraint: Each cube cell is covered exactly once.
    for cell in placements_by_cell:
        cell_vars = list(placements_by_cell[cell])
        clauses.extend(exactly_one(cell_vars))
    return placements, clauses, num_vars, var_names

# Generate the SAT instance.
placements, clauses, num_vars, var_names = generate_sat_instance()

# --- Print a Portion of the Formula in LaTeX (with duplicate literals removed) ---
def print_formula_portion(clauses, var_names):
    """
    Print a portion of the Boolean formula in LaTeX format.
    For each clause width among the three smallest distinct clause sizes,
    one representative clause is printed with duplicate literals removed.
    """
    # Get distinct clause lengths from the generated clauses.
    clause_widths = sorted(set(len(clause) for clause in clauses))
    smallest_widths = clause_widths[:3]
    
    printed = {}  # key: clause width, value: LaTeX string for that clause
    for clause in clauses:
        original_length = len(clause)
        if original_length in smallest_widths and original_length not in printed:
            # Remove duplicate literals while preserving the original order.
            unique_clause = []
            seen = set()
            for lit in clause:
                if lit not in seen:
                    unique_clause.append(lit)
                    seen.add(lit)
            # Create LaTeX strings for each literal.
            lit_strs = []
            for lit in unique_clause:
                if lit > 0:
                    lit_strs.append(var_names.get(lit, f"P_{{{lit}}}"))
                else:
                    lit_strs.append(r"\neg " + var_names.get(-lit, f"P_{{{-lit}}}"))
            # Build the clause string with the LaTeX disjunction operator.
            clause_str = "(" + " \\vee ".join(lit_strs) + ")"
            printed[original_length] = clause_str

    # Print the overall formula with a representative clause for each selected width.
    print("Puzzle: Find an assignment of truth values (0's and 1's) to all the $P_{xyzi}$ variables such that the entire formula $\\Phi$ evaluates to true (1).")
    print("\n$$")
    print("\\begin{aligned}")
    # Combine the representative clauses using the conjunction operator.
    clause_lines = [printed[k] for k in sorted(printed.keys())]
    formula_str = " \\wedge ".join(clause_lines) + " \\wedge \\ldots"
    print("\\Phi= & " + formula_str)
    print("\\end{aligned}")
    print("$$\n")

# Print the formula portion.
print_formula_portion(clauses, var_names)

# --- Model Counting with Progress Tracker ---
def count_solutions(clauses, num_vars):
    """
    Enumerate all solutions of the CNF instance using a blocking clause method.
    Prints a progress update each time a solution is found.
    
    Returns:
      - solution_count: total number of solutions found.
      - models: list of models.
    """
    solver = Minisat22(bootstrap_with=clauses)
    solution_count = 0
    models = []
    while solver.solve():
        model = solver.get_model()
        solution_count += 1
        models.append(model)
        sys.stdout.write(f"\rSolutions found so far: {solution_count}")
        sys.stdout.flush()
        # Block the current solution.
        blocking_clause = [-lit for lit in model]
        solver.add_clause(blocking_clause)
    print()  # Newline after progress updates.
    solver.delete()
    return solution_count, models

solution_count, models = count_solutions(clauses, num_vars)
print("Total number of solutions found:", solution_count)

# --- Reconstruct One Solution ---
if solution_count == 0:
    print("No solution found!")
    exit()
else:
    chosen_model = models[0]
    # Mark the cells covered by each placement in the chosen solution.
    solution_cells = {}  # maps each cube cell (x, y, z) to a piece color
    for (piece, adjusted), var in placements.items():
        if var in chosen_model:  # placement is selected (variable is true)
            for cell in adjusted:
                solution_cells[cell] = colors[piece]
    
    # Prepare the list for plotting: each element is (x, y, z, color)
    solution_list = [(cell[0], cell[1], cell[2], solution_cells[cell])
                     for cell in solution_cells]

# --- Plot the 3D Solution ---
def plot_solution(solution):
    """
    Plot a 3D visualization of the Soma cube solution.
    Each cell in the 3x3x3 cube is drawn as a colored cube.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    color_map = {
        "blue": '#0000FF',
        "red": '#FF0000',
        "purple": '#800080',
        "brown": '#8B4513',
        "yellow": '#FFD700',
        "orange": '#FFA500',
        "green": '#008000'
    }
    for (x, y, z, color) in solution:
        ax.bar3d(x, y, z, 1, 1, 1, color=color_map.get(color, "#CCCCCC"), shade=True, alpha=0.8)
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.view_init(elev=30, azim=45)
    plt.title("Soma Cube Solution")
    plt.show()

plot_solution(solution_list)
