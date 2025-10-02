# python/analyzer.py
import numpy as np
from scipy import stats

def fit_reaction_order(time, concentration):
    """
    Führt eine lineare Regression für 0., 1. und 2. Ordnung durch.
    Gibt die Ergebnisse für alle drei Ordnungen zurück.
    """
    results = {}
    valid_indices = concentration > 1e-9
    if np.count_nonzero(valid_indices) < 2: return None

    time_valid, conc_valid = time[valid_indices], concentration[valid_indices]

    # 0. Ordnung: [A] vs. t -> k hat Einheit mol L⁻¹ s⁻¹
    slope, _, r_val, _, _ = stats.linregress(time_valid, conc_valid)
    results['zero_order'] = {'r_squared': r_val**2, 'k': -slope, 'unit': 'mol·L⁻¹·s⁻¹'}

    # 1. Ordnung: ln[A] vs. t -> k hat Einheit s⁻¹
    slope, _, r_val, _, _ = stats.linregress(time_valid, np.log(conc_valid))
    results['first_order'] = {'r_squared': r_val**2, 'k': -slope, 'unit': 's⁻¹'}

    # 2. Ordnung: 1/[A] vs. t -> k hat Einheit L mol⁻¹ s⁻¹
    slope, _, r_val, _, _ = stats.linregress(time_valid, 1 / conc_valid)
    results['second_order'] = {'r_squared': r_val**2, 'k': slope, 'unit': 'L·mol⁻¹·s⁻¹'}

    return results

def analyze_kinetics(sim_results, reaction_system):
    """
    Analysiert die Simulation und strukturiert die Ergebnisse pro Reaktionspfeil.
    """
    analysis = {}
    time = np.array(sim_results['time_points'])
    
    for reaction in reaction_system.reactions:
        if not reaction.reactants: continue
        
        best_reactant_for_analysis, max_decrease = None, -1
        for reactant_idx, _ in reaction.reactants:
            concentration = np.array(sim_results['concentrations'][reactant_idx])
            if concentration[0] > concentration[-1]:
                decrease = concentration[0] - concentration[-1]
                if decrease > max_decrease:
                    max_decrease, best_reactant_for_analysis = decrease, reactant_idx

        if best_reactant_for_analysis is not None:
            reactant_idx = best_reactant_for_analysis
            reactant_name = reaction_system.species[reactant_idx].name
            concentration = np.array(sim_results['concentrations'][reactant_idx])
            fit_results = fit_reaction_order(time, concentration)
            if fit_results:
                best_order = max(fit_results, key=lambda k: fit_results[k]['r_squared'])
                
                analysis[reaction.rate_label] = {
                    'analyzed_reactant': reactant_name,
                    'best_fit_order': best_order,
                    'calculated_k': fit_results[best_order]['k'],
                    'k_unit': fit_results[best_order]['unit'], # Einheit hinzufügen
                    'r_squared': fit_results[best_order]['r_squared'],
                    'all_fits': fit_results
                }
    return analysis