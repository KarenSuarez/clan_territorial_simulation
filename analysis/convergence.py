# analysis/convergence.py
import numpy as np
from simulation.engine import SimulationEngine
from models.environment import Environment
from models.clan import Clan
import json

CONVERGENCE_TOLERANCE = 0.05

def run_simulation_for_convergence(initial_conditions, total_steps, dt):
    # Crear clanes desde las condiciones iniciales
    if 'clans' in initial_conditions:
        clans_data = initial_conditions['clans']
    else:
        # Generar clanes de ejemplo si no existen
        clans_data = [
            {'id': 1, 'size': 50, 'position': [10, 10], 'parameters': {'birth_rate': 0.1, 'natural_death_rate': 0.05}},
            {'id': 2, 'size': 40, 'position': [30, 30], 'parameters': {'birth_rate': 0.12, 'natural_death_rate': 0.04}}
        ]
    
    # Crear objetos Clan correctamente
    initial_clans = []
    for clan_data in clans_data:
        clan = Clan(
            clan_id=clan_data['id'],
            initial_size=clan_data['size'],
            initial_position=clan_data['position'],
            parameters=clan_data['parameters']
        )
        initial_clans.append(clan)
    
    # Crear engine con parámetros correctos (sin simulation_params)
    engine = SimulationEngine(
        Environment(grid_size=initial_conditions.get('grid_size', [50, 50])),
        initial_clans,
        dt=dt  # Pasar dt directamente
    )
    
    states = [engine.get_simulation_state()]
    for _ in range(int(total_steps / dt)):
        engine.step()  # Usar step() en lugar de run_step()
        states.append(engine.get_simulation_state())
    return states

def calculate_l2_norm(state1, state2):
    """Calcula la norma L2 de la diferencia entre dos estados de la simulación."""
    diff_pop = 0
    max_len = max(len(state1['clans']), len(state2['clans']))
    for i in range(max_len):
        size1 = state1['clans'][i]['size'] if i < len(state1['clans']) else 0
        size2 = state2['clans'][i]['size'] if i < len(state2['clans']) else 0
        diff_pop += (size1 - size2) ** 2

    diff_resource = np.sum((np.array(state1['resource_grid']) - np.array(state2['resource_grid'])) ** 2)
    return np.sqrt(diff_pop + diff_resource)

def richardson_extrapolation(results, dts):
    """Aplica la extrapolación de Richardson para estimar el error de truncamiento."""
    if len(results) < 2:
        return {}

    extrapolated_errors = {}
    sorted_dts = sorted(dts, reverse=True)
    r = sorted_dts[0] / sorted_dts[1]

    if len(results) >= 3:
        r2 = sorted_dts[1] / sorted_dts[2]
        norm12 = calculate_l2_norm(results[sorted_dts[0]][-1], results[sorted_dts[1]][-1])
        norm23 = calculate_l2_norm(results[sorted_dts[1]][-1], results[sorted_dts[2]][-1])
        if norm12 > 1e-9 and norm23 > 1e-9:
            p_est = np.log(norm12 / norm23) / np.log(r)
        else:
            p_est = 1
    else:
        p_est = 1

    for i in range(len(sorted_dts) - 1):
        dt_fine = sorted_dts[i+1]
        dt_coarse = sorted_dts[i]
        state_fine = results[dt_fine][-1]
        state_coarse = results[dt_coarse][-1]
        error_estimate = calculate_l2_norm(state_fine, state_coarse) / (r**p_est - 1)
        extrapolated_errors[f"{dt_fine}/{dt_coarse}"] = error_estimate

    return extrapolated_errors

def analyze_convergence(initial_conditions, total_steps, dts_to_test):
    """Realiza el análisis de convergencia completo."""
    results = {}
    for dt in dts_to_test:
        print(f"Running simulation with dt = {dt}")
        results[dt] = run_simulation_for_convergence(initial_conditions, total_steps, dt)

    convergence_norms = {}
    if results:
        finest_dt = min(results.keys())
        for dt, states in results.items():
            if dt != finest_dt:
                norm = calculate_l2_norm(states[-1], results[finest_dt][-1])
                convergence_norms[f"L2({dt}, {finest_dt})"] = norm

    richardson_errors = richardson_extrapolation(results, list(dts_to_test))
    convergence_achieved = all(norm < CONVERGENCE_TOLERANCE for norm in convergence_norms.values()) if convergence_norms else False

    return {
        'convergence_norms': convergence_norms,
        'richardson_errors': richardson_errors,
        'convergence_achieved': convergence_achieved,
        'tested_dts': list(dts_to_test)
    }

def load_convergence_results(filepath="data/validation/convergence_results.json"):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_convergence_results(results, filepath="data/validation/convergence_results.json"):
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=4)

def generate_convergence_report(analysis_results):
    report = "## Reporte de Análisis de Convergencia\n\n"
    report += "### Normas L2 de Convergencia\n"
    if analysis_results['convergence_norms']:
        for key, value in analysis_results['convergence_norms'].items():
            report += f"- {key}: {value:.4f}\n"
    else:
        report += "No se pudieron calcular las normas de convergencia (insuficientes resultados).\n"

    report += "\n### Estimación del Error de Truncamiento (Extrapolación de Richardson)\n"
    if analysis_results['richardson_errors']:
        for key, value in analysis_results['richardson_errors'].items():
            report += f"- Error estimado para {key}: {value:.4f}\n"
    else:
        report += "No se pudo realizar la extrapolación de Richardson (insuficientes pasos de tiempo).\n"

    report += f"\n### Criterio de Aceptación de Convergencia (||E||_2 < {CONVERGENCE_TOLERANCE:.2f})\n"
    report += f"Convergencia Alcanzada: {'Sí' if analysis_results['convergence_achieved'] else 'No'}\n"
    report += f"\nPasos de Tiempo Probados (dt): {analysis_results['tested_dts']}\n"

    return report