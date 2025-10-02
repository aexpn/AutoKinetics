# backend/simulator.py
import numpy as np
from scipy.integrate import solve_ivp
# KORREKTUR: Relative Imports entfernt
from data_model import ReactionSystem

class ODESolver:
    """Löst das DGL-System für ein Reaktionsnetzwerk."""
    def __init__(self, system: ReactionSystem, temperature):
        self.system = system
        self.temperature = temperature

    def model(self, t, y):
        """Definiert das DGL-System d[X]/dt = f(t, y)."""
        dydt = np.zeros_like(y)
        concentrations = y

        for reaction in self.system.reactions:
            # Geschwindigkeitskonstante für die aktuelle Temperatur berechnen
            k = reaction.calculate_k(self.temperature)
            
            # Reaktionsgeschwindigkeit berechnen (v = k * [A]^m * [B]^n)
            rate = k
            for reactant_idx, _ in reaction.reactants:
                # Stelle sicher, dass die Konzentration nicht negativ wird
                conc = concentrations[reactant_idx] if concentrations[reactant_idx] > 0 else 0
                order = reaction.reaction_order.get(reactant_idx, 1)
                rate *= conc ** order
            
            # Konzentrationsänderungen basierend auf der Stöchiometrie
            for reactant_idx, stoich in reaction.reactants:
                dydt[reactant_idx] -= stoich * rate
            for product_idx, stoich in reaction.products:
                dydt[product_idx] += stoich * rate
        
        return dydt

    def solve(self, t_span, t_eval):
        """Löst die DGLs und gibt die Ergebnisse zurück."""
        y0 = self.system.get_initial_concentrations()
        
        solution = solve_ivp(
            fun=self.model,
            t_span=t_span,
            y0=y0,
            t_eval=t_eval,
            method='Radau' # Guter Solver für "steife" DGLs in der Kinetik
        )
        
        return solution