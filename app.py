# app.py - Versión final funcional completa
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import numpy as np
import json
import os
import time
from datetime import datetime
from threading import Thread, Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Variables globales con lock para thread safety
simulation_lock = Lock()
simulation_data = {
    'running': False,
    'clans': [],
    'resources': None,
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

# Configuración simple
GRID_SIZE = 50
NUM_CLANS = 3

def initialize_simulation():
    """Inicializa la simulación con datos básicos"""
    global simulation_data
    
    with simulation_lock:
        print("🚀 Inicializando simulación...")
        
        # Crear grid de recursos
        simulation_data['resources'] = np.random.uniform(30, 80, (GRID_SIZE, GRID_SIZE))
        
        # Crear clanes con posiciones aleatorias
        simulation_data['clans'] = []
        for i in range(NUM_CLANS):
            clan = {
                'id': i + 1,
                'size': np.random.randint(8, 15),
                'x': np.random.uniform(10, GRID_SIZE - 10),
                'y': np.random.uniform(10, GRID_SIZE - 10),
                'energy': 100.0,
                'state': 'foraging',
                'direction_x': np.random.uniform(-1, 1),
                'direction_y': np.random.uniform(-1, 1)
            }
            simulation_data['clans'].append(clan)
            print(f"✅ Clan {clan['id']}: tamaño={clan['size']}, pos=({clan['x']:.1f}, {clan['y']:.1f})")
        
        simulation_data['step'] = 0
        simulation_data['time'] = 0.0
        simulation_data['running'] = False
        simulation_data['speed_multiplier'] = 1.0
        simulation_data['update_interval'] = 1.0
        simulation_data['extinction_counter'] = 0
        simulation_data['last_populations'] = []
        
        print(f"✅ Simulación inicializada con {len(simulation_data['clans'])} clanes")

def simulation_step():
    """Ejecuta un paso de simulación"""
    global simulation_data
    
    with simulation_lock:
        if not simulation_data['running']:
            return None
            
        print(f"🔄 Ejecutando paso {simulation_data['step'] + 1}")
        
        # Regenerar recursos ligeramente
        simulation_data['resources'] *= 1.01
        simulation_data['resources'] = np.minimum(simulation_data['resources'], 100)
        
        # Actualizar cada clan
        for clan in simulation_data['clans']:
            if clan['size'] <= 0:
                continue
                
            # Movimiento simple (velocidad afectada por multiplicador)
            speed = 0.8 * simulation_data['speed_multiplier']
            clan['x'] += clan['direction_x'] * speed
            clan['y'] += clan['direction_y'] * speed
            
            # Mantener dentro del grid (toroidal)
            clan['x'] = clan['x'] % GRID_SIZE
            clan['y'] = clan['y'] % GRID_SIZE
            
            # Cambiar dirección aleatoriamente a veces
            if np.random.random() < 0.1:
                clan['direction_x'] = np.random.uniform(-1, 1)
                clan['direction_y'] = np.random.uniform(-1, 1)
            
            # Consumir recursos
            grid_x = int(clan['x']) % GRID_SIZE
            grid_y = int(clan['y']) % GRID_SIZE
            
            resource_consumed = min(simulation_data['resources'][grid_x, grid_y], clan['size'] * 0.2)
            simulation_data['resources'][grid_x, grid_y] -= resource_consumed
            
            # Actualizar energía
            if resource_consumed > clan['size'] * 0.1:
                clan['energy'] = min(100, clan['energy'] + 2)
                clan['state'] = 'foraging'
            else:
                clan['energy'] = max(0, clan['energy'] - 3)
                clan['state'] = 'migrating' if clan['energy'] > 30 else 'resting'
            
            # Crecimiento/decrecimiento poblacional simple
            if clan['energy'] > 70:
                clan['size'] += 0.05 * clan['size']
            elif clan['energy'] < 30:
                clan['size'] -= 0.02 * clan['size']
            
            clan['size'] = max(0, int(clan['size']))
        
        # Remover clanes extintos
        simulation_data['clans'] = [c for c in simulation_data['clans'] if c['size'] > 0]
        
        # Incrementar contadores (aplicar multiplicador de velocidad)
        simulation_data['step'] += 1
        simulation_data['time'] += 0.5 * simulation_data['speed_multiplier']
        
        active_clans = len(simulation_data['clans'])
        total_pop = sum(c['size'] for c in simulation_data['clans'])
        
        # Registrar población para análisis de convergencia
        simulation_data['last_populations'].append(total_pop)
        if len(simulation_data['last_populations']) > simulation_data['convergence_threshold']:
            simulation_data['last_populations'].pop(0)
        
        print(f"📊 Paso {simulation_data['step']}: {active_clans} clanes, {total_pop} población total")
        
        # Verificar condiciones de finalización
        should_stop, reason = check_termination_conditions()
        if should_stop:
            simulation_data['running'] = False
            print(f"🛑 Simulación terminada: {reason}")
            return reason
        
        return None

def check_termination_conditions():
    """Verifica si la simulación debe terminar"""
    if not simulation_data['auto_stop']:
        # Solo verificar límite máximo de pasos si auto_stop está desactivado
        if simulation_data['step'] >= simulation_data['max_steps']:
            return True, f"Límite máximo de pasos alcanzado ({simulation_data['max_steps']})"
        return False, ""
    
    total_pop = sum(c['size'] for c in simulation_data['clans'])
    active_clans = len(simulation_data['clans'])
    
    # 1. Extinción total
    if total_pop == 0:
        simulation_data['extinction_counter'] += 1
        if simulation_data['extinction_counter'] >= simulation_data['extinction_threshold']:
            return True, "Extinción total: No quedan individuos en ningún clan"
    else:
        simulation_data['extinction_counter'] = 0
    
    # 2. Un solo clan sobreviviente (dominancia total)
    if active_clans == 1 and simulation_data['step'] > 50:
        return True, f"Dominancia total: Solo queda el Clan {simulation_data['clans'][0]['id']}"
    
    # 3. Límite máximo de pasos
    if simulation_data['step'] >= simulation_data['max_steps']:
        return True, f"Límite máximo de pasos alcanzado ({simulation_data['max_steps']})"
    
    # 4. Convergencia poblacional (población estable por mucho tiempo)
    if len(simulation_data['last_populations']) >= simulation_data['convergence_threshold']:
        recent_pops = simulation_data['last_populations'][-20:]  # Últimos 20 pasos
        if len(recent_pops) >= 20:
            variance = np.var(recent_pops)
            mean_pop = np.mean(recent_pops)
            
            # Si la varianza es muy baja relative a la media, hay convergencia
            if variance < (mean_pop * 0.02) and mean_pop > 0:  # Menos del 2% de variación
                return True, f"Convergencia alcanzada: Población estable en {mean_pop:.0f} individuos"
    
    # 5. Población muy baja (cerca de extinción)
    if total_pop <= 5 and simulation_data['step'] > 100:
        return True, f"Población crítica: Solo quedan {total_pop} individuos"
    
    # 6. Sistema degenerado (todos los clanes muy pequeños)
    if active_clans > 1 and simulation_data['step'] > 200:
        max_clan_size = max(c['size'] for c in simulation_data['clans'])
        if max_clan_size <= 3:
            return True, "Sistema degenerado: Todos los clanes tienen poblaciones muy pequeñas"
    
    return False, ""

def get_simulation_summary():
    """Genera un resumen de la simulación terminada"""
    total_pop = sum(c['size'] for c in simulation_data['clans'])
    active_clans = len(simulation_data['clans'])
    
    summary = {
        'total_steps': simulation_data['step'],
        'simulation_time': simulation_data['time'],
        'final_population': total_pop,
        'surviving_clans': active_clans,
        'clan_details': []
    }
    
    for clan in simulation_data['clans']:
        summary['clan_details'].append({
            'id': clan['id'],
            'final_size': clan['size'],
            'final_energy': clan['energy'],
            'final_state': clan['state']
        })
    
    return summary

def get_simulation_state():
    """Obtiene el estado actual para enviar al frontend"""
    with simulation_lock:
        # Convertir a formato compatible con el frontend
        state = {
            'time': simulation_data['time'],
            'step': simulation_data['step'],
            'mode': 'stochastic',
            'resource_grid': simulation_data['resources'].tolist(),
            'clans': [],
            'running': simulation_data['running'],
            'max_steps': simulation_data['max_steps'],
            'auto_stop': simulation_data['auto_stop']
        }
        
        for clan in simulation_data['clans']:
            clan_data = {
                'id': clan['id'],
                'size': clan['size'],
                'position': [clan['x'], clan['y']],
                'energy': clan['energy'],
                'state': clan['state'],
                'strategy': 'cooperative',
                'visual_size': max(3, min(12, np.sqrt(clan['size']) * 1.5))
            }
            state['clans'].append(clan_data)
        
        return state

def simulation_loop():
    """Loop principal de simulación"""
    print("🔄 Iniciando loop de simulación...")
    
    while True:
        try:
            if simulation_data['running']:
                termination_reason = simulation_step()
                
                # Enviar estado actualizado a todos los clientes
                state = get_simulation_state()
                print(f"📤 Enviando estado: paso {state['step']}, {len(state['clans'])} clanes")
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
                
            # Calcular intervalo dinámico basado en velocidad
            base_interval = simulation_data['update_interval']
            speed_multiplier = simulation_data['speed_multiplier']
            
            # Velocidad más alta = intervalo más corto
            dynamic_interval = max(0.1, base_interval / speed_multiplier)
            
            socketio.sleep(dynamic_interval)
            
        except Exception as e:
            print(f"❌ Error en loop de simulación: {e}")
            import traceback
            traceback.print_exc()
            with simulation_lock:
                simulation_data['running'] = False
            socketio.sleep(2.0)

# === RUTAS WEB ===

@app.route('/')
def index():
    return render_template('index.html', 
                         grid_size=(GRID_SIZE, GRID_SIZE),
                         initial_clans=NUM_CLANS,
                         resource_density="Media",
                         build_version="2.0")

@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    if request.method == 'POST':
        # Reinicializar con nueva configuración si es necesario
        initialize_simulation()
    
    config_files = ['stochastic_default', 'deterministic_default', 'small_test', 'large_scale']
    return render_template('simulation.html', 
                         current_mode='stochastic', 
                         config_files=config_files)

@app.route('/conservation_analysis')
def conservation_analysis():
    report = f"""
    <h2>📊 Análisis de Conservación</h2>
    <div style="background: #e8f5e8; padding: 2rem; border-radius: 8px;">
        <h3>🧬 Estado del Sistema</h3>
        <p><strong>Clanes activos:</strong> {len(simulation_data['clans'])}</p>
        <p><strong>Población total:</strong> {sum(c['size'] for c in simulation_data['clans'])}</p>
        <p><strong>Pasos ejecutados:</strong> {simulation_data['step']}</p>
        <p>La simulación está funcionando correctamente.</p>
    </div>
    """
    
    return render_template('analysis_report.html', 
                         report=report, 
                         analysis_type="Análisis de Conservación",
                         current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

@app.route('/convergence_analysis')
def convergence_analysis():
    report = """
    <h2>📈 Análisis de Convergencia</h2>
    <div style="background: #e8f4f8; padding: 2rem; border-radius: 8px;">
        <h3>📊 Métricas del Sistema</h3>
        <p>Análisis de convergencia disponible después de ejecutar la simulación.</p>
        <p>Execute varios pasos para obtener datos significativos.</p>
    </div>
    """
    
    return render_template('analysis_report.html', 
                         report=report, 
                         analysis_type="Análisis de Convergencia",
                         current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

@app.route('/sensitivity_analysis')
def sensitivity_analysis():
    return render_template('analysis_report.html', 
                         report="<h2>🔧 Análisis de Sensibilidad</h2><p>Disponible próximamente.</p>", 
                         analysis_type="Análisis de Sensibilidad",
                         current_time=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

# === EVENTOS WEBSOCKET ===

@socketio.on('connect')
def handle_connect():
    print('🔌 Cliente conectado al WebSocket')
    
    # Enviar estado inicial
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
        simulation_data['running'] = True
    
    print('✅ Simulación INICIADA')
    
    # Enviar confirmación inmediata
    emit('simulation_started', {'status': 'running'})
    
    # Enviar estado actual inmediatamente
    state = get_simulation_state()
    emit('simulation_state', state)
    print(f'📤 Estado inmediato enviado tras inicio')

@socketio.on('pause_simulation')
def handle_pause_simulation():
    print('⏸️ Solicitud de PAUSA recibida')
    
    with simulation_lock:
        simulation_data['running'] = False
    
    print('✅ Simulación PAUSADA')

@socketio.on('reset_simulation')
def handle_reset_simulation():
    print('🔄 Solicitud de REINICIO recibida')
    
    with simulation_lock:
        simulation_data['running'] = False
    
    # Reinicializar
    initialize_simulation()
    
    # Enviar nuevo estado
    state = get_simulation_state()
    emit('simulation_state', state)
    
    print('✅ Simulación REINICIADA')

@socketio.on('step_simulation')
def handle_step_simulation():
    print('👆 Solicitud de PASO MANUAL recibida')
    
    # Ejecutar un solo paso
    termination_reason = simulation_step()
    
    # Enviar estado actualizado
    state = get_simulation_state()
    emit('simulation_state', state)
    print(f'📤 Estado de paso manual enviado: paso {state["step"]}')
    
    # Si terminó, notificar
    if termination_reason:
        summary = get_simulation_summary()
        emit('simulation_terminated', {
            'reason': termination_reason,
            'summary': summary
        })
    
    print('✅ Paso manual ejecutado')

@socketio.on('request_state')
def handle_request_state():
    print('📤 Solicitud de estado recibida')
    
    state = get_simulation_state()
    emit('simulation_state', state)
    
    print(f'📤 Estado enviado: {len(state["clans"])} clanes, paso {state["step"]}')

@socketio.on('update_speed')
def handle_update_speed(data):
    """Maneja cambios de velocidad desde el frontend"""
    try:
        new_speed = float(data.get('speed', 1.0))
        # Limitar velocidad entre 0.1x y 5.0x
        new_speed = max(0.1, min(5.0, new_speed))
        
        with simulation_lock:
            simulation_data['speed_multiplier'] = new_speed
            
        print(f'⚡ Velocidad actualizada a {new_speed:.1f}x')
        
        # Enviar confirmación
        emit('speed_updated', {'speed': new_speed})
        
    except Exception as e:
        print(f'❌ Error actualizando velocidad: {e}')
        emit('speed_update_error', {'error': str(e)})

@socketio.on('get_speed')
def handle_get_speed():
    """Envía la velocidad actual al cliente"""
    with simulation_lock:
        current_speed = simulation_data['speed_multiplier']
    
    emit('current_speed', {'speed': current_speed})
    print(f'📤 Velocidad actual enviada: {current_speed:.1f}x')

@socketio.on('toggle_auto_stop')
def handle_toggle_auto_stop(data):
    """Alterna el auto-stop de la simulación"""
    try:
        new_auto_stop = bool(data.get('auto_stop', True))
        
        with simulation_lock:
            simulation_data['auto_stop'] = new_auto_stop
            
        print(f'🔄 Auto-stop {"activado" if new_auto_stop else "desactivado"}')
        
        # Enviar confirmación
        emit('auto_stop_updated', {'auto_stop': new_auto_stop})
        
    except Exception as e:
        print(f'❌ Error toggling auto-stop: {e}')

@socketio.on('set_max_steps')
def handle_set_max_steps(data):
    """Establece el máximo número de pasos"""
    try:
        new_max_steps = int(data.get('max_steps', 500))
        new_max_steps = max(50, min(2000, new_max_steps))  # Límites razonables
        
        with simulation_lock:
            simulation_data['max_steps'] = new_max_steps
            
        print(f'📊 Máximo de pasos establecido en {new_max_steps}')
        
        # Enviar confirmación
        emit('max_steps_updated', {'max_steps': new_max_steps})
        
    except Exception as e:
        print(f'❌ Error setting max steps: {e}')

@socketio.on('get_simulation_config')
def handle_get_simulation_config():
    """Envía la configuración actual de la simulación"""
    with simulation_lock:
        config = {
            'max_steps': simulation_data['max_steps'],
            'auto_stop': simulation_data['auto_stop'],
            'current_step': simulation_data['step'],
            'extinction_threshold': simulation_data['extinction_threshold'],
            'convergence_threshold': simulation_data['convergence_threshold']
        }
    
    emit('simulation_config', config)
    print(f'📤 Configuración enviada: max_steps={config["max_steps"]}, auto_stop={config["auto_stop"]}')

if __name__ == '__main__':
    print("🚀 Iniciando aplicación de simulación territorial...")
    print("=" * 50)
    
    # Inicializar simulación
    initialize_simulation()
    
    # Iniciar loop de simulación en hilo separado
    simulation_thread = Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()
    print("🔄 Loop de simulación iniciado en hilo separado")
    
    print("🌐 Servidor listo en http://localhost:5000")
    print("=" * 50)
    
    # Ejecutar servidor
    socketio.run(app, debug=False, host='127.0.0.1', port=5000)