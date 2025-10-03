# backend/parser.py
import json
from collections import Counter
from data_model import Species, Reaction, ReactionSystem

def parse_kin_file(filepath):
    """Liest eine .kin-Datei und erstellt ein ReactionSystem-Objekt."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    species_list = [Species(**s) for s in data['species']]

    def resolve_node_to_indices(node_id, groups_map):
        """Löst eine Knoten-ID in eine flache Liste von Spezies-Indizes auf."""
        if isinstance(node_id, int):
            return [node_id]
        elif isinstance(node_id, str) and node_id in groups_map:
            return groups_map[node_id]['items']
        return []

    groups_map = {g['id']: g for g in data.get('groups', [])}
    
    reaction_list = []
    for r_data in data['arrows']:
        reactant_indices = resolve_node_to_indices(r_data['start_id'], groups_map)
        product_indices = resolve_node_to_indices(r_data['end_id'], groups_map)

        # Grund-Stöchiometrie durch Zählen ermitteln
        reactant_stoich = Counter(reactant_indices)
        product_stoich = Counter(product_indices)

        # Manuell gesetzte Stöchiometrie explizit überschreiben
        if 'stoichiometry' in r_data:
            # HINWEIS: dict.update() überschreibt Werte, während Counter.update() sie addiert.
            # Wir verwenden hier das Standard-Verhalten von dict.update(), um den Fehler zu beheben.
            explicit_reactants = {int(k): v for k, v in r_data['stoichiometry'].get('reactants', {}).items()}
            explicit_products = {int(k): v for k, v in r_data['stoichiometry'].get('products', {}).items()}
            
            # Wende die expliziten Faktoren an, indem die gezählten Werte überschrieben werden.
            for idx, factor in explicit_reactants.items():
                reactant_stoich[idx] = factor
            for idx, factor in explicit_products.items():
                product_stoich[idx] = factor
        
        reactants = list(reactant_stoich.items())
        products = list(product_stoich.items())
        
        if not reactants or not products:
            continue

        reaction = Reaction(reactants, products, r_data['rate_constant'], **r_data)
        reaction_list.append(reaction)
        
    return ReactionSystem(species_list, reaction_list)