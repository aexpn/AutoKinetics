# AutoKinetics: A Visual Simulator for Chemical Reaction Networks

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-PyQt6-green.svg)](https://www.qt.io/qt-for-python)

A computational tool for the visual construction and numerical simulation of chemical kinetic systems. AutoKinetics bridges the gap between the intuitive, graphical representation of reaction mechanisms and rigorous quantitative analysis, making it an ideal tool for researchers, educators, and students in chemical engineering and physical chemistry.

---

## 🔬 Core Features

* **Visual Network Editor:** A drag-and-drop interface to build complex reaction networks using species, groups, and reaction arrows.
* **Object-Oriented Data Model:** Each graphical element holds detailed chemical and physical properties (enthalpy, Arrhenius parameters, concentration, etc.).
* **Integrated ODE Backend:** A powerful backend engine using **SciPy** to solve the system of coupled ordinary differential equations (ODEs) that govern the system's temporal evolution.
* **Automated Kinetic Analysis:** The backend automatically analyzes the simulation results to:
    * Determine the best-fit reaction order (0, 1st, or 2nd).
    * Calculate the effective rate constant ($k$) via linear regression.
* **Data Persistence:** Save and load entire reaction networks using a human-readable JSON-based `.kin` file format.
* **Result Visualization:** Automatically generates plots for concentration profiles, rate law analysis, reaction rates, and energy profiles.

---

## 📊 Example Simulation Output

Below is an example of the output generated for the first-order isomerization of cyclopropane to propene. The application provides a comprehensive view of the system's dynamics.
<img width="802" height="751" alt="Screenshot from 2025-10-03 00-23-31" src="https://github.com/user-attachments/assets/b301f5fa-6b0d-4132-bbd2-b306fd120e25" />
<img width="802" height="751" alt="image" src="https://github.com/user-attachments/assets/ae3106f9-5380-4db1-9b26-8ff6d7d6849a" />

---

## 🧪 Theoretical Background

The simulation engine is based on fundamental principles of chemical kinetics. The temporal evolution of the concentration of any species $i$, denoted $[X_i]$, is described by a system of ordinary differential equations.

### Differential Rate Laws
The rate of change for the concentration of species $i$ is the sum of the rates of all reactions ($j$) in which it participates:

$$
\frac{d[X_i]}{dt} = \sum_{j} \nu_{ij} v_j
$$

where:
- $\nu_{ij}$ is the stoichiometric coefficient of species $i$ in reaction $j$ (positive for products, negative for reactants).
- $v_j$ is the rate of reaction $j$.

### Reaction Rate Law
The rate of an elementary reaction, $v_j$, is determined by the concentration of its reactants and a temperature-dependent rate constant, $k_j$. For a generic reaction, the rate is given by:

$$
v_j = k_j \prod_{r \in \text{reactants}} [X_r]^{m_r}
$$

where:
- $[X_r]$ is the concentration of reactant $r$.
- $m_r$ is the partial reaction order with respect to reactant $r$.

### Temperature Dependence
The rate constant $k$ is calculated using the modified Arrhenius equation, which accounts for temperature dependence:

$$
k(T) = A \cdot T^n \cdot e^{-\frac{E_a}{RT}}
$$

where:
- $A$ is the pre-exponential (Arrhenius) factor.
- $T$ is the absolute temperature in Kelvin (K).
- $n$ is the temperature exponent.
- $E_a$ is the activation energy in Joules per mole (J/mol).
- $R$ is the universal gas constant ($8.314 \text{ J/(mol·K)}$).

The backend solves this system of coupled, non-linear ODEs numerically using the `scipy.integrate.solve_ivp` function with the `Radau` method, which is well-suited for stiff systems often encountered in chemical kinetics.

---

## 🛠️ Architecture

The application is built on a decoupled frontend-backend architecture.

* **Frontend (`gui.py`):** A graphical user interface built with **PyQt6**. It manages user interaction, visual scene construction, and property editing. It communicates with the backend by passing a `.kin` file.
* **Backend (Python Scripts):** A headless set of scripts (`backend_main.py`, `simulator.py`, `analyzer.py`, etc.) that performs all heavy computations.
    * It parses the `.kin` file.
    * It solves the ODE system using **NumPy** and **SciPy**.
    * It generates result plots as image files using **Matplotlib**.
    * It returns all simulation and analysis data as a single JSON object to standard output.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd AutoKinetics
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install the required libraries:**
    A `requirements.txt` file should be created with the following content:
    ```
    numpy
    scipy
    matplotlib
    PyQt6
    ```
    Then, install them:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Launch the GUI:**
    ```bash
    python python/gui.py
    ```

2.  **Run the Backend Manually (for testing):**
    The backend can be tested directly from the command line. It will use a default test file.
    ```bash
    python python/backend_main.py
    ```

---

## 📝 `.kin` File Format

The project state is saved in a JSON-based `.kin` file with the following main keys:
* `species`: A list of objects, where each object contains the name, position, and all physical/chemical properties of a species.
* `groups`: A list of visual grouping objects, containing a title and the indices of the species they contain.
* `arrows`: A list of reaction objects, containing kinetic parameters (like `arrhenius_A`, `Ea`) and references to the reactant and product species/groups.

---

## 🗺️ Roadmap

Future development will focus on enhancing the scientific accuracy and user experience:

* [ ] **Full Stoichiometry Support:** Implement a robust UI for editing stoichiometric coefficients and partial reaction orders for each species in a reaction.
* [ ] **Interactive Plotting:** Replace static Matplotlib images with an interactive plotting widget (e.g., using `pyqtgraph`) directly within the GUI.
* [ ] **Global Simulation Conditions:** Create a dedicated panel for global parameters like pressure and temperature, decoupling them from individual reactions.
* [ ] **Reversible Reactions:** Update the ODE solver to correctly handle reversible reactions and equilibrium constants.
* [ ] **NIST Database Integration:** Add functionality to query the NIST Chemical Kinetics Database to automatically populate species and reaction parameters.
* [ ] **Advanced Plotting:** Include plots of analytical solutions for simple-order reactions alongside the numerical results for comparison and verification.
* [ ] **Machine Learning Integration:** Implement ML models to predict rate constants ($k$) from molecular features or to fit complex kinetic models to sparse experimental data.


---

## 📜 License
