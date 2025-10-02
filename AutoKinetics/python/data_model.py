import numpy as np

R = 8.31446261815324  # Universelle Gaskonstante in J/(mol·K)

class Species:
    """Repräsentiert eine einzelne chemische Spezies mit ihren Eigenschaften."""
    def __init__(self, name, **kwargs):
        self.name = name
        self.start_concentration = float(kwargs.get('start_concentration', 1.0))
        self.concentration = self.start_concentration
        
        for key, value in kwargs.items():
            setattr(self, key, value)

class Reaction:
    """Repräsentiert eine einzelne Reaktion mit ihren kinetischen Parametern."""
    def __init__(self, reactants, products, rate_label, **params):
        self.reactants = reactants
        self.products = products
        self.rate_label = rate_label
        
        self.arrhenius_A = float(params.get('arrhenius_A', 1.0))
        self.activation_energy_Ea = float(params.get('activation_energy_Ea', 0.0))
        self.temp_exponent_n = float(params.get('temperature_exponent_n', 0.0))
        
        self.reaction_order = {}
        try:
            order_val = float(params.get('reaction_order', '1'))
            for r_idx, _ in self.reactants:
                self.reaction_order[r_idx] = order_val
        except ValueError:
            for r_idx, _ in self.reactants:
                self.reaction_order[r_idx] = 1.0

    def calculate_k(self, T):
        """Berechnet die Geschwindigkeitskonstante k bei Temperatur T."""
        if self.arrhenius_A == 0: return 0.0
        
        # --- KORREKTUR ---
        # Die Multiplikation mit 1000 wurde entfernt.
        # Wir gehen davon aus, dass Ea in der .kin-Datei immer in J/mol angegeben ist.
        Ea_J_mol = self.activation_energy_Ea
        
        k = self.arrhenius_A * (T ** self.temp_exponent_n) * np.exp(-Ea_J_mol / (R * T))
        return k

class ReactionSystem:
    """Verwaltet das gesamte System aus Spezies und Reaktionen."""
    def __init__(self, species_list, reaction_list):
        self.species = species_list
        self.reactions = reaction_list
        self.species_map = {s.name: i for i, s in enumerate(species_list)}

    def get_initial_concentrations(self):
        return np.array([s.start_concentration for s in self.species])