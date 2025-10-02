import sys
import json
import numpy as np
import argparse
from pathlib import Path
from parser import parse_kin_file
from simulator import ODESolver
from analyzer import analyze_kinetics
from plotter import generate_plots

def run_simulation_and_analysis(kin_filepath, sim_time_s, temp_K, plot_paths):
    """
    Führt die gesamte Kette aus: Parsen, Simulieren, Analysieren, Plotten.
    """
    reaction_system = parse_kin_file(kin_filepath)
    solver = ODESolver(reaction_system, temperature=temp_K)
    t_span = (0, sim_time_s)
    t_eval = np.linspace(*t_span, num=100)
    solution = solver.solve(t_span, t_eval)
    
    sim_results = {
        "time_points": solution.t.tolist(),
        "species_names": [s.name for s in reaction_system.species],
        "concentrations": solution.y.tolist(),
        "simulation_parameters": {"duration_s": sim_time_s, "temperature_K": temp_K}
    }
    
    analysis_results = analyze_kinetics(sim_results, reaction_system)
    
    generate_plots(sim_results, analysis_results, plot_paths)
    
    return {
        "simulation": sim_results,
        "analysis": analysis_results,
        "plot_files": plot_paths
    }

def main():
    """
    Diese Funktion wird aufgerufen, wenn das Skript von der GUI (via subprocess)
    mit Kommandozeilen-Argumenten gestartet wird.
    """
    parser = argparse.ArgumentParser(description="Run a chemical kinetics simulation.")
    parser.add_argument("kin_file", help="Path to the .kin input file.")
    parser.add_argument("-t", "--time", type=float, default=10.0, help="Simulation time in seconds.")
    parser.add_argument("-T", "--temp", type=float, default=298.15, help="Temperature in Kelvin.")
    parser.add_argument("--p_conc", required=True, help="Output path for concentration plot.")
    parser.add_argument("--p_zero", required=True, help="Output path for zero order plot.")
    parser.add_argument("--p_first", required=True, help="Output path for first order plot.")
    parser.add_argument("--p_second", required=True, help="Output path for second order plot.")
    args = parser.parse_args()

    plot_paths = {
        "concentration": args.p_conc, "zero_order": args.p_zero,
        "first_order": args.p_first, "second_order": args.p_second
    }

    try:
        final_results = run_simulation_and_analysis(
            kin_filepath=args.kin_file, 
            sim_time_s=args.time, 
            temp_K=args.temp,
            plot_paths=plot_paths
        )
        print(json.dumps(final_results, indent=4))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == '__main__':
    # Überprüfen, ob Argumente übergeben wurden. Wenn nicht, sind wir im manuellen Test-Modus.
    if len(sys.argv) > 1:
        # GUI-Modus: Argumente werden verarbeitet
        main()
    else:
        # Manueller Test-Modus: Benutze Standardwerte
        print("--- Manueller Test-Modus ---")
        try:
            SCRIPT_DIR = Path(__file__).resolve().parent
            PROJECT_ROOT = SCRIPT_DIR.parent
            kin_file = PROJECT_ROOT / 'test_first_order.kin'
            
            if not kin_file.exists():
                raise FileNotFoundError(f"Testdatei '{kin_file.name}' nicht im Projekt-Hauptordner gefunden.")

            # Standard-Pfade für die Plots definieren
            plot_paths = {
                "concentration": "test_concentration_plot.png",
                "zero_order": "test_zero_order_plot.png",
                "first_order": "test_first_order_plot.png",
                "second_order": "test_second_order_plot.png",
            }
            
            final_results = run_simulation_and_analysis(
                kin_filepath=kin_file, 
                sim_time_s=30.0, 
                temp_K=298.15,
                plot_paths=plot_paths
            )
            print(json.dumps(final_results, indent=4))
        except Exception as e:
            print(json.dumps({"error": str(e)}))