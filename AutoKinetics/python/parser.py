# backend/parser.py
import json
from collections import Counter  # Importieren Sie den Counter
from data_model import Species, Reaction, ReactionSystem

def parse_kin_file(filepath):
    """Liest eine .kin-Datei und erstellt ein ReactionSystem-Objekt."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # 1. Spezies einlesen
    species_list = [Species(**s) for s in data['species']]

    # Hilfsfunktion, um Knoten (Spezies oder Gruppe) zu Spezies-Indizes aufzulösen
    def resolve_node(node_id, groups_map):
        """
        Löst eine Knoten-ID (entweder ein Spezies-Index oder eine Gruppen-ID)
        in eine Liste von Tupeln (spezies_index, stöchiometrie) auf.
        """
        if isinstance(node_id, int):  # Es ist bereits ein Spezies-Index
            # Einzelne Spezies hat die Stöchiometrie 1
            return [(node_id, 1)]
        elif isinstance(node_id, str) and node_id in groups_map:  # Es ist eine Gruppe
            # Zähle die Vorkommen jedes Spezies-Index in der Gruppe
            item_indices = groups_map[node_id]['items']
            stoichiometry = Counter(item_indices)
            # Gib die Liste der (spezies_index, anzahl) Tupel zurück
            return list(stoichiometry.items())
        return []

    groups_map = {g['id']: g for g in data.get('groups', [])}
    
    # 2. Reaktionen einlesen
    reaction_list = []
    for r_data in data['arrows']:
        # Wandle die Start- und Endknoten in Listen mit Stöchiometrie um
        reactants = resolve_node(r_data['start_id'], groups_map)
        products = resolve_node(r_data['end_id'], groups_map)
        
        # Überspringe, falls Edukte oder Produkte leer sind
        if not reactants or not products:
            continue

        reaction = Reaction(reactants, products, r_data['rate_constant'], **r_data)
        reaction_list.append(reaction)
        
    return ReactionSystem(species_list, reaction_list)