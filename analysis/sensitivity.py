# analysis/sensitivity.py
import numpy as np
from simulation.engine import SimulationEngine
from models.environment import Environment
from models.clan import Clan
import json
from config import GRID_SIZE, INITIAL_CLAN_COUNT, MIN_CLAN_SIZE, MAX_CLAN_SIZE

def run_monte_carlo_simulation(num_runs=100, num_steps=100, dt=0.1, seed=None):
    """Realiza un análisis de sensibilidad de Monte Carlo."""
    results = []
    rng = np.random.RandomState(seed)

    for i in range(num_runs):
        print(f"Ejecutando simulación de Monte Carlo {i+1}/{num_runs}")
        initial_clans = []
        for j in range(rng.randint(1, INITIAL_CLAN_COUNT + 1)):
            initial_size = rng.randint(MIN_CLAN_SIZE, MAX_CLAN_SIZE + 1)
            initial_position = [rng.randint(0, GRID_SIZE[0]), rng.randint(0, GRID_SIZE[1])]
            
            # Crear objeto Clan correctamente
            clan = Clan(
                clan_id=j + 1,
                initial_size=initial_size,
                initial_position=initial_position,
                parameters={
                    'birth_rate': rng.uniform(0.05, 0.2),
                    'natural_death_rate': rng.uniform(0.01, 0.1)
                }
            )
            initial_clans.append(clan)

        environment = Environment(grid_size=GRID_SIZE)
        
        # Corregir la creación del engine - remover simulation_params y seed
        engine = SimulationEngine(
            environment, 
            initial_clans, 
            dt=dt  # Pasar dt directamente
        )
        
        # Si necesitas semilla, configúrala antes
        if seed:
            np.random.seed(rng.randint(0, 1000000))

        initial_conditions = {
            'clans': [{'id': c.id, 'size': c.size, 'position': c.position.tolist(), 'parameters': c.parameters} for c in initial_clans],
            'grid_size': GRID_SIZE
        }
        
        final_state = None
        for _ in range(num_steps):
            engine.step()  # Usar step() en lugar de run_step()
            final_state = engine.get_simulation_state()

        if final_state:
            results.append({'initial_conditions': initial_conditions, 'final_state': final_state})

    return results

def analyze_sensitivity_results(monte_carlo_results):
    """Analiza los resultados del análisis de sensibilidad de Monte Carlo."""
    if not monte_carlo_results:
        return {"error": "No hay resultados de Monte Carlo para analizar."}

    initial_params = []
    final_populations = []

    for result in monte_carlo_results:
        init_cond = result['initial_conditions']
        final_state = result['final_state']
        total_initial_size = sum(c['size'] for c in init_cond['clans'])
        initial_params.append({
            'num_clans': len(init_cond['clans']),
            'avg_initial_size': total_initial_size / len(init_cond['clans']) if init_cond['clans'] else 0,
            'birth_rates': [c['parameters']['birth_rate'] for c in init_cond['clans']],
            'death_rates': [c['parameters']['natural_death_rate'] for c in init_cond['clans']]
        })
        final_populations.append(sum(c['size'] for c in final_state['clans']))

    # Calcular correlaciones
    correlations = {}
    if initial_params and final_populations:
        try:
            num_clans_corr = np.corrcoef([p['num_clans'] for p in initial_params], final_populations)[0][1]
            correlations['num_clans_vs_final_population'] = num_clans_corr if not np.isnan(num_clans_corr) else 0

            avg_size_corr = np.corrcoef([p['avg_initial_size'] for p in initial_params], final_populations)[0][1]
            correlations['avg_initial_size_vs_final_population'] = avg_size_corr if not np.isnan(avg_size_corr) else 0

            avg_birth_rates = [np.mean(p['birth_rates']) if p['birth_rates'] else 0 for p in initial_params]
            birth_rate_corr = np.corrcoef(avg_birth_rates, final_populations)[0][1]
            correlations['avg_birth_rate_vs_final_population'] = birth_rate_corr if not np.isnan(birth_rate_corr) else 0

            avg_death_rates = [np.mean(p['death_rates']) if p['death_rates'] else 0 for p in initial_params]
            death_rate_corr = np.corrcoef(avg_death_rates, final_populations)[0][1]
            correlations['avg_death_rate_vs_final_population'] = death_rate_corr if not np.isnan(death_rate_corr) else 0
        except Exception as e:
            print(f"Error calculando correlaciones: {e}")
            correlations = {'error': str(e)}

    # Identificar configuraciones críticas
    critical_configs = [res['initial_conditions'] for res in monte_carlo_results 
                       if sum(c['size'] for c in res['final_state']['clans']) == 0]

    return {
        'correlations': correlations,
        'critical_configurations': critical_configs
    }

def generate_sensitivity_report(analysis_results):
    report = "## Reporte de Análisis de Sensibilidad (Monte Carlo)\n\n"
    report += "### Correlaciones entre Condiciones Iniciales y Resultados Finales (Población Total)\n"
    if analysis_results.get('correlations'):
        if 'error' in analysis_results['correlations']:
            report += f"Error en el cálculo de correlaciones: {analysis_results['correlations']['error']}\n"
        else:
            for key, value in analysis_results['correlations'].items():
                report += f"- {key}: {value:.4f}\n"
    else:
        report += "No se pudieron calcular las correlaciones.\n"
       
    report += "\n### Identificación de Configuraciones Críticas (Extinción Total)\n"
    if analysis_results.get('critical_configurations'):
        if analysis_results['critical_configurations']:
            report += f"Se encontraron {len(analysis_results['critical_configurations'])} configuraciones iniciales que llevaron a la extinción total de los clanes:\n"
            for i, config in enumerate(analysis_results['critical_configurations'][:5]):
                report += f"  - Configuración {i+1}: {len(config['clans'])} clanes iniciales\n"
            if len(analysis_results['critical_configurations']) > 5:
                report += "  - ... (más configuraciones críticas encontradas)\n"
        else:
            report += "No se encontraron configuraciones iniciales que llevaran a la extinción total bajo las condiciones de prueba.\n"
    else:
        report += "No se pudo analizar la existencia de configuraciones críticas.\n"

    return report