import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def generate_plots(sim_results, analysis, plot_dir):
    """
    Erstellt und speichert die Ergebnis-Plots für die Gesamtübersicht und
    für jeden einzelnen analysierten Reaktionsschritt.
    """
    plot_dir = Path(plot_dir)
    plot_dir.mkdir(exist_ok=True)
    
    time = np.array(sim_results['time_points'])
    species_names = sim_results['species_names']
    concentrations = np.array(sim_results['concentrations'])
    
    # Dictionary zum Sammeln aller erstellten Dateipfade
    plot_files = {}

    # 1. Haupt-Plot (Konzentrationsverlauf)
    plt.figure(figsize=(10, 7))
    for i, name in enumerate(species_names):
        plt.plot(time, concentrations[i], label=name)
    plt.title('Konzentrationsverlauf über die Zeit')
    plt.xlabel('Zeit (s)')
    plt.ylabel('Konzentration (mol/L)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    concentration_plot_path = plot_dir / "concentration.png"
    plt.savefig(concentration_plot_path)
    plt.close()
    plot_files["concentration"] = str(concentration_plot_path)

    # 2. Analyse-Plots für JEDE Reaktion im Analyse-Ergebnis
    analysis_plots = {}
    for rate_label, analysis_data in analysis.items():
        reactant_name = analysis_data['analyzed_reactant']
        try:
            reactant_idx = species_names.index(reactant_name)
        except ValueError:
            continue

        reactant_conc = concentrations[reactant_idx]
        
        # Nur valide Datenpunkte für die Analyse verwenden
        valid_indices = reactant_conc > 1e-9
        time_valid = time[valid_indices]
        conc_valid = reactant_conc[valid_indices]

        if len(time_valid) < 2:
            continue

        k_fits = analysis_data.get('all_fits', {})
        paths_for_reaction = {}

        # Plot: 0. Ordnung
        k0_info = k_fits.get('zero_order', {})
        k0 = k0_info.get('k', 0)
        u0 = k0_info.get('unit', 'mol·L⁻¹·s⁻¹')
        plt.figure(figsize=(8, 6))
        plt.plot(time_valid, conc_valid, 'o', label=f'[{reactant_name}]')
        plt.title(f'Analyse 0. Ordnung für {rate_label} (k = {k0:.3g} {u0})')
        plt.xlabel('Zeit (s)')
        plt.ylabel('Konzentration (mol/L)')
        plt.grid(True); plt.legend(); plt.tight_layout()
        path = plot_dir / f"{rate_label}_zero_order.png"
        plt.savefig(path)
        plt.close()
        paths_for_reaction["zero_order"] = str(path)
        
        # Plot: 1. Ordnung
        k1_info = k_fits.get('first_order', {})
        k1 = k1_info.get('k', 0)
        u1 = k1_info.get('unit', 's⁻¹')
        plt.figure(figsize=(8, 6))
        plt.plot(time_valid, np.log(conc_valid), 'o', label=f'ln([{reactant_name}])')
        plt.title(f'Analyse 1. Ordnung für {rate_label} (k = {k1:.3g} {u1})')
        plt.xlabel('Zeit (s)')
        plt.ylabel('ln(Konzentration)')
        plt.grid(True); plt.legend(); plt.tight_layout()
        path = plot_dir / f"{rate_label}_first_order.png"
        plt.savefig(path)
        plt.close()
        paths_for_reaction["first_order"] = str(path)

        # Plot: 2. Ordnung
        k2_info = k_fits.get('second_order', {})
        k2 = k2_info.get('k', 0)
        u2 = k2_info.get('unit', 'L·mol⁻¹·s⁻¹')
        plt.figure(figsize=(8, 6))
        plt.plot(time_valid, 1 / conc_valid, 'o', label=f'1/[{reactant_name}]')
        plt.title(f'Analyse 2. Ordnung für {rate_label} (k = {k2:.3g} {u2})')
        plt.xlabel('Zeit (s)')
        plt.ylabel('1/Konzentration (L/mol)')
        plt.grid(True); plt.legend(); plt.tight_layout()
        path = plot_dir / f"{rate_label}_second_order.png"
        plt.savefig(path)
        plt.close()
        paths_for_reaction["second_order"] = str(path)
        
        analysis_plots[rate_label] = paths_for_reaction
        
    plot_files["analysis_plots"] = analysis_plots
    return plot_files