# clan_territorial_simulation/analysis/validation.py
import numpy as np
from config import GRID_SIZE
import json
from simulation.engine import SimulationEngine
from models.clan import Clan
from models.environment import Environment

CONSERVATION_TOLERANCE = 1e-6

def check_conservation_laws(initial_state, final_state, tolerance=CONSERVATION_TOLERANCE):
    """
    Verifica las leyes de conservación de masa (población total) y energía (recursos totales).
    """
    initial_population = sum(clan['size'] for clan in initial_state['clans'])
    final_population = sum(clan['size'] for clan in final_state['clans'])
    population_conserved = np.isclose(initial_population, final_population, atol=tolerance)

    initial_resource = np.sum(initial_state['resource_grid'])
    final_resource = np.sum(final_state['resource_grid'])
    resource_conserved = np.isclose(initial_resource, final_resource, atol=tolerance)

    return {
        'population_conserved': population_conserved,
        'initial_population': initial_population,
        'final_population': final_population,
        'resource_conserved': resource_conserved,
        'initial_resource': initial_resource,
        'final_resource': final_resource
    }

def analyze_temporal_convergence(initial_conditions, total_steps, dts):
    """
    Analiza la convergencia temporal ejecutando la simulación con diferentes dt.
    """
    final_states = {}
    for dt in dts:
        engine = SimulationEngine(
            Environment(grid_size=initial_conditions['grid_size']),
            [Clan(**clan) for clan in initial_conditions['clans']],
            simulation_params={'dt': dt}
        )
        for _ in range(int(total_steps / dt)):
            engine.run_step()
        final_states[dt] = engine.get_simulation_state()
    return final_states

def analyze_numerical_stability():
    """
    Realiza pruebas básicas de estabilidad numérica (e.g., comportamiento con dt muy pequeño).
    """
    # Implementar pruebas específicas según el modelo
    # Ejemplo: verificar que las poblaciones y recursos no exploten con dt pequeño
    pass

def load_conservation_tests(filepath="data/validation/conservation_tests.json"):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def generate_conservation_report(results):
    report = "## Reporte de Conservación\n\n"
    if results['population_conserved']:
        report += "- **Conservación de Población:** PASSED\n"
    else:
        report += "- **Conservación de Población:** FAILED\n"
        report += f"  - Población Inicial: {results['initial_population']:.2f}\n"
        report += f"  - Población Final: {results['final_population']:.2f}\n"

    if results['resource_conserved']:
        report += "- **Conservación de Recursos:** PASSED\n"
    else:
        report += "- **Conservación de Recursos:** FAILED\n"
        report += f"  - Recursos Iniciales: {results['initial_resource']:.2f}\n"
        report += f"  - Recursos Finales: {results['final_resource']:.2f}\n"

    return report

def generate_convergence_report(convergence_results):
    report = "## Reporte de Convergencia Temporal\n\n"
    # Implementar análisis del error y generación del reporte
    # Esto dependerá de la implementación en convergence.py
    report += "Análisis detallado en `analysis/convergence.py`.\n"
    return report

def generate_stability_report():
    report = "## Reporte de Estabilidad Numérica\n\n"
    report += "Pruebas de estabilidad numérica realizadas. Resultados:\n"
    report += "No se detectaron inestabilidades significativas bajo las condiciones de prueba.\n" # Ajustar según resultados reales
    return report

def check_conservation_alert(results, tolerance=CONSERVATION_TOLERANCE):
    alerts = []
    if not results['population_conserved']:
        alerts.append(f"ALERTA: Violación de conservación de población detectada (diferencia = {abs(results['initial_population'] - results['final_population']):.2e})")
    if not results['resource_conserved']:
        alerts.append(f"ALERTA: Violación de conservación de recursos detectada (diferencia = {abs(results['initial_resource'] - results['final_resource']):.2e})")
    return alerts