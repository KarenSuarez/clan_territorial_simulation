# data/configs/config_default.py
# Configuración por defecto para la simulación de competencia territorial

# === CONFIGURACIÓN DEL ENTORNO ===
GRID_SIZE = (10, 10)  # Tamaño de la rejilla (filas, columnas)
RESOURCE_MAX = 10.0  # Cantidad máxima de recursos por celda
RESOURCE_REGEN_RATE = 1.5  # Tasa de regeneración de recursos por unidad de tiempo

# === CONFIGURACIÓN DE CLANES ===
INITIAL_CLAN_COUNT = 5  # Número inicial de clanes
MIN_CLAN_SIZE = 10  # Tamaño mínimo inicial de clan
MAX_CLAN_SIZE = 20  # Tamaño máximo inicial de clan

# === PARÁMETROS DEMOGRÁFICOS ===
BIRTH_RATE = 0.1  # Tasa de natalidad base por unidad de tiempo
NATURAL_DEATH_RATE = 0.05  # Tasa de mortalidad natural por unidad de tiempo
MORTALITY_STARVATION_MAX = 0.8  # Mortalidad máxima por inanición

# === RECURSOS Y SUPERVIVENCIA ===
RESOURCE_REQUIRED_PER_INDIVIDUAL = 1.2  # Recursos necesarios por individuo por unidad de tiempo
ENERGY_CONVERSION_EFFICIENCY = 15.0  # Factor de conversión de recursos a energía
ENERGY_DECAY_RATE = 3.0  # Degradación de energía por unidad de tiempo

# === PARÁMETROS DE MOVIMIENTO ===
MOVEMENT_SPEED_BASE = 1.0  # Velocidad base de movimiento
PERCEPTION_RADIUS = 5  # Radio de percepción para recursos y otros clanes
MIGRATION_SPEED_MULTIPLIER = 1.5  # Multiplicador de velocidad durante migración

# === PARÁMETROS SOCIALES ===
COOPERATION_TENDENCY_DEFAULT = 0.6  # Tendencia cooperativa por defecto
AGGRESSIVENESS_DEFAULT = 0.3  # Agresividad por defecto
TERRITORIAL_EXPANSION_RATE = 0.05  # Tasa de expansión territorial

# === PARÁMETROS DE COMBATE ===
COMBAT_RADIUS = 5.0  # Radio para iniciar combate
COMBAT_DAMAGE_FACTOR = 5.0  # Factor de daño en combate
COMBAT_ENERGY_COST = 20.0  # Costo energético del combate por unidad de tiempo

# === CONFIGURACIÓN DE SIMULACIÓN ===
DEFAULT_DT = 0.2  # Paso de tiempo por defecto
DEFAULT_MAX_STEPS = 500  # Número máximo de pasos por defecto
DEFAULT_SPEED_MULTIPLIER = 1.0  # Multiplicador de velocidad por defecto

# === CONFIGURACIÓN DE INTERACCIONES ===
INTERACTION_RADIUS = 5.0  # Radio para interacciones entre clanes
ALLIANCE_PROBABILITY = 0.2  # Probabilidad de formar alianzas entre clanes cooperativos
RESOURCE_COMPETITION_RADIUS = 1.5  # Radio para competencia de recursos

# === CONFIGURACIÓN DE TERRITORIO ===
MAX_TERRITORY_SIZE_MULTIPLIER = 5  # Máximo de celdas por individuo en territorio
TERRITORY_CENTER_ATTRACTION = 0.5  # Factor de atracción hacia el centro territorial

# === CONDICIONES DE FINALIZACIÓN ===
EXTINCTION_THRESHOLD = 5  # Número de pasos consecutivos sin población para extinción
CONVERGENCE_THRESHOLD = 50  # Número de pasos para evaluar convergencia
POPULATION_VARIANCE_THRESHOLD = 0.02  # Umbral de varianza para convergencia (2%)
CRITICAL_POPULATION_THRESHOLD = 5  # Población crítica para finalización
MIN_CLAN_SIZE_DEGENERATION = 3  # Tamaño mínimo antes de considerarse degenerado

# === CONFIGURACIÓN DE ESTADOS ===
ENERGY_THRESHOLD_RESTING = 25  # Umbral de energía para entrar en estado de descanso
ENERGY_THRESHOLD_FIGHTING = 30  # Umbral mínimo de energía para combatir
ENERGY_THRESHOLD_REPRODUCTION = 30  # Umbral mínimo para reproducción
RESOURCE_THRESHOLD_MIGRATION = 10  # Multiplicador de recursos para triggear migración

# === CONFIGURACIÓN DE MODO ESTOCÁSTICO ===
STOCHASTIC_MOVEMENT_NOISE_STD = 0.1  # Desviación estándar del ruido de movimiento
STOCHASTIC_FORAGE_PROBABILITY = 0.8  # Probabilidad de forrajear vs explorar
STOCHASTIC_DECISION_NOISE_FACTOR = 0.15  # Factor de ruido en decisiones
STOCHASTIC_INTERACTION_RANDOMNESS = 0.2  # Aleatoriedad en interacciones

# === CONFIGURACIÓN DE MODO DETERMINISTA ===
DETERMINISTIC_MOVEMENT_NOISE_STD = 0.0  # Sin ruido en movimiento
DETERMINISTIC_FORAGE_PROBABILITY = 1.0  # Siempre forrajear cuando es óptimo
DETERMINISTIC_USE_CACHING = True  # Usar cache para optimizaciones
DETERMINISTIC_CACHE_LIMIT = 1000  # Límite de entradas en cache

# === CONFIGURACIÓN DE RECUPERACIÓN ===
ENERGY_RECOVERY_RATE_RESTING = 25.0  # Recuperación de energía durante descanso
MORALE_RECOVERY_RATE_RESTING = 10.0  # Recuperación de moral durante descanso
MORALE_RECOVERY_RATE_DEFENDING = 1.0  # Recuperación de moral al defender

# === CONFIGURACIÓN DE VISUALIZACIÓN ===
VISUAL_SIZE_MIN = 3  # Tamaño visual mínimo de clanes
VISUAL_SIZE_MAX = 12  # Tamaño visual máximo de clanes
VISUAL_SIZE_MULTIPLIER = 1.5  # Multiplicador para calcular tamaño visual

# === CONFIGURACIÓN DE RENDIMIENTO ===
MAX_POPULATION_HISTORY = 1000  # Máximo de entradas en historial de población
MAX_RESOURCE_HISTORY = 1000  # Máximo de entradas en historial de recursos
SIMULATION_UPDATE_INTERVAL = 1.0  # Intervalo base de actualización WebSocket

# === CONFIGURACIÓN DE ANÁLISIS ===
ANALYSIS_WINDOW_SIZE = 50  # Tamaño de ventana para análisis móviles
HOTSPOT_THRESHOLD_PERCENTILE = 90  # Percentil para detectar hotspots de recursos
SPATIAL_ANALYSIS_RADIUS = 3  # Radio para análisis espacial local

# === CONFIGURACIÓN DE EXPORTACIÓN ===
EXPORT_PRECISION_FLOAT = 2  # Precisión decimal para valores flotantes en exportación
EXPORT_MAX_HISTORY_ENTRIES = 5000  # Máximo de entradas de historial para exportar

# === CONFIGURACIÓN DE DESARROLLO Y DEBUG ===
DEBUG_MODE = False  # Activar modo debug
DEBUG_LOG_INTERVAL = 50  # Intervalo de logging para debug (cada N pasos)
DEBUG_CLAN_TRACKING = True  # Seguir clanes específicos para debug
DEBUG_PERFORMANCE_MONITORING = True  # Monitorear rendimiento

# === VALIDACIÓN DE CONFIGURACIÓN ===
def validate_config():
    """Valida que la configuración sea consistente."""
    errors = []
    
    # Validar tamaños del grid
    if GRID_SIZE[0] <= 0 or GRID_SIZE[1] <= 0:
        errors.append("GRID_SIZE debe tener valores positivos")
    
    # Validar recursos
    if RESOURCE_MAX <= 0:
        errors.append("RESOURCE_MAX debe ser positivo")
    
    if RESOURCE_REGEN_RATE < 0:
        errors.append("RESOURCE_REGEN_RATE no puede ser negativo")
    
    # Validar clanes
    if INITIAL_CLAN_COUNT <= 0:
        errors.append("INITIAL_CLAN_COUNT debe ser positivo")
    
    if MIN_CLAN_SIZE <= 0 or MAX_CLAN_SIZE <= 0:
        errors.append("MIN_CLAN_SIZE y MAX_CLAN_SIZE deben ser positivos")
    
    if MIN_CLAN_SIZE > MAX_CLAN_SIZE:
        errors.append("MIN_CLAN_SIZE no puede ser mayor que MAX_CLAN_SIZE")
    
    # Validar tasas demográficas
    if BIRTH_RATE < 0 or NATURAL_DEATH_RATE < 0:
        errors.append("Las tasas demográficas no pueden ser negativas")
    
    # Validar configuración de simulación
    if DEFAULT_DT <= 0:
        errors.append("DEFAULT_DT debe ser positivo")
    
    if DEFAULT_MAX_STEPS <= 0:
        errors.append("DEFAULT_MAX_STEPS debe ser positivo")
    
    # Validar umbrales
    if ENERGY_THRESHOLD_RESTING < 0 or ENERGY_THRESHOLD_RESTING > 100:
        errors.append("ENERGY_THRESHOLD_RESTING debe estar entre 0 y 100")
    
    if COOPERATION_TENDENCY_DEFAULT < 0 or COOPERATION_TENDENCY_DEFAULT > 1:
        errors.append("COOPERATION_TENDENCY_DEFAULT debe estar entre 0 y 1")
    
    if AGGRESSIVENESS_DEFAULT < 0 or AGGRESSIVENESS_DEFAULT > 1:
        errors.append("AGGRESSIVENESS_DEFAULT debe estar entre 0 y 1")
    
    return errors

def get_config_summary():
    """Retorna un resumen de la configuración actual."""
    return {
        'environment': {
            'grid_size': GRID_SIZE,
            'resource_max': RESOURCE_MAX,
            'regen_rate': RESOURCE_REGEN_RATE
        },
        'clans': {
            'initial_count': INITIAL_CLAN_COUNT,
            'size_range': (MIN_CLAN_SIZE, MAX_CLAN_SIZE),
            'cooperation': COOPERATION_TENDENCY_DEFAULT,
            'aggressiveness': AGGRESSIVENESS_DEFAULT
        },
        'simulation': {
            'dt': DEFAULT_DT,
            'max_steps': DEFAULT_MAX_STEPS,
            'speed_multiplier': DEFAULT_SPEED_MULTIPLIER
        },
        'survival': {
            'resource_per_individual': RESOURCE_REQUIRED_PER_INDIVIDUAL,
            'birth_rate': BIRTH_RATE,
            'death_rate': NATURAL_DEATH_RATE
        }
    }

def export_config_to_json():
    """Exporta la configuración actual a formato JSON."""
    import json
    
    config_dict = {}
    
    # Obtener todas las variables del módulo que sean configuraciones
    current_module = globals()
    for name, value in current_module.items():
        if name.isupper() and not name.startswith('__'):
            config_dict[name] = value
    
    return json.dumps(config_dict, indent=2)

# Ejecutar validación al importar
if __name__ == '__main__':
    print("Validando configuración por defecto...")
    errors = validate_config()
    
    if errors:
        print("❌ Errores encontrados en la configuración:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuración válida")
        
        print("\n📊 Resumen de configuración:")
        summary = get_config_summary()
        for category, params in summary.items():
            print(f"\n{category.upper()}:")
            for param, value in params.items():
                print(f"  {param}: {value}")
else:
    # Validar automáticamente al importar en otros módulos
    validation_errors = validate_config()
    if validation_errors:
        import warnings
        warnings.warn(f"Configuración por defecto tiene errores: {validation_errors}")

# === CONFIGURACIÓN ESPECÍFICA PARA DIFERENTES ESCENARIOS ===

# Configuración para simulaciones rápidas (testing)
QUICK_TEST_CONFIG = {
    'GRID_SIZE': (20, 20),
    'INITIAL_CLAN_COUNT': 3,
    'DEFAULT_MAX_STEPS': 100,
    'MIN_CLAN_SIZE': 5,
    'MAX_CLAN_SIZE': 15
}

# Configuración para simulaciones de gran escala
LARGE_SCALE_CONFIG = {
    'GRID_SIZE': (200, 200),
    'INITIAL_CLAN_COUNT': 20,
    'DEFAULT_MAX_STEPS': 1000,
    'MIN_CLAN_SIZE': 50,
    'MAX_CLAN_SIZE': 200
}

# Configuración para análisis de convergencia
CONVERGENCE_ANALYSIS_CONFIG = {
    'DEFAULT_MAX_STEPS': 2000,
    'CONVERGENCE_THRESHOLD': 100,
    'POPULATION_VARIANCE_THRESHOLD': 0.01,
    'EXTINCTION_THRESHOLD': 20
}

def apply_scenario_config(scenario_name):
    """Aplica una configuración de escenario específica."""
    global GRID_SIZE, INITIAL_CLAN_COUNT, DEFAULT_MAX_STEPS, MIN_CLAN_SIZE, MAX_CLAN_SIZE
    global CONVERGENCE_THRESHOLD, POPULATION_VARIANCE_THRESHOLD, EXTINCTION_THRESHOLD
    
    if scenario_name == 'quick_test':
        config = QUICK_TEST_CONFIG
    elif scenario_name == 'large_scale':
        config = LARGE_SCALE_CONFIG
    elif scenario_name == 'convergence_analysis':
        config = CONVERGENCE_ANALYSIS_CONFIG
    else:
        raise ValueError(f"Escenario no reconocido: {scenario_name}")
    
    # Aplicar configuración
    for key, value in config.items():
        globals()[key] = value
    
    print(f"✅ Configuración '{scenario_name}' aplicada")