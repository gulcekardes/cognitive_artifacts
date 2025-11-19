# Solver for "Physical Complexity of a Cognitive Artifact"

This repository contains the code for our cognitive-artifacts experiments on the cube and related puzzles.

- `solver.py` is the main search-based solver for the cube.
- `sat_solver.py` converts the same puzzle representation into a SAT (CNF) encoding used in our SAT-based experiments.
- `preprocessing.py` is used to regenerate the preprocessing / querying curves reported in the paper.

The following scripts are auxiliary and are mainly used for the appendix case studies and figures (they are not needed to run the main solver):

- `chess.py`, `chess_branching_trend.py` – scripts for the chess-style branching experiments.
- `sliding.py` – sliding-block–style toy model.
- `slothouber_graatsma.py` – experiments on the Slothouber–Graatsma puzzle.
  
## Solver Strategies

The implementation in [`solvers.py`](solvers.py) incorporates the following strategies:

- **Dynamic Pruning:**  
  Dynamically prunes small voids (regions of size 1 or 2) during the search to eliminate non-promising branches early.

- **Cell-Selection Strategies:**  
  The solver supports various methods to choose the next unassigned cell:
  
  - **Deterministic:**  
    Always selects the lexicographically first unassigned cell, ensuring a fixed, predictable ordering.
  
  - **Random:**  
    Chooses an unassigned cell at random, which can help avoid pathological cases inherent in fixed orderings.
  
  - **Flexibility:**  
    Uses a weighted selection that favors cells with more available candidate moves. The weighting is controlled by the parameter `--weight_power`, allowing you to adjust how much preference is given to cells with a higher number of candidates.
  
  - **MCV (Minimum Constraining Value):**  
    Selects the cell with the fewest candidate moves (i.e., the most constrained cell), aiming to reduce the search space by addressing bottlenecks early.
  
  - **Layer-Based:**  
    Prioritizes cells based on their \(z\)-coordinate, typically focusing on cells in the lowest (or highest) layer first, reflecting the physical assembly order.
  
  - **Layer_MRV:**  
    A hybrid strategy that combines layer-based ordering with the MCV heuristic, with an additional weighting parameter to balance spatial and constraint-based factors.

- **Dead State Processing:**  
  Implements a two-phase mode where the solver precomputes and records "dead states" (non-promising partial solutions) that are then pruned during subsequent search phases.

- **Biased Value Ordering:**  
  Preprocesses a set number of solutions to gather bias statistics, which are then used to guide the ordering of candidate moves during the main search.

## Execution Instructions

### Basic Execution

Run the solver with the default deterministic cell-selection strategy:

`python solvers.py`

### Using Alternative Cell-Selection Strategies

- **Random Selection:**  
  `python solvers.py --selection_choice random`

- **Flexibility Ordering:**  
  `python solvers.py --selection_choice flexibility --weight_power 2`

- **MCV:**  
  `python solvers.py --selection_choice MCV`

- **Layer-Based Ordering:**  
  `python solvers.py --selection_choice layer_based`

- **Layer_MRV Ordering:**  
  `python solvers.py --selection_choice layer_mrv --alpha 2.0`

### Enabling Advanced Features

- **Dynamic Pruning:**  
  Enable dynamic pruning of small voids:  
  `python solvers.py --pruning`

- **Dead State Processing:**  
  Precompute dead states:  
  `python solvers.py --dead_state_mode precompute`  
  Once precomputed, run the solver using the saved dead states:  
  `python solvers.py --dead_state_mode query`

- **Biased Value Ordering:**  
  Enable biased value ordering based on precomputed statistics (e.g., using 50 solutions for bias computation):  
  `python solvers.py --biased_value_ordering --preprocess_bias_solutions 50`

### Additional Options

- **Setting a Random Seed:**  
  For reproducibility, you can set a random seed:  
  `python solvers.py --seed 42`

- **Forward Checking Value Ordering:**  
  Enable forward checking for candidate value ordering:  
  `python solvers.py --forward_checking_ordering`

## Dependencies

- Python 3.x
- `numpy`
- `matplotlib`
- `argparse`
- `pickle`
