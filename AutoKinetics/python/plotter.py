# python/plotter.py
import matplotlib.pyplot as plt
import numpy as np

def generate_plots(sim_results, analysis, plot_paths):
    """
    Erstellt und speichert die Ergebnis-Plots in separaten Dateien.
    """
    time = np.array(sim_results['time_points'])
    species_names = sim_results['species_names']
    concentrations = np.array(sim_results['concentrations'])
    
    # 1. Haupt-Plot
    plt.figure(figsize=(8, 6))
    for i, name in enumerate(species_names): plt.plot(time, concentrations[i], label=name)
    plt.title('Konzentrationsverlauf über die Zeit'); plt.xlabel('Zeit (s)'); plt.ylabel('Konzentration (mol/L)')
    plt.legend(); plt.grid(True); plt.tight_layout(); plt.savefig(plot_paths['concentration']); plt.close()

    reactant_to_plot = next(iter(analysis), None)
    if not reactant_to_plot:
        # Leere Plots erstellen, wenn keine Analyse möglich war
        for order_key in ["zero_order", "first_order", "second_order"]:
            plt.figure(figsize=(8, 6)); plt.title(f'Analyse nicht möglich'); plt.text(0.5, 0.5, 'Keine Daten für Analyse.', ha='center', va='center'); plt.savefig(plot_paths[order_key]); plt.close()
        return

    analysis_data = analysis[reactant_to_plot]
    reactant_name = analysis_data['analyzed_reactant']
    reactant_idx = species_names.index(reactant_name)
    reactant_conc = concentrations[reactant_idx]
    valid_indices = reactant_conc > 1e-9
    time_valid, conc_valid = time[valid_indices], reactant_conc[valid_indices]

    # Titel mit Einheiten
    k0 = analysis_data['all_fits']['zero_order']['k']
    u0 = analysis_data['all_fits']['zero_order']['unit']
    k1 = analysis_data['all_fits']['first_order']['k']
    u1 = analysis_data['all_fits']['first_order']['unit']
    k2 = analysis_data['all_fits']['second_order']['k']
    u2 = analysis_data['all_fits']['second_order']['unit']

    # 2. Plot: 0. Ordnung
    plt.figure(figsize=(8, 6)); plt.plot(time_valid, conc_valid, 'o', label=f'[{reactant_name}]')
    plt.title(f'Analyse 0. Ordnung (k = {k0:.3f} {u0})'); plt.xlabel('Zeit (s)'); plt.ylabel('Konzentration (mol/L)')
    plt.grid(True); plt.legend(); plt.tight_layout(); plt.savefig(plot_paths['zero_order']); plt.close()

    # 3. Plot: 1. Ordnung
    plt.figure(figsize=(8, 6)); plt.plot(time_valid, np.log(conc_valid), 'o', label=f'ln([{reactant_name}])')
    plt.title(f'Analyse 1. Ordnung (k = {k1:.3f} {u1})'); plt.xlabel('Zeit (s)'); plt.ylabel('ln(Konzentration)')
    plt.grid(True); plt.legend(); plt.tight_layout(); plt.savefig(plot_paths['first_order']); plt.close()

    # 4. Plot: 2. Ordnung
    plt.figure(figsize=(8, 6)); plt.plot(time_valid, 1 / conc_valid, 'o', label=f'1/[{reactant_name}]')
    plt.title(f'Analyse 2. Ordnung (k = {k2:.3f} {u2})'); plt.xlabel('Zeit (s)'); plt.ylabel('1/Konzentration (L/mol)')
    plt.grid(True); plt.legend(); plt.tight_layout(); plt.savefig(plot_paths['second_order']); plt.close()