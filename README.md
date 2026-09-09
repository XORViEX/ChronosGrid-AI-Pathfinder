# ChronosGrid-AI-Pathfinder
**Advanced AI Pathfinding & Constraint Satisfaction Simulation**

[github.com/xorviex/ChronosGrid-AI-Pathfinder](https://github.com/xorviex/ChronosGrid-AI-Pathfinder)

---

**Chronos-Grid** is an advanced AI simulation modeling a time-varying sci-fi reactor facility. It combines automated constraint satisfaction problem (CSP) map generation with animated pathfinding algorithms to navigate dynamic hazards, temporal walls, and energy constraints.

## ⚡ Key Features
* **CSP-Driven Generation:** Automatically maps valid reactor floors using backtracking, forward checking, and Minimum Remaining Values (MRV) heuristics.
* **Time-Varying Hazards:** Simulates cyclical temporal walls that open and close based on discrete time states ($t \pmod 3 == 0$).
* **Multiple Search Strategies:** Compare agent behavior across **BFS** (time-optimal), **UCS** (energy-optimal), and **A* Search** (heuristic routing).
* **Interactive GUI:** Built natively using Python's `tkinter` library with real-time visual step-by-step rendering.

## ⚙️ Tech Stack
* **Language:** Python 3.x
* **GUI Framework:** Tkinter
* **Core Libraries:** `heapq`, `collections`, `random`
  
## 📊 Documentation & Slides
You can view the project presentation slides [here](https://canva.link/2lnq0i0scvyqr77) to learn more about the CSP heuristics and search algorithm design.

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed on your system. No external package installations are required since `tkinter` and standard libraries are bundled with Python.

### Installation & Execution
Clone the repository and run the application script `gui.py`:

```bash
git clone [https://github.com/xorviex/ChronosGrid-AI-Pathfinder.git](https://github.com/xorviex/ChronosGrid-AI-Pathfinder.git)
cd ChronosGrid-AI-Pathfinder
python gui.py
