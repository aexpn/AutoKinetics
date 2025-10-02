# backend/parser.py
import json
# KORREKTUR: Relative Imports entfernt
from data_model import Species, Reaction, ReactionSystem

def parse_kin_file(filepath):
    """Liest eine .kin-Datei und erstellt ein ReactionSystem-Objekt."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # 1. Spezies einlesen
    species_list = [Species(**s) for s in data['species']]
    species_map = {s.name: i for i, s in enumerate(species_list)}

    # Hilfsfunktion, um Knoten (Spezies oder Gruppe) zu Spezies-Indizes aufzulösen
    def resolve_node(node_id, groups_map):
        if isinstance(node_id, int): # Es ist bereits ein Spezies-Index
            return [(node_id, 1)] # Annahme: Stöchiometrie ist 1
        elif isinstance(node_id, str) and node_id in groups_map: # Es ist eine Gruppe
            return [(item_idx, 1) for item_idx in groups_map[node_id]['items']]
        return []

    groups_map = {g['id']: g for g in data.get('groups', [])}
    
    # 2. Reaktionen einlesen
    reaction_list = []
    for r_data in data['arrows']:
        reactants = resolve_node(r_data['start_id'], groups_map)
        products = resolve_node(r_data['end_id'], groups_map)
        
        if not reactants or not products: continue

        reaction = Reaction(reactants, products, r_data['rate_constant'], **r_data)
        reaction_list.append(reaction)
        
    return ReactionSystem(species_list, reaction_list)