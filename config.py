# clan_territorial_simulation/config.py - Valores por defecto

GRID_SIZE = (10, 10)
INITIAL_CLAN_COUNT = 5
MIN_CLAN_SIZE = 5
MAX_CLAN_SIZE = 20
RESOURCE_MAX = 100.0
RESOURCE_REGENERATION_RATE = 1.5 # Coincidir con Environment default
RESOURCE_REQUIRED_PER_INDIVIDUAL = 0.1 # Coincidir con Clan default
MORTALITY_STARVATION_MAX = 0.5 # Coincidir con equations default

# Parámetros de Validación (mantener como constantes si se usan en scripts de análisis)
CONVERGENCE_DTS = [0.1, 0.05, 0.025]
CONVERGENCE_STEPS = 100
MONTE_CARLO_RUNS = 10
MONTE_CARLO_STEPS = 50