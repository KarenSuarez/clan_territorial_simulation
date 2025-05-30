# clan_territorial_simulation/app.py
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from models.environment import Environment
from models.clan import Clan
from simulation.engine import SimulationEngine
from visualization.renderer import SimulationRenderer
from simulation.modes import StochasticMode, DeterministicMode
from analysis.validation import check_conservation_laws, generate_conservation_report, check_conservation_alert
from analysis.convergence import analyze_convergence, generate_convergence_report
from analysis.sensitivity import run_monte_carlo_simulation, analyze_sensitivity_results, generate_sensitivity_report
from analysis.statistics import calculate_clan_statistics, analyze_variable_correlation, perform_significance_tests, analyze_probability_distributions
from visualization.charts import plot_population_over_time, plot_territory_heatmap, analyze_spatial_patterns, visualize_convergence_metrics
from data.exports.scripts.export_utils import export_simulation_data_csv, export_simulation_data_json, generate_scientific_report_html, generate_animation_html
import numpy as np
import json
from config import GRID_SIZE, INITIAL_CLAN_COUNT, MIN_CLAN_SIZE, MAX_CLAN_SIZE, CONVERGENCE_DTS, CONVERGENCE_STEPS, MONTE_CARLO_RUNS, MONTE_CARLO_STEPS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# --- Configuración de la simulación ---
GRID_X, GRID_Y = GRID_SIZE
simulation_engine = None
renderer = SimulationRenderer()
simulation_running = False
simulation_interval = None
step_requested = False
current_mode = "stochastic" # Default mode
current_config_path = None
current_grid_size = GRID_SIZE # Store the current grid size
simulation_history = []

def initialize_simulation(mode="stochastic", config_path=None, seed=None):
    global simulation_engine, current_mode, current_config_path, current_grid_size, simulation_history
    current_mode = mode
    current_config_path = config_path
    simulation_history = [] # Reset history on new initialization

    config = {}
    if config_path:
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}")

    grid_size = config.get('grid_size', GRID_SIZE)
    current_grid_size = grid_size # Update the current grid size
    initial_clan_count = config.get('initial_clan_count', INITIAL_CLAN_COUNT)
    min_clan_size = config.get('min_clan_size', MIN_CLAN_SIZE)
    max_clan_size = config.get('max_clan_size', MAX_CLAN_SIZE)

    initial_clans = []
    for i in range(initial_clan_count):
        initial_size = np.random.randint(min_clan_size, max_clan_size + 1)
        initial_position = [np.random.randint(0, grid_size[0]), np.random.randint(0, grid_size[1])]
        initial_clans.append(Clan(i + 1, initial_size, initial_position))

    environment = Environment(grid_size=grid_size)

    if mode == "stochastic":
        simulation_mode = StochasticMode(config_path, seed)
    elif mode == "deterministic":
        simulation_mode = DeterministicMode(config_path, seed)
    else:
        raise ValueError(f"Unknown simulation mode: {mode}")

    simulation_engine = SimulationEngine(environment, initial_clans, simulation_mode=simulation_mode)

def run_simulation_step():
    global simulation_engine, simulation_history
    if simulation_engine:
        initial_state = simulation_engine.get_simulation_state()
        simulation_engine.step()
        final_state = simulation_engine.get_simulation_state()
        rendered_state = renderer.render_state(final_state)
        rendered_state['mode'] = current_mode # Send the current mode to the frontend
        socketio.emit('simulation_state', rendered_state)

        # Perform continuous validation (example: conservation)
        conservation_results = check_conservation_laws(initial_state, final_state)
        alerts = check_conservation_alert(conservation_results)
        if alerts:
            print("--- CONSERVATION ALERTS ---")
            for alert in alerts:
                print(alert)
            print("--------------------------")
        simulation_history.append(final_state)

@app.route('/')
def index():
    return render_template('index.html', grid_size=current_grid_size) # Pass grid_size to index.html

@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    if request.method == 'POST':
        mode = request.form.get('simulation_mode')
        config_file = request.form.get('config_file')
        seed = request.form.get('seed')
        initialize_simulation(mode, f"data/configs/{config_file}.json" if config_file else None, int(seed) if seed else None)
    return render_template('simulation.html', current_mode=current_mode, config_files=['stochastic_default', 'deterministic_default', 'small_test', 'large_scale'])

@app.route('/analysis')
def analysis_page():
    population_chart = plot_population_over_time(simulation_history)
    territory_heatmap = plot_territory_heatmap(simulation_history, last_n_steps=100)
    spatial_patterns = analyze_spatial_patterns(simulation_history)
    # Assuming convergence analysis was run and results are stored (replace with actual loading)
    convergence_results = {}
    convergence_plot = visualize_convergence_metrics(convergence_results)
    clan_statistics = calculate_clan_statistics(simulation_history)
    variable_correlation = analyze_variable_correlation(simulation_history)
    significance_tests = perform_significance_tests(simulation_history)
    population_distribution = analyze_probability_distributions(simulation_history)

    return render_template('analysis.html',
                           population_chart=population_chart,
                           territory_heatmap=territory_heatmap,
                           spatial_patterns=spatial_patterns,
                           convergence_plot=convergence_plot,
                           clan_statistics=clan_statistics,
                           variable_correlation=variable_correlation,
                           significance_tests=significance_tests,
                           population_distribution=population_distribution)

@app.route('/analysis/conservation')
def conservation_analysis():
    if not simulation_history:
        return render_template('analysis_report.html', report="No simulation data available for conservation analysis.", analysis_type="Análisis de Conservación")
    initial_state = simulation_history[0] if simulation_history else None
    final_state = simulation_history[-1] if simulation_history else None
    results = check_conservation_laws(initial_state, final_state) if initial_state and final_state else {}
    report = generate_conservation_report(results)
    return render_template('analysis_report.html', report=report, analysis_type="Análisis de Conservación")

@app.route('/analysis/convergence')
def convergence_analysis():
    # Load initial conditions from a default config or the last run
    config_path = current_config_path or "data/configs/small_test.json"
    try:
        with open(config_path, 'r') as f:
            initial_conditions = json.load(f)
    except FileNotFoundError:
        return render_template('analysis_report.html', report=f"Error: Config file not found at {config_path}", analysis_type="Análisis de Convergencia Temporal")

    dts_to_test = CONVERGENCE_DTS
    total_steps = CONVERGENCE_STEPS
    analysis_results = analyze_convergence(initial_conditions, total_steps, dts_to_test)
    report = generate_convergence_report(analysis_results)
    # Optionally save results
    # save_convergence_results(analysis_results)
    return render_template('analysis_report.html', report=report, analysis_type="Análisis de Convergencia Temporal")

@app.route('/analysis/sensitivity')
def sensitivity_analysis():
    num_runs = MONTE_CARLO_RUNS
    num_steps = MONTE_CARLO_STEPS
    monte_carlo_results = run_monte_carlo_simulation(num_runs, num_steps)
    analysis_results = analyze_sensitivity_results(monte_carlo_results)
    report = generate_sensitivity_report(analysis_results)
    return render_template('analysis_report.html', report=report, analysis_type="Análisis de Sensibilidad (Monte Carlo)")

@app.route('/export/<format>')
def export_data(format):
    if not simulation_history:
        return "No simulation data to export."
    if format == 'csv':
        if export_simulation_data_csv(simulation_history):
            return "Datos de simulación exportados a CSV."
        else:
            return "Error al exportar datos a CSV."
    elif format == 'json':
        if export_simulation_data_json(simulation_history):
            return "Datos de simulación exportados a JSON."
        else:
            return "Error al exportar datos a JSON."
    else:
        return "Formato de exportación no válido."

@app.route('/report')
def generate_report():
    if not simulation_history:
        return "No simulation data to generate a report."
    if generate_scientific_report_html(simulation_history, current_mode, current_config_path):
        return "Reporte científico generado en HTML. Puedes encontrarlo en la carpeta `data/exports/report.html`."
    else:
        return "Error al generar el reporte científico."

@app.route('/animation')
def generate_animation():
    if not simulation_history:
        return "No simulation data to generate an animation."
    if generate_animation_html(simulation_history):
        return render_template('animation.html', animation_frames=json.dumps(simulation_history))
    else:
        return "Error al generar la animación."

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    if simulation_engine:
        state = simulation_engine.get_simulation_state()
        rendered_state = renderer.render_state(state)
        rendered_state['mode'] = current_mode
        socketio.emit('simulation_state', rendered_state)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_simulation')
def handle_start_simulation():
    global simulation_running, simulation_interval
    if simulation_engine:
        simulation_running = True
        if simulation_interval is None:
            simulation_interval = socketio.start_background_task(target=simulation_loop)
        print('Simulation started')
    else:
        print('Simulation not initialized. Please select mode and config.')

@socketio.on('pause_simulation')
def handle_pause_simulation():
    global simulation_running
    simulation_running = False
    print('Simulation paused')

@socketio.on('reset_simulation')
def handle_reset_simulation():
    global simulation_running, simulation_interval, simulation_history
    simulation_running = False
    if simulation_interval:
        simulation_interval.kill()
        simulation_interval = None
    simulation_history = []
    # Re-initialize with current mode and config
    if current_mode:
        seed = simulation_engine.simulation_mode.seed if simulation_engine and simulation_engine.simulation_mode else None
        initialize_simulation(current_mode, current_config_path, seed)
        state = simulation_engine.get_simulation_state()
        rendered_state = renderer.render_state(state)
        rendered_state['mode'] = current_mode
        socketio.emit('simulation_state', rendered_state)
        print('Simulation reset')
    else:
        print('No mode selected to reset.')

@socketio.on('step_simulation')
def handle_step_simulation():
    global step_requested
    step_requested = True
    run_simulation_step()
    step_requested = False

def simulation_loop():
    while True:
        if simulation_running or step_requested:
            run_simulation_step()
        socketio.sleep(0.1)

@socketio.on('request_state')
def handle_request_state():
    if simulation_engine:
        state = simulation_engine.get_simulation_state()
        rendered_state = renderer.render_state(state)
        rendered_state['mode'] = current_mode
        socketio.emit('simulation_state', rendered_state)

if __name__ == '__main__':
    socketio.run(app, debug=True)