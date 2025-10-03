import sys
import json
import numpy as np
import argparse
from pathlib import Path
from parser import parse_kin_file
from simulator import ODESolver
from analyzer import analyze_kinetics
from plotter import generate_plots

def run_simulation_and_analysis(kin_filepath, sim_time_s, temp_K, plot_dir):
    """
    Führt die gesamte Kette aus: Parsen, Simulieren, Analysieren, Plotten.
    """
    reaction_system = parse_kin_file(kin_filepath)
    solver = ODESolver(reaction_system, temperature=temp_K)
    t_span = (0, sim_time_s)
    t_eval = np.linspace(*t_span, num=200)
    solution = solver.solve(t_span, t_eval)
    
    sim_results = {
        "time_points": solution.t.tolist(),
        "species_names": [s.name for s in reaction_system.species],
        "concentrations": solution.y.tolist(),
        "simulation_parameters": {"duration_s": sim_time_s, "temperature_K": temp_K}
    }
    
    analysis_results = analyze_kinetics(sim_results, reaction_system)
    
    # generate_plots gibt jetzt ein Dictionary mit allen Dateipfaden zurück
    plot_files = generate_plots(sim_results, analysis_results, plot_dir)
    
    return {
        "simulation": sim_results,
        "analysis": analysis_results,
        "plot_files": plot_files
    }

def main():
    parser = argparse.ArgumentParser(description="Run a chemical kinetics simulation.")
    parser.add_argument("kin_file", help="Path to the .kin input file.")
    parser.add_argument("-t", "--time", type=float, default=10.0, help="Simulation time in seconds.")
    parser.add_argument("-T", "--temp", type=float, default=298.15, help="Temperature in Kelvin.")
    parser.add_argument("--plot_dir", required=True, help="Directory to save output plots.")
    args = parser.parse_args()

    try:
        final_results = run_simulation_and_analysis(
            kin_filepath=args.kin_file, 
            sim_time_s=args.time, 
            temp_K=args.temp,
            plot_dir=args.plot_dir
        )
        print(json.dumps(final_results, indent=4))
    except Exception as e:
        print(json.dumps({"error": str(e), "traceback": str(e.__traceback__)}))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        # Manueller Test-Modus
        print("--- Manueller Test-Modus ---")
        # Hier könnten Sie Testcode einfügen, falls gewünscht
        pass