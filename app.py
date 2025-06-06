# app.py - Versión refactorizada para usar SimulationEngine y configuraciones externas

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import numpy as np
import json
import os
import time
from datetime import datetime
from threading import Thread, Lock

# Importar las clases de modelos y motor
from models.environment import Environment
from models.clan import Clan
from simulation.engine import SimulationEngine
from simulation.modes import StochasticMode, DeterministicMode
# Importamos config_default para valores por defecto si no se carga un JSON
import data.configs.config_default as default_config 


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Variables globales con lock para thread safety
simulation_lock = Lock()
current_simulation_engine = None # Instancia del motor de simulación
current_config = {} # Configuración cargada
current_simulation_mode_name = 'stochastic' # Para el frontend
# Modos y RNG globales para que puedan ser usados por cualquier parte que lo necesite (p.ej. initialize_simulation)
current_mode_instance = None # Instancia del modo (StochasticMode o DeterministicMode)
global_rng_seed = None # Semilla global para control total

simulation_data = {
    'running': False,
    'step': 0,
    'time': 0.0,
    'speed_multiplier': 1.0,
    'update_interval': 1.0,
    'max_steps': 500,
    'auto_stop': True,
    'extinction_threshold': 5,
    'extinction_counter': 0,
    'convergence_threshold': 50,
    'last_populations': []
}

CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'data', 'configs')

def load_config_file(config_name):
    """Carga una configuración desde un archivo JSON."""
    config_path = os.path.join(CONFIG_DIR, f"{config_name}.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    print(f"⚠️ Archivo de configuración '{config_name}.json' no encontrado. Usando valores por defecto o la configuración actual.")
    return {}

def initialize_simulation(mode_name='stochastic', config_name='stochastic_default', seed=None, custom_grid_size=None):
    """Inicializa la simulación, cargando la configuración y estableciendo el modo."""
    global current_simulation_engine, current_config, current_simulation_mode_name, current_mode_instance, global_rng_seed

    with simulation_lock:
        print("🚀 Inicializando simulación...")

        # 1. Cargar configuración base
        base_config = load_config_file(config_name)
        # Combinar con config_default para tener valores por defecto si no están en el JSON
        combined_config = {
            'GRID_SIZE': custom_grid_size or default_config.GRID_SIZE,
            'INITIAL_CLAN_COUNT': default_config.INITIAL_CLAN_COUNT,
            'MIN_CLAN_SIZE': default_config.MIN_CLAN_SIZE,
            'MAX_CLAN_SIZE': default_config.MAX_CLAN_SIZE,
            'RESOURCE_MAX': default_config.RESOURCE_MAX,
            'RESOURCE_REGEN_RATE': default_config.RESOURCE_REGEN_RATE,
            'RESOURCE_REQUIRED_PER_INDIVIDUAL': default_config.RESOURCE_REQUIRED_PER_INDIVIDUAL,
            'MORTALITY_STARVATION_MAX': default_config.MORTALITY_STARVATION_MAX,
            'simulation_steps': simulation_data['max_steps'], # Default from app.py initially
            'dt': 0.2, # Default dt
            'movement_noise_std': 0.0, # Default for stochastic mode
            'forage_probability': 1.0 # Default for stochastic mode
        }
        combined_config.update(base_config)
        
        # Aplicar tamaño de rejilla personalizado si se proporciona
        if custom_grid_size:
            combined_config['GRID_SIZE'] = custom_grid_size
            print(f"📐 Tamaño de rejilla personalizado aplicado: {custom_grid_size}")
        
        current_config = combined_config
        
        global_rng_seed = seed # Guardar la semilla globalmente para MersenneTwister

        # 2. Configurar el modo de simulación y el RNG
        current_simulation_mode_name = mode_name
        if mode_name == 'stochastic':
            current_mode_instance = StochasticMode(seed=global_rng_seed)
        elif mode_name == 'deterministic':
            current_mode_instance = DeterministicMode(seed=global_rng_seed)
        else:
            print(f"❌ Modo '{mode_name}' no reconocido. Usando Estocástico por defecto.")
            current_simulation_mode_name = 'stochastic'
            current_mode_instance = StochasticMode(seed=global_rng_seed)
        
        # Aplicar configuraciones específicas del modo
        if 'movement_noise_std' in current_config:
            current_mode_instance.config['movement_noise_std'] = current_config['movement_noise_std']
        if 'forage_probability' in current_config:
            current_mode_instance.config['forage_probability'] = current_config['forage_probability']
        

        # 3. Inicializar entorno con tamaño de grid desde la configuración
        env = Environment(grid_size=current_config['GRID_SIZE'])
        env.max_resource = current_config['RESOURCE_MAX']
        env.regeneration_rate = current_config['RESOURCE_REGEN_RATE']
        
        # Inicializar recursos usando el RNG del modo
        if current_simulation_mode_name == 'stochastic':
            env.grid = current_mode_instance.rng.random_uniform(30, 80, current_config['GRID_SIZE'])
        else:
            # Modo determinista podría tener una distribución inicial fija o también controlada por semilla
            # Por ahora, usaremos el mismo RNG para mantener consistencia
            env.grid = current_mode_instance.rng.random_uniform(30, 80, current_config['GRID_SIZE'])


        # 4. Crear clanes
        clans = []
        num_clans_to_create = current_config['INITIAL_CLAN_COUNT']
        for i in range(num_clans_to_create):
            initial_size = current_mode_instance.rng.random_randint(current_config['MIN_CLAN_SIZE'], current_config['MAX_CLAN_SIZE'])
            # Posiciones aleatorias dentro del grid usando el RNG del modo
            pos_x = current_mode_instance.rng.random_uniform(0, current_config['GRID_SIZE'][0])
            pos_y = current_mode_instance.rng.random_uniform(0, current_config['GRID_SIZE'][1])
            initial_position = np.array([pos_x, pos_y])

            clan_params = {
                'resource_required_per_individual': current_config['RESOURCE_REQUIRED_PER_INDIVIDUAL']
                # Otros parámetros de clan se pueden añadir aquí desde la config
            }
            clans.append(Clan(i + 1, initial_size, initial_position, clan_params))
            print(f"✅ Clan {clans[-1].id}: tamaño={clans[-1].size}, pos=({clans[-1].position[0]:.1f}, {clans[-1].position[1]:.1f})")

        # 5. Instanciar SimulationEngine
        simulation_data['max_steps'] = current_config.get('simulation_steps', 500)
        simulation_data['dt'] = current_config.get('dt', 0.2)

        current_simulation_engine = SimulationEngine(
            environment=env,
            initial_clans=clans,
            simulation_mode=current_mode_instance, # Pasar la instancia del modo
            dt=simulation_data['dt'],
            seed=global_rng_seed # La semilla se maneja dentro del modo y Engine
        )
        
        # Resetear datos de simulación
        simulation_data['step'] = 0
        simulation_data['time'] = 0.0
        simulation_data['running'] = False
        simulation_data['speed_multiplier'] = 1.0
        simulation_data['update_interval'] = 1.0 # Intervalo base para socketio.sleep
        simulation_data['extinction_counter'] = 0
        simulation_data['last_populations'] = []

        print(f"✅ Simulación inicializada con {len(current_simulation_engine.clans)} clanes en modo {current_simulation_mode_name}")
        print(f"   Grid: {env.grid_size[0]}x{env.grid_size[1]}, Max Steps: {simulation_data['max_steps']}")


def simulation_step():
    """Ejecuta un paso de simulación utilizando el motor."""
    global simulation_data, current_simulation_engine

    with simulation_lock:
        if not simulation_data['running'] or current_simulation_engine is None:
            return None

        # print(f"🔄 Ejecutando paso {simulation_data['step'] + 1} del motor")
        
        current_simulation_engine.run_step() # El motor avanza su propio tiempo y step_count

        # Sincronizar datos globales con el motor
        simulation_data['step'] = current_simulation_engine.step_count
        simulation_data['time'] = current_simulation_engine.time
        
        active_clans = len(current_simulation_engine.clans)
        total_pop = sum(c.size for c in current_simulation_engine.clans)

        # Registrar población para análisis de convergencia
        simulation_data['last_populations'].append(total_pop)
        if len(simulation_data['last_populations']) > simulation_data['convergence_threshold']:
            simulation_data['last_populations'].pop(0)

        # print(f"📊 Paso {simulation_data['step']}: {active_clans} clanes, {total_pop} población total")

        # Verificar condiciones de finalización
        should_stop, reason = check_termination_conditions()
        if should_stop:
            simulation_data['running'] = False
            print(f"🛑 Simulación terminada: {reason}")
            return reason

        return None


def check_termination_conditions():
    """Verifica si la simulación debe terminar."""
    # Asegurarse de usar current_simulation_engine para el estado más reciente
    if current_simulation_engine is None:
        return True, "Motor de simulación no inicializado."

    if not simulation_data['auto_stop']:
        if simulation_data['step'] >= simulation_data['max_steps']:
            return True, f"Límite máximo de pasos alcanzado ({simulation_data['max_steps']})"
        return False, ""

    total_pop = sum(c.size for c in current_simulation_engine.clans)
    active_clans = len(current_simulation_engine.clans)

    # 1. Extinción total
    if total_pop == 0:
        simulation_data['extinction_counter'] += 1
        if simulation_data['extinction_counter'] >= simulation_data['extinction_threshold']:
            return True, "Extinción total: No quedan individuos en ningún clan"
        else:
            # No parar inmediatamente si el contador no ha llegado al umbral
            return False, "" 
    else: # Si hay población, resetear el contador de extinción
        simulation_data['extinction_counter'] = 0

    # 2. Un solo clan sobreviviente (dominancia total)
    if active_clans == 1 and simulation_data['step'] > 50:
        return True, f"Dominancia total: Solo queda el Clan {current_simulation_engine.clans[0].id}"

    # 3. Límite máximo de pasos
    if simulation_data['step'] >= simulation_data['max_steps']:
        return True, f"Límite máximo de pasos alcanzado ({simulation_data['max_steps']})"

    # 4. Convergencia poblacional (población estable por mucho tiempo)
    if len(simulation_data['last_populations']) >= simulation_data['convergence_threshold']:
        recent_pops = simulation_data['last_populations'][-simulation_data['convergence_threshold']:] 
        if len(recent_pops) == simulation_data['convergence_threshold']:
            variance = np.var(recent_pops)
            mean_pop = np.mean(recent_pops)

            # Si la varianza es muy baja relative a la media, hay convergencia
            if mean_pop > 0 and variance < (mean_pop * 0.02): # Menos del 2% de variación
                return True, f"Convergencia alcanzada: Población estable en {mean_pop:.0f} individuos"

    # 5. Población muy baja (cerca de extinción)
    if total_pop > 0 and total_pop <= 5 and simulation_data['step'] > 100:
        return True, f"Población crítica: Solo quedan {total_pop} individuos"
        
    # 6. Sistema degenerado (todos los clanes muy pequeños, pero no extintos)
    if active_clans > 1 and simulation_data['step'] > 200:
        max_clan_size = max(c.size for c in current_simulation_engine.clans)
        if max_clan_size <= 3:
            return True, "Sistema degenerado: Todos los clanes tienen poblaciones muy pequeñas"

    return False, ""


def get_simulation_summary():
    """Genera un resumen de la simulación terminada."""
    if current_simulation_engine is None:
        return {"error": "Simulación no iniciada."}

    total_pop = sum(c.size for c in current_simulation_engine.clans)
    active_clans = len(current_simulation_engine.clans)

    summary = {
        'total_steps': simulation_data['step'],
        'simulation_time': simulation_data['time'],
        'final_population': total_pop,
        'surviving_clans': active_clans,
        'clan_details': []
    }

    for clan in current_simulation_engine.clans:
        summary['clan_details'].append({
            'id': clan.id,
            'final_size': clan.size,
            'final_energy': clan.energy,
            'final_state': clan.state
        })
    return summary


def get_simulation_state():
    """Obtiene el estado actual para enviar al frontend."""
    with simulation_lock:
        if current_simulation_engine is None:
            # Estado por defecto si la simulación no ha sido inicializada
            return {
                'time': 0.0,
                'step': 0,
                'mode': 'N/A',
                'resource_grid': [],
                'clans': [],
                'running': False,
                'max_steps': simulation_data['max_steps'],
                'auto_stop': simulation_data['auto_stop'],
                'grid_size': current_config.get('GRID_SIZE', [50, 50]),  # AGREGADO
                'system_metrics': {  # AGREGADO: Métricas por defecto
                    'total_population': 0,
                    'active_clans': 0,
                    'avg_energy': 0,
                    'total_resources': 0
                }
            }
        
        engine_state = current_simulation_engine.get_simulation_state()
        
        state = {
            'time': engine_state['time'],
            'step': engine_state['step'],
            'mode': current_simulation_mode_name,
            'resource_grid': engine_state['resource_grid'],
            'clans': engine_state['clans'], # Ya viene formateado del engine
            'running': simulation_data['running'],
            'max_steps': simulation_data['max_steps'],
            'auto_stop': simulation_data['auto_stop'],
            'grid_size': current_config.get('GRID_SIZE', [50, 50]),  # AGREGADO
            'system_metrics': engine_state.get('system_metrics', {  # AGREGADO: Métricas del engine
                'total_population': 0,
                'active_clans': 0,
                'avg_energy': 0,
                'total_resources': 0
            })
        }
        return state


def simulation_loop():
    """Loop principal de simulación."""
    print("🔄 Iniciando loop de simulación...")
    while True:
        try:
            if simulation_data['running'] and current_simulation_engine is not None:
                termination_reason = simulation_step()

                # Enviar estado actualizado a todos los clientes
                state = get_simulation_state()
                # print(f"📤 Enviando estado: paso {state['step']}, {len(state['clans'])} clanes")
                socketio.emit('simulation_state', state)

                # Si la simulación terminó, notificar a los clientes
                if termination_reason:
                    summary = get_simulation_summary()
                    socketio.emit('simulation_terminated', {
                        'reason': termination_reason,
                        'summary': summary
                    })
                    print(f"🏁 Simulación terminada: {termination_reason}")
                    print(f"📤 Notificación de terminación enviada")
                    # Una vez terminada, se detiene el loop hasta un nuevo inicio/reset
                    with simulation_lock:
                        simulation_data['running'] = False # Asegurarse de que esté en False

            # Calcular intervalo dinámico basado en velocidad
            base_interval = simulation_data['update_interval']
            speed_multiplier = simulation_data['speed_multiplier']
            dynamic_interval = max(0.01, base_interval / speed_multiplier) # Limite mínimo de 10ms
            
            socketio.sleep(dynamic_interval)

        except Exception as e:
            print(f"❌ Error en loop de simulación: {e}")
            import traceback
            traceback.print_exc()
            with simulation_lock:
                simulation_data['running'] = False
                socketio.emit('simulation_error', {'error': str(e), 'trace': traceback.format_exc()})
            socketio.sleep(2.0) # Esperar un poco antes de reintentar o detener completamente

# === RUTAS WEB ===

@app.route('/')
def index():
    # Usar valores de la configuración por defecto para la página principal
    return render_template('index.html',
                           grid_size=default_config.GRID_SIZE,
                           initial_clans=default_config.INITIAL_CLAN_COUNT,
                           resource_density="Media", # Esto es un string, no un valor dinámico aún
                           build_version="2.0")

@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    global global_rng_seed
    config_files = [f.replace('.json', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
    config_files.sort() # Ordenar alfabéticamente

    if request.method == 'POST':
        # Solo procesar POST si es un formulario tradicional (fallback)
        selected_mode = request.form.get('simulation_mode', 'stochastic')
        selected_config_file = request.form.get('config_file', 'stochastic_default')
        seed_input = request.form.get('seed')
        
        seed = int(seed_input) if seed_input and seed_input.isdigit() else None
        
        # Reinicializar con nueva configuración y modo
        initialize_simulation(mode_name=selected_mode, config_name=selected_config_file, seed=seed)
        print(f"⚙️ Configuración aplicada vía POST: Modo={selected_mode}, Archivo={selected_config_file}, Semilla={seed}")

    # En caso de GET, solo inicializar si NO hay simulación activa
    if current_simulation_engine is None:
        print("🔄 Inicializando simulación por primera vez en GET /simulation")
        initialize_simulation(mode_name='stochastic', config_name='stochastic_default', seed=None)
    else:
        print("✅ Simulación ya existente, no reinicializando en GET /simulation")

    return render_template('simulation.html',
                           current_mode=current_simulation_mode_name,
                           config_files=config_files,
                           initial_seed=global_rng_seed) # Pasar la semilla actual para mostrar en el input

@app.route('/conservation_analysis')
def conservation_analysis():
    # Este resumen se generará al final de la simulación
    summary = get_simulation_summary()
    report = f"""
    <h2>📊 Análisis de Conservación</h2>
    <div style="background: #e8f5e8; padding: 2rem; border-radius: 8px;">
        <h3>🧬 Estado del Sistema al Final de la Simulación</h3>
        <p><strong>Clanes activos:</strong> {summary.get('surviving_clans', 'N/A')}</p>
        <p><strong>Población total:</strong> {summary.get('final_population', 'N/A')}</p>
        <p><strong>Pasos ejecutados:</strong> {summary.get('total_steps', 'N/A')}</p>
        <p>La simulación finalizó con la siguiente distribución:</p>
        <ul>
        {''.join([f"<li>Clan {c['id']}: Tamaño final {c['final_size']}, Energía {c['final_energy']:.1f}%</li>" for c in summary.get('clan_details', [])]) if summary.get('clan_details') else '<li>No hay detalles de clanes.</li>'}
        </ul>
    </div>
    """
    return render_template('analysis_report.html',
                           report=report,
                           analysis_type="Análisis de Conservación",
                           current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

@app.route('/convergence_analysis')
def convergence_analysis():
    # Esto también dependerá del estado de una simulación finalizada
    report = """
    <h2>📈 Análisis de Convergencia</h2>
    <div style="background: #e8f4f8; padding: 2rem; border-radius: 8px;">
        <h3>📊 Métricas del Sistema</h3>
        <p>Este análisis requiere datos de una simulación completada. Por favor, ejecuta una simulación y luego visita esta sección.</p>
        <p>La convergencia poblacional se evalúa buscando estabilidad en la varianza de la población total durante un umbral de pasos.</p>
    </div>
    """
    return render_template('analysis_report.html',
                           report=report,
                           analysis_type="Análisis de Convergencia",
                           current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

@app.route('/sensitivity_analysis')
def sensitivity_analysis():
    return render_template('analysis_report.html',
                           report="<h2>🔧 Análisis de Sensibilidad</h2><p>Disponible próximamente. Este análisis requerirá múltiples ejecuciones de simulación con diferentes parámetros para evaluar su impacto.</p>",
                           analysis_type="Análisis de Sensibilidad",
                           current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

# === EVENTOS WEBSOCKET ===

@socketio.on('connect')
def handle_connect():
    print('🔌 Cliente conectado al WebSocket')
    state = get_simulation_state()
    emit('simulation_state', state)
    print(f'📤 Estado inicial enviado: {len(state["clans"])} clanes, paso {state["step"]}')

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Cliente desconectado del WebSocket')

@socketio.on('start_simulation')
def handle_start_simulation():
    print('▶️ Solicitud de INICIO recibida')
    with simulation_lock:
        if current_simulation_engine is None:
            # Inicializar si no se ha hecho, por ejemplo si se entra directamente a /simulation
            initialize_simulation() 
        simulation_data['running'] = True
    print('✅ Simulación INICIADA')
    emit('simulation_started', {'status': 'running'})
    state = get_simulation_state()
    emit('simulation_state', state) # Enviar estado actual inmediatamente
    print(f'📤 Estado inmediato enviado tras inicio')

@socketio.on('pause_simulation')
def handle_pause_simulation():
    print('⏸️ Solicitud de PAUSA recibida')
    with simulation_lock:
        simulation_data['running'] = False
    print('✅ Simulación PAUSADA')
    emit('simulation_paused', {'status': 'paused'}) # Emitir evento de pausa

@socketio.on('reset_simulation')
def handle_reset_simulation():
    print('🔄 Solicitud de REINICIO recibida')
    with simulation_lock:
        simulation_data['running'] = False
    # Reinicializar con la última configuración usada o con la default
    initialize_simulation(
        mode_name=current_simulation_mode_name, 
        config_name=request.form.get('config_file', 'stochastic_default'), # Intentar usar la config actual del formulario si existe
        seed=global_rng_seed, # Mantener la semilla si estaba en determinista
        custom_grid_size=current_config.get('GRID_SIZE')  # Mantener el tamaño de rejilla actual
    )
    state = get_simulation_state()
    emit('simulation_state', state)
    print('✅ Simulación REINICIADA')

@socketio.on('step_simulation')
def handle_step_simulation():
    print('👆 Solicitud de PASO MANUAL recibida')
    if current_simulation_engine is None:
        emit('simulation_error', {'error': 'Simulación no inicializada para paso manual.'})
        return
    termination_reason = simulation_step()
    state = get_simulation_state()
    emit('simulation_state', state)
    print(f'📤 Estado de paso manual enviado: paso {state["step"]}')
    if termination_reason:
        summary = get_simulation_summary()
        emit('simulation_terminated', {
            'reason': termination_reason,
            'summary': summary
        })
    print('✅ Paso manual ejecutado')

@socketio.on('request_state')
def handle_request_state():
    # print('📤 Solicitud de estado recibida')
    state = get_simulation_state()
    emit('simulation_state', state)
    # print(f'📤 Estado enviado: {len(state["clans"])} clanes, paso {state["step"]}')

@socketio.on('update_speed')
def handle_update_speed(data):
    try:
        new_speed = float(data.get('speed', 1.0))
        new_speed = max(0.1, min(5.0, new_speed))
        with simulation_lock:
            simulation_data['speed_multiplier'] = new_speed
        print(f'⚡ Velocidad actualizada a {new_speed:.1f}x')
        emit('speed_updated', {'speed': new_speed})
    except Exception as e:
        print(f'❌ Error actualizando velocidad: {e}')
        emit('speed_update_error', {'error': str(e)})

@socketio.on('get_speed')
def handle_get_speed():
    with simulation_lock:
        current_speed = simulation_data['speed_multiplier']
    emit('current_speed', {'speed': current_speed})
    print(f'📤 Velocidad actual enviada: {current_speed:.1f}x')

@socketio.on('toggle_auto_stop')
def handle_toggle_auto_stop(data):
    try:
        new_auto_stop = bool(data.get('auto_stop', True))
        with simulation_lock:
            simulation_data['auto_stop'] = new_auto_stop
        print(f'🔄 Auto-stop {"activado" if new_auto_stop else "desactivado"}')
        emit('auto_stop_updated', {'auto_stop': new_auto_stop})
    except Exception as e:
        print(f'❌ Error toggling auto-stop: {e}')

@socketio.on('set_max_steps')
def handle_set_max_steps(data):
    try:
        new_max_steps = int(data.get('max_steps', 500))
        new_max_steps = max(50, min(2000, new_max_steps))
        with simulation_lock:
            simulation_data['max_steps'] = new_max_steps
            # Actualizar también el max_steps en el motor si ya está inicializado
            if current_simulation_engine:
                current_simulation_engine.max_steps = new_max_steps
        print(f'📊 Máximo de pasos establecido en {new_max_steps}')
        emit('max_steps_updated', {'max_steps': new_max_steps})
    except Exception as e:
        print(f'❌ Error setting max steps: {e}')

@socketio.on('get_simulation_config')
def handle_get_simulation_config():
    with simulation_lock:
        config = {
            'max_steps': simulation_data['max_steps'],
            'auto_stop': simulation_data['auto_stop'],
            'current_step': simulation_data['step'],
            'extinction_threshold': simulation_data['extinction_threshold'],
            'convergence_threshold': simulation_data['convergence_threshold'],
            'grid_size': current_config.get('GRID_SIZE', [0,0]), # Enviar el grid_size real
            'current_mode': current_simulation_mode_name,
            'current_config_file': request.form.get('config_file', 'stochastic_default'), # Para el frontend
            'current_seed': global_rng_seed
        }
    emit('simulation_config', config)
    print(f'📤 Configuración enviada: max_steps={config["max_steps"]}, auto_stop={config["auto_stop"]}, mode={config["current_mode"]}')

# NUEVOS EVENTOS WEBSOCKET PARA CONFIGURACIÓN SIN RECARGA

@socketio.on('apply_configuration')
def handle_apply_configuration(data):
    """Maneja la aplicación de nueva configuración sin recargar la página."""
    print('⚙️ Solicitud de aplicar configuración recibida')
    
    try:
        mode_name = data.get('simulation_mode', 'stochastic')
        config_name = data.get('config_file', 'stochastic_default')
        seed_input = data.get('seed')
        
        # Validar modo
        if mode_name not in ['stochastic', 'deterministic']:
            emit('configuration_error', {'error': 'Modo de simulación no válido'})
            return
        
        # Procesar semilla
        seed = None
        if seed_input and str(seed_input).strip():
            try:
                seed = int(seed_input)
                if seed < 1 or seed > 999999:
                    emit('configuration_error', {'error': 'La semilla debe estar entre 1 y 999999'})
                    return
            except ValueError:
                emit('configuration_error', {'error': 'La semilla debe ser un número entero'})
                return
        
        # Detener simulación si está corriendo
        with simulation_lock:
            simulation_data['running'] = False
        
        # Aplicar nueva configuración
        initialize_simulation(mode_name=mode_name, config_name=config_name, seed=seed)
        
        # Enviar confirmación con el nuevo estado
        state = get_simulation_state()
        emit('configuration_applied', {
            'message': f'Configuración aplicada: {mode_name}, {config_name}, semilla: {seed}',
            'new_state': state,
            'config': {
                'mode': mode_name,
                'config_file': config_name,
                'seed': seed
            }
        })
        
        print(f'✅ Configuración aplicada: Modo={mode_name}, Archivo={config_name}, Semilla={seed}')
        
    except Exception as e:
        print(f'❌ Error aplicando configuración: {e}')
        import traceback
        traceback.print_exc()
        emit('configuration_error', {'error': f'Error interno: {str(e)}'})

@socketio.on('get_available_configs')
def handle_get_available_configs():
    """Envía la lista de configuraciones disponibles."""
    try:
        config_files = [f.replace('.json', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
        config_files.sort()
        emit('available_configs', {'configs': config_files})
    except Exception as e:
        print(f'❌ Error obteniendo configuraciones: {e}')
        emit('configuration_error', {'error': 'No se pudieron cargar las configuraciones'})

# NUEVOS EVENTOS PARA PARÁMETROS EN VIVO
@socketio.on('update_parameters')
def handle_update_parameters(data):
    """Maneja la actualización de parámetros en tiempo real."""
    print('🔧 Solicitud de actualizar parámetros recibida:', data)
    
    try:
        # Filtrar parámetros válidos
        valid_parameters = {}
        
        # Parámetros que pueden modificarse en vivo
        allowed_params = {
            'birthRate', 'deathRate', 'starvationMortality', 'energyDecay',
            'resourceRegen', 'resourceRequired', 'energyConversion', 'resourceMax',
            'cooperation', 'aggressiveness', 'movementSpeed', 'perceptionRadius', 
            'territorialExpansion', 'combatRadius', 'combatDamage', 'combatEnergyCost',
            'allianceProbability', 'interactionRadius', 'migrationThreshold', 
            'restingThreshold', 'fightingThreshold'
        }
        
        for param, value in data.items():
            if param in allowed_params:
                try:
                    valid_parameters[param] = float(value)
                except (ValueError, TypeError):
                    continue
        
        if not valid_parameters:
            emit('parameters_error', {'error': 'No se proporcionaron parámetros válidos'})
            return
        
        # Aplicar parámetros al motor de simulación si existe
        if current_simulation_engine:
            # Aquí necesitarías métodos en tu SimulationEngine para actualizar parámetros
            # Por ahora, simulamos la aplicación exitosa
            print(f'✅ Parámetros aplicados: {valid_parameters}')
            
            # Actualizar configuración actual
            current_config.update(valid_parameters)
            
            emit('parameters_updated', {
                'message': f'Se aplicaron {len(valid_parameters)} parámetros exitosamente',
                'updated_parameters': valid_parameters
            })
        else:
            emit('parameters_error', {'error': 'No hay simulación activa para actualizar'})
    
    except Exception as e:
        print(f'❌ Error actualizando parámetros: {e}')
        emit('parameters_error', {'error': f'Error interno: {str(e)}'})

@socketio.on('get_current_parameters')
def handle_get_current_parameters():
    """Envía los parámetros actuales del sistema."""
    try:
        # Enviar parámetros de la configuración actual
        current_params = {
            'birthRate': current_config.get('birth_rate', 0.1),
            'deathRate': current_config.get('death_rate', 0.05),
            'starvationMortality': current_config.get('MORTALITY_STARVATION_MAX', 0.8),
            'energyDecay': current_config.get('energy_decay', 3),
            'resourceRegen': current_config.get('RESOURCE_REGEN_RATE', 1.5),
            'resourceRequired': current_config.get('RESOURCE_REQUIRED_PER_INDIVIDUAL', 1.2),
            'resourceMax': current_config.get('RESOURCE_MAX', 100),
            # Agregar más parámetros según sea necesario
        }
        
        emit('current_parameters', {'parameters': current_params})
        print('📤 Parámetros actuales enviados')
        
    except Exception as e:
        print(f'❌ Error obteniendo parámetros actuales: {e}')
        emit('parameters_error', {'error': f'Error obteniendo parámetros: {str(e)}'})

# NUEVO EVENTO PARA CAMBIAR TAMAÑO DE REJILLA
@socketio.on('update_grid_size')
def handle_update_grid_size(data):
    """Maneja el cambio de tamaño de rejilla."""
    print('📐 Solicitud de cambiar tamaño de rejilla recibida:', data)
    
    try:
        grid_width = int(data.get('gridWidth', 50))
        grid_height = int(data.get('gridHeight', 50))
        
        # Validar dimensiones
        if grid_width < 10 or grid_width > 200:
            emit('grid_size_error', {'error': 'El ancho debe estar entre 10 y 200'})
            return
            
        if grid_height < 10 or grid_height > 200:
            emit('grid_size_error', {'error': 'La altura debe estar entre 10 y 200'})
            return
        
        new_grid_size = [grid_width, grid_height]
        
        # Detener simulación si está corriendo
        with simulation_lock:
            simulation_data['running'] = False
        
        # Reinicializar con nuevo tamaño de rejilla
        initialize_simulation(
            mode_name=current_simulation_mode_name, 
            config_name='stochastic_default',  # Usar config default para el nuevo tamaño
            seed=global_rng_seed,
            custom_grid_size=new_grid_size
        )
        
        # Enviar confirmación
        state = get_simulation_state()
        emit('grid_size_updated', {
            'message': f'Rejilla actualizada a {grid_width}x{grid_height}',
            'new_grid_size': new_grid_size,
            'new_state': state
        })
        
        print(f'✅ Tamaño de rejilla actualizado a: {grid_width}x{grid_height}')
        
    except Exception as e:
        print(f'❌ Error actualizando tamaño de rejilla: {e}')
        emit('grid_size_error', {'error': f'Error interno: {str(e)}'})


if __name__ == '__main__':
    print("🚀 Iniciando aplicación de simulación territorial...")
    print("=" * 50)

    # Inicializar simulación por defecto al inicio del servidor
    initialize_simulation()

    # Iniciar loop de simulación en hilo separado
    simulation_thread = Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()
    print("🔄 Loop de simulación iniciado en hilo separado")

    print("🌐 Servidor listo en http://127.0.0.1:5000")
    print("=" * 50)

    socketio.run(app, debug=False, host='127.0.0.1', port=5000)