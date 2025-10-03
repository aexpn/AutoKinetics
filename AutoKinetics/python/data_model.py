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
        except (ValueError, TypeError):
            # Fallback, falls 'reaction_order' keine gültige Zahl ist
            for r_idx, stoich in self.reactants:
                # Standardmäßig wird die Ordnung gleich dem stöchiometrischen Faktor gesetzt
                self.reaction_order[r_idx] = stoich

    def calculate_k(self, T):
        """Berechnet die Geschwindigkeitskonstante k bei Temperatur T."""
        if self.arrhenius_A == 0: return 0.0
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

    def get_rate_law_equations(self):
        """Erstellt eine korrekte textuelle Darstellung des differentiellen Zeitgesetzes."""
        equations = []
        species_names = [s.name for s in self.species]
        
        for i, species in enumerate(self.species):
            lhs = f"d[{species_names[i]}]/dt ="
            rhs_terms = []

            for reaction in self.reactions:
                # Der Ratenterm (v) = k * [Edukt1]^ordnung1 * [Edukt2]^ordnung2
                rate_expression_parts = [reaction.rate_label]
                for reactant_idx, _ in reaction.reactants:
                    order = reaction.reaction_order.get(reactant_idx, 1.0)
                    order_str = f"^{order}" if order != 1.0 else ""
                    rate_expression_parts.append(f"[{species_names[reactant_idx]}]" + order_str)
                rate_expr = " * ".join(rate_expression_parts)

                # Die Änderungsrate ist ±stöchiometrischer_Faktor * v
                for reactant_idx, stoich in reaction.reactants:
                    if reactant_idx == i:
                        stoich_str = f"{stoich} * " if stoich != 1 else ""
                        rhs_terms.append(f"- {stoich_str}{rate_expr}")
                        
                for product_idx, stoich in reaction.products:
                    if product_idx == i:
                        stoich_str = f"{stoich} * " if stoich != 1 else ""
                        rhs_terms.append(f"+ {stoich_str}{rate_expr}")
            
            if not rhs_terms:
                rhs = " 0.0"
            else:
                rhs = " ".join(rhs_terms)
                # Führendes '+' oder '-' anpassen für saubere Darstellung
                if rhs.startswith("+ "):
                    rhs = rhs[1:]
                elif rhs.startswith("- "):
                    rhs = "-" + rhs[1:]

            equations.append(lhs + rhs)
            
        return "\n".join(equations)